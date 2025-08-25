import os
import re
import requests
import datetime
from datetime import timedelta
from typing import Dict, Any, List, Tuple

class Config:
    def __init__(self):
        self.REPO_PATH = "Rewrite"
        self.REWRITE_DIR = "Tool"
        self.OUTPUT_FILE = "Tool.config"
        self.README_PATH = "README_Rewrite.md"
        self.TIMEOUT = 30
        # 规则源
        self.REWRITE_SOURCES = {
            "谷歌重定向": "https://raw.githubusercontent.com/6666-H/Qx-Resource/refs/heads/main/Manual/Rewrite/GoogleToSearch.config",
             "ReLens": "https://raw.githubusercontent.com/6666-H/Qx-Resource/refs/heads/main/Manual/Rewrite/ReLens.config",
            "京东比价": "https://raw.githubusercontent.com/githubdulong/Script/master/Surge/jd_price.sgmodule",
            "懒人听书": "https://raw.githubusercontent.com/WeiGiegie/666/main/lrts.js"
        }

class RuleProcessor:
    HOST_RE = re.compile(r'(?i)^\s*hostname\s*=\s*(.+)$')
    SECTION_RE = re.compile(r'^\s*\[(.+?)\]\s*$')
    COMMENT_RE = re.compile(r'^\s*(#|//)')

    # ✅ 只保留这些 section
    ALLOWED_SECTIONS = {"[rewrite_local]", "[script]", "[rewrite]", "[header_rewrite]"}

    def __init__(self, config: Config):
        self.config = config

    # -------- 下载 --------
    def download_rule(self, name: str, url: str) -> Tuple[str, str | None]:
        try:
            r = requests.get(url, timeout=self.config.TIMEOUT)
            r.raise_for_status()
            return name, r.text
        except Exception as e:
            print(f"Error downloading {name}: {e}")
            return name, None

    # -------- 解析 hostname 列表 --------
    def _parse_hostnames(self, raw_value: str) -> List[str]:
        no_comment = re.split(r'\s#|//', raw_value, maxsplit=1)[0].strip()
        no_placeholder = re.sub(r'%[A-Za-z_]+%', '', no_comment).strip()
        parts = [p.strip().strip(',') for p in no_placeholder.split(',')]
        hosts = [p.lower() for p in parts if p]
        return hosts

    # -------- 处理单个源文本 --------
    def process_rules(self, content: str) -> Dict[str, Any]:
        out = {
            'sections': {},
            'host': set(),
            'mitm_other': []
        }
        if not content:
            return out

        lines = content.splitlines()
        current_section = '[rewrite]'
        out['sections'][current_section] = []

        seen_mitm_other = set()
        in_js_block = False

        for raw in lines:
            line = raw.rstrip()
            if not line.strip() or self.COMMENT_RE.match(line):
                continue

            # section
            m_sec = self.SECTION_RE.match(line)
            if m_sec:
                sec_name = f"[{m_sec.group(1).strip().lower()}]"
                current_section = sec_name
                if current_section not in out['sections']:
                    out['sections'][current_section] = []
                continue

            # hostname
            m_host = self.HOST_RE.match(line)
            if m_host:
                hosts = self._parse_hostnames(m_host.group(1))
                out['host'].update(hosts)
                continue

            # MITM 其它项
            if current_section == '[mitm]':
                key = line.lower()
                if key not in seen_mitm_other:
                    out['mitm_other'].append(line)
                    seen_mitm_other.add(key)
                continue

            # 🚫 跳过非白名单 section
            if current_section not in self.ALLOWED_SECTIONS:
                continue

            # 🚫 跳过 JS 赋值块
            if re.match(r'^\s*var\s+\w+\s*=\s*JSON\.parse\(\$response\.body\);', line):
                continue
            if re.match(r'^\s*\w+\s*=\s*{', line):
                in_js_block = True
                continue
            if in_js_block:
                if line.strip().endswith("};"):
                    in_js_block = False
                continue

            # ✅ 保留规则行
            out['sections'][current_section].append(line)

        return out

    # -------- 合并多个源 --------
    def merge_rules(self) -> Dict[str, Any]:
        merged = {
            'sections': {},
            'host': set(),
            'mitm_other': []
        }
        seen_mitm_other = set()

        for name, url in self.config.REWRITE_SOURCES.items():
            print(f"Downloading {name}...")
            _, content = self.download_rule(name, url)
            if not content:
                continue

            rules = self.process_rules(content)

            for sec, lines in rules['sections'].items():
                if sec not in merged['sections']:
                    merged['sections'][sec] = []
                if lines:
                    merged['sections'][sec].append(f"# {name}")
                    merged['sections'][sec].extend(lines)

            merged['host'].update(rules['host'])

            for line in rules['mitm_other']:
                key = line.lower()
                if key not in seen_mitm_other:
                    merged['mitm_other'].append(line)
                    seen_mitm_other.add(key)

        return merged

    # -------- 生成输出 --------
    def generate_output(self, merged: Dict[str, Any]) -> str:
        beijing_time = datetime.datetime.utcnow() + timedelta(hours=8)
        header = [
            "#!name = 自建重写解锁合集",
            "#!desc = 自建重写解锁合集",
            f"# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)",
            "# 合并自以下源：",
            *[f"# {name}: {url}" for name, url in self.config.REWRITE_SOURCES.items()],
            ""
        ]
        body: List[str] = []

        for sec, lines in merged['sections'].items():
            if sec == '[mitm]':
                continue
            if not lines:
                continue
            body.append(sec.upper())
            body.extend(lines)
            body.append("")

        mitm_block: List[str] = []
        if merged['mitm_other']:
            mitm_block.extend(merged['mitm_other'])
        if merged['host']:
            host_line = "hostname = " + ", ".join(sorted(merged['host']))
            mitm_block.append(host_line)

        if mitm_block:
            body.append("[MITM]")
            body.extend(mitm_block)
            body.append("")

        return "\n".join(header + body)

    # -------- 更新 README --------
    def update_readme(self, merged: Dict[str, Any]) -> None:
        beijing_time = datetime.datetime.utcnow() + timedelta(hours=8)
        section_counts: Dict[str, int] = {}
        for sec, lines in merged['sections'].items():
            cnt = sum(1 for x in lines if not x.strip().startswith('#'))
            section_counts[sec] = cnt

        readme = f"""# 自建重写解锁合集

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 规则说明
本重写规则集合并自各个开源规则，自动归并 hostname 到 [MITM]，并保留 [MITM] 下其它配置项。

## 规则统计
- MITM 主机数量：{len(merged['host'])}
{"".join([f"- {sec.upper()} 规则数量：{count}\n" for sec, count in section_counts.items()])}
- MITM 其它配置项数量：{len(merged['mitm_other'])}

## 规则来源
{chr(10).join([f"- {name}: {url}" for name, url in self.config.REWRITE_SOURCES.items()])}
"""
        os.makedirs(self.config.REPO_PATH, exist_ok=True)
        with open(os.path.join(self.config.REPO_PATH, self.config.README_PATH), "w", encoding="utf-8") as f:
            f.write(readme)

def main():
    config = Config()
    p = RuleProcessor(config)

    try:
        os.makedirs(os.path.join(config.REPO_PATH, config.REWRITE_DIR), exist_ok=True)
        merged = p.merge_rules()
        output_text = p.generate_output(merged)

        out_path = os.path.join(config.REPO_PATH, config.REWRITE_DIR, config.OUTPUT_FILE)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(output_text)

        p.update_readme(merged)
        print("Successfully generated rules and README")
    except Exception as e:
        print(f"Error in main process: {e}")
        raise

if __name__ == "__main__":
    main()
