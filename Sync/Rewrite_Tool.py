import os
import requests
import datetime
from datetime import timedelta
from typing import Dict, Set, List

class Config:
    def __init__(self):
        self.REPO_PATH = "Rewrite"
        self.REWRITE_DIR = "Tool" 
        self.OUTPUT_FILE = "Tool.config"
        self.README_PATH = "README_Rewrite.md"
        self.TIMEOUT = 30
        self.REWRITE_SOURCES = {
            "京东比价": "https://raw.githubusercontent.com/githubdulong/Script/master/Surge/jd_price.sgmodule",
            "懒人听书": "https://raw.githubusercontent.com/WeiGiegie/666/main/lrts.js",
            "谷歌重定向":"https://raw.githubusercontent.com/6666-H/Qx-Resource/refs/heads/main/Manual/Rewrite/GoogleToSearch.config",
            "ReLens":"https://raw.githubusercontent.com/chxm1023/Rewrite/main/ReLens.js",
            "微信110解锁被屏蔽的URL":"https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/Function/UnblockURLinWeChat.conf",
            "哔哩哔哩广告净化":"https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/BilibiliAds.conf",
            "Google自动翻页":"https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/Html/EndlessGoogle.conf",
            "百度搜索去广告":"https://raw.githubusercontent.com/limbopro/Adblock4limbo/main/Adblock4limbo.conf"
        }

class RuleProcessor:
    def __init__(self, config):
        self.config = config

    def download_rule(self, name: str, url: str) -> tuple:
        try:
            response = requests.get(url, timeout=self.config.TIMEOUT)
            response.raise_for_status()
            return name, response.text
        except Exception as e:
            print(f"Error downloading {name}: {e}")
            return name, None

    def process_rules(self, content: str) -> Dict[str, any]:
        rules = {
            'sections': {},
            'host': set()
        }

        if not content:
            return rules

        lines = content.splitlines()
        current_section = '[rewrite]'  # 默认标签
        rules['sections'][current_section] = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue

            # 标签行
            if line.startswith('[') and line.endswith(']'):
                current_section = line.lower()
                if current_section not in rules['sections']:
                    rules['sections'][current_section] = []
                continue

            # 添加到当前标签
            rules['sections'][current_section].append(line)

            # 收集 hostname
            if 'hostname' in line.lower() and '=' in line:
                hostname = line.split('=')[1].strip()
                if hostname:
                    rules['host'].update(hostname.split(','))

        return rules

    def merge_rules(self) -> Dict[str, any]:
        merged_rules = {
            'sections': {},
            'host': set()
        }

        for name, url in self.config.REWRITE_SOURCES.items():
            print(f"Downloading {name}...")
            _, content = self.download_rule(name, url)
            if content:
                rules = self.process_rules(content)
                for section, contents in rules['sections'].items():
                    if section not in merged_rules['sections']:
                        merged_rules['sections'][section] = []
                    if contents:
                        merged_rules['sections'][section].append(f"# {name}")
                        merged_rules['sections'][section].extend(contents)
                merged_rules['host'].update(rules['host'])

        return merged_rules

    def generate_output(self, rules: Dict[str, any]) -> str:
        beijing_time = datetime.datetime.utcnow() + timedelta(hours=8)
        content = [
            f"#!name = 自建重写解锁合集",
            f"#!desc = 自建重写解锁合集",
            f"# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)",
            "# 合并自以下源：",
            *[f"# {name}: {url}" for name, url in self.config.REWRITE_SOURCES.items()],
            ""
        ]

        for section, contents in rules['sections'].items():
            if '[mitm]' not in section:
                content.extend([
                    section.upper(),
                    *contents,
                    ""
                ])

        if rules['host']:
            content.extend([
                "[MITM]",
                f"hostname = {','.join(sorted(rules['host']))}",
                ""
            ])

        return '\n'.join(content)

    def update_readme(self, rules: Dict[str, any]):
        beijing_time = datetime.datetime.utcnow() + timedelta(hours=8)
        section_counts = {}
        for section, contents in rules['sections'].items():
            rule_count = len([line for line in contents if not line.startswith('#')])
            section_counts[section] = rule_count

        content = f"""# 自建重写解锁合集

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 规则说明
本重写规则集合并自各个开源规则。

## 规则统计
- MITM主机数量：{len(rules['host'])}
{"".join([f'- {section.upper()} 规则数量：{count}\n' for section, count in section_counts.items()])}

## 规则来源
{chr(10).join([f'- {name}: {url}' for name, url in self.config.REWRITE_SOURCES.items()])}
"""

        os.makedirs(self.config.REPO_PATH, exist_ok=True)
        with open(os.path.join(self.config.REPO_PATH, self.config.README_PATH), 'w', encoding='utf-8') as f:
            f.write(content)

def main():
    config = Config()
    processor = RuleProcessor(config)

    try:
        os.makedirs(os.path.join(config.REPO_PATH, config.REWRITE_DIR), exist_ok=True)
        rules = processor.merge_rules()
        output = processor.generate_output(rules)

        output_path = os.path.join(config.REPO_PATH, config.REWRITE_DIR, config.OUTPUT_FILE)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)

        processor.update_readme(rules)
        print("Successfully generated rules and README")
    except Exception as e:
        print(f"Error in main process: {e}")
        raise

if __name__ == "__main__":
    main()
