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
            "谷歌重定向":"https://raw.githubusercontent.com/6666-H/Qx-Resource/refs/heads/main/Manual/Rewrite/GoogleToSearch.config",
            "微博优化":"https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/weibo.snippet",
            "sora去水印":"https://gist.githubusercontent.com/ddgksf2013/71fca841d34a7b440408276d03da3261/raw/SoraRemoveWatermark.js"
        }

class RuleProcessor:
    HOST_RE = re.compile(r'(?i)^\s*hostname\s*=\s*(.+)$')

    def __init__(self, config: Config):
        self.config = config

    # -------- 下载规则 --------
    def download_rule(self, name: str, url: str) -> Tuple[str, str | None]:
        try:
            r = requests.get(url, timeout=self.config.TIMEOUT)
            r.raise_for_status()
            return name, r.text
        except Exception as e:
            print(f"Error downloading {name}: {e}")
            return name, None

    # -------- 解析单个文件 --------
    def process_rules(self, content: str) -> Dict[str, Any]:
        out = {
            'block': [],
            'host': set()
        }
        if not content:
            return out

        lines = content.splitlines()
        in_keep_block = False
        in_mitm_block = False

        for raw in lines:
            line = raw.strip()
            if not line:
                continue

            # 第一个 section 起始
            if not in_keep_block and line.startswith("[") and line.endswith("]"):
                in_keep_block = True
                out['block'].append(line)
                continue

            if in_keep_block:
                # 检测 [mitm] 开始
                if line.lower().startswith("[mitm]"):
                    in_mitm_block = True
                    continue

                if in_mitm_block:
                    # 收集 hostname，不写入 block
                    m_host = self.HOST_RE.match(line)
                    if m_host:
                        hosts = self._parse_hostnames(m_host.group(1))
                        out['host'].update(hosts)
                    continue

                # 其它行写入 block
                out['block'].append(raw)

        return out

    # -------- 解析 hostname --------
    def _parse_hostnames(self, raw_value: str) -> List[str]:
        no_comment = re.split(r'\s#|//', raw_value, maxsplit=1)[0].strip()
        no_placeholder = re.sub(r'%[A-Za-z_]+%', '', no_comment).strip()
        parts = [p.strip().strip(',') for p in no_placeholder.split(',')]
        hosts = [p.lower() for p in parts if p]
        return hosts

    # -------- 合并所有文件 --------
    def merge_rules(self) -> Dict[str, Any]:
        merged = {
            'blocks': [],
            'host': set()
        }

        for name, url in self.config.REWRITE_SOURCES.items():
            print(f"Downloading {name}...")
            _, content = self.download_rule(name, url)
            if not content:
                continue

            rules = self.process_rules(content)
            if rules['block']:
                merged['blocks'].append(f"# {name}")
                merged['blocks'].extend(rules['block'])
                merged['blocks'].append("")  # 分隔空行

            merged['host'].update(rules['host'])

        return merged

    # -------- 格式化 hostname，生成一行 --------
    def _format_hostnames(self, hosts: List[str]) -> List[str]:
        # 所有 hosts 拼成一行
        return ["hostname = " + ", ".join(hosts)]

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

        body = merged['blocks'][:]

        # 汇总所有 hostname 到一个 [MITM]
        if merged['host']:
            body.append("[MITM]")
            host_lines = self._format_hostnames(sorted(merged['host']))
            body.extend(host_lines)
            body.append("")

        return "\n".join(header + body)

    # -------- 更新 README --------
    def update_readme(self, merged: Dict[str, Any]) -> None:
        beijing_time = datetime.datetime.utcnow() + timedelta(hours=8)
        readme = f"""# 自建重写解锁合集

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 规则说明
- 每个源文件只保留 **第一个 [section] 开始 到 [mitm] 前 + [mitm] 内的 hostname** 
- 所有 hostname 自动归并到最终 [MITM]

## 统计信息
- MITM 主机数量：{len(merged['host'])}

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
