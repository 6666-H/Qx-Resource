import os
import re
import requests
import datetime
from datetime import timedelta
from typing import Dict, Any, List, Set, Tuple

class Config:
    def __init__(self):
        self.REPO_PATH = "Rewrite"
        self.REWRITE_DIR = "Tool"
        self.OUTPUT_FILE = "Tool.config"
        self.README_PATH = "README_Rewrite.md"
        self.TIMEOUT = 30
        # 规则源（保持你原来的）
        self.REWRITE_SOURCES = {
            "京东比价": "https://raw.githubusercontent.com/githubdulong/Script/master/Surge/jd_price.sgmodule",
            "懒人听书": "https://raw.githubusercontent.com/WeiGiegie/666/main/lrts.js",
            "谷歌重定向": "https://raw.githubusercontent.com/6666-H/Qx-Resource/refs/heads/main/Manual/Rewrite/GoogleToSearch.config",
            "ReLens": "https://raw.githubusercontent.com/chxm1023/Rewrite/main/ReLens.js",
            "哔哩哔哩广告净化": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/BilibiliAds.conf"
        }

class RuleProcessor:
    HOST_RE = re.compile(r'(?i)^\s*hostname\s*=\s*(.+)$')  # 捕获 hostname 行
    SECTION_RE = re.compile(r'^\s*\[(.+?)\]\s*$')          # 捕获 [section]
    COMMENT_RE = re.compile(r'^\s*(#|//)')                 # 注释行

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
        """
        支持：
        - 去掉 %APPEND% / %REJECT% / %DELETE% 等占位
        - 去掉行内注释 (# 或 //)
        - 逗号分割，去空格、去尾随逗号
        - 小写
        """
        # 去除行内注释
        no_comment = re.split(r'\s#|//', raw_value, maxsplit=1)[0].strip()
        # 移除占位符
        no_placeholder = re.sub(r'%[A-Za-z_]+%', '', no_comment).strip()
        # 分割并清洗
        parts = [p.strip().strip(',') for p in no_placeholder.split(',')]
        hosts = [p.lower() for p in parts if p]
        return hosts

    # -------- 处理单个源文本 --------
    def process_rules(self, content: str) -> Dict[str, Any]:
        """
        返回：
        {
          'sections': { '[rewrite]': [...], ... },
          'host': set([...]),
          'mitm_other': list([...])  # [MITM] 下除 hostname 外的其它配置项（去重）
        }
        规则：
        - 无标签的行默认归到 [rewrite]
        - 任意位置的 'hostname = ...' 只汇总到 host，不写回 sections
        - [MITM] 下的非 hostname 行保留到 mitm_other（合并时去重）
        - 忽略注释与空行
        """
        out = {
            'sections': {},     # {section_lower: [lines]}
            'host': set(),      # {host1, host2, ...}
            'mitm_other': []    # list of lines, preserve order; we'll dedup later
        }

        if not content:
            return out

        lines = content.splitlines()
        current_section = '[rewrite]'  # 默认标签
        out['sections'][current_section] = []

        # 用于 [MITM] 其它键去重（保持顺序）
        seen_mitm_other = set()

        for raw in lines:
            line = raw.strip()
            if not line or self.COMMENT_RE.match(line):
                continue

            # 标签行
            m_sec = self.SECTION_RE.match(line)
            if m_sec:
                current_section = f"[{m_sec.group(1).strip().lower()}]"
                if current_section not in out['sections']:
                    out['sections'][current_section] = []
                continue

            # hostname 行（无论在哪个 section）
            m_host = self.HOST_RE.match(line)
            if m_host:
                hosts = self._parse_hostnames(m_host.group(1))
                out['host'].update(hosts)
                # 不写回原标签
                continue

            # [MITM] 下的其它键（非 hostname）
            if current_section == '[mitm]':
                # 避免把注释或空行放进来，且去重
                key = line.lower()
                if key not in seen_mitm_other:
                    out['mitm_other'].append(line)
                    seen_mitm_other.add(key)
                continue

            # 其它规则写入当前标签
            out['sections'][current_section].append(line)

        return out

    # -------- 合并多个源 --------
    def merge_rules(self) -> Dict[str, Any]:
        merged = {
            'sections': {},     # 合并后的各标签
            'host': set(),      # 合并后的 hostname
            'mitm_other': []    # 合并后的 [MITM] 其它键
        }

        # 用于 [MITM] 其它键的去重（全局）
        seen_mitm_other = set()

        for name, url in self.config.REWRITE_SOURCES.items():
            print(f"Downloading {name}...")
            _, content = self.download_rule(name, url)
            if not content:
                continue

            rules = self.process_rules(content)

            # 合并 section
            for sec, lines in rules['sections'].items():
                if sec not in merged['sections']:
                    merged['sections'][sec] = []
                if lines:
                    merged['sections'][sec].append(f"# {name}")
                    merged['sections'][sec].extend(lines)

            # 合并 host
            merged['host'].update(rules['host'])

            # 合并 MITM 其它键
            for line in rules['mitm_other']:
                key = line.lower()
                if key not in seen_mitm_other:
                    merged['mitm_other'].append(line)
                    seen_mitm_other.add(key)

        return merged

    # -------- 生成输出内容 --------
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

        # 输出除 MITM 以外的各标签（统一大写输出以保持风格一致）
        for sec, lines in merged['sections'].items():
            if sec == '[mitm]':
                continue
            if not lines:
                continue
            body.append(sec.upper())
            body.extend(lines)
            body.append("")  # 空行分隔

        # 组装 [MITM]
        mitm_block: List[str] = []
        # 先放其它键
        if merged['mitm_other']:
            mitm_block.extend(merged['mitm_other'])
        # 再放 hostname
        if merged['host']:
            # 排序后拼接
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
        # 统计各标签非注释行
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
        # 创建输出目录
        os.makedirs(os.path.join(config.REPO_PATH, config.REWRITE_DIR), exist_ok=True)

        # 合并
        merged = p.merge_rules()

        # 生成输出文本
        output_text = p.generate_output(merged)

        # 写入规则文件
        out_path = os.path.join(config.REPO_PATH, config.REWRITE_DIR, config.OUTPUT_FILE)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(output_text)

        # 更新 README
        p.update_readme(merged)

        print("Successfully generated rules and README")
    except Exception as e:
        print(f"Error in main process: {e}")
        raise

if __name__ == "__main__":
    main()
