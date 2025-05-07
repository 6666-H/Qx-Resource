import os
import re
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
        # "京东比价": "https://raw.githubusercontent.com/mw418/Loon/main/script/jd_price.js",
        # 规则源
        self.REWRITE_SOURCES = {
            "京东比价": "https://raw.githubusercontent.com/githubdulong/Script/master/Surge/jd_price.sgmodule",
            "1998解锁": "https://raw.githubusercontent.com/Yu9191/Rewrite/main/1998.js"
        }

class RuleProcessor:
    def __init__(self, config):
        self.config = config

    def download_rule(self, name: str, url: str) -> tuple:
        """下载规则源"""
        try:
            response = requests.get(url, timeout=self.config.TIMEOUT)
            response.raise_for_status()
            content = response.text
            return name, content
        except Exception as e:
            print(f"Error downloading {name}: {e}")
            return name, None

    def process_rules(self, content: str) -> Dict[str, any]:
        """处理规则内容"""
        rules = {
            'sections': {},       # 使用字典存储所有标签内容 {标签名: [内容列表]}
            'host': set()        # 单独存储所有hostname
        }
        
        if not content:
            return rules
            
        lines = content.splitlines()
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # 跳过空行
            if not line:
                continue
            
            # 检查是否是标签行 - 匹配[xxx]格式
            if line.startswith('[') and line.endswith(']'):
                current_section = line.lower()  # 统一转换为小写
                if current_section not in rules['sections']:
                    rules['sections'][current_section] = []
                continue
            
            # 处理规则内容
            if current_section:
                # 只保留规则行
                if not line.startswith('#') and not line.startswith('//'):
                    rules['sections'][current_section].append(line)
                    
                    # 如果是hostname行,额外收集
                    if 'hostname' in line.lower() and '=' in line:
                        hostname = line.split('=')[1].strip()
                        if hostname:
                            rules['host'].update(hostname.split(','))

        return rules

    def merge_rules(self) -> Dict[str, any]:
        """合并所有规则"""
        merged_rules = {
            'sections': {},
            'host': set()
        }
        
        # 下载和处理所有规则
        for name, url in self.config.REWRITE_SOURCES.items():
            print(f"Downloading {name}...")
            _, content = self.download_rule(name, url)
            if content:
                rules = self.process_rules(content)
                # 合并各标签内容
                for section, contents in rules['sections'].items():
                    if section not in merged_rules['sections']:
                        merged_rules['sections'][section] = []
                    if contents:  # 只有当有内容时才添加源名称注释和内容
                        merged_rules['sections'][section].append(f"# {name}")
                        merged_rules['sections'][section].extend(contents)
                merged_rules['host'].update(rules['host'])
        
        return merged_rules

    def generate_output(self, rules: Dict[str, any]) -> str:
        """生成最终的规则文件"""
        beijing_time = datetime.datetime.utcnow() + timedelta(hours=8)
        
        content = [
            f"#!name = 自建重写解锁合集",
            f"#!desc = 自建重写解锁合集",
            f"# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)",
            "# 合并自以下源：",
            *[f"# {name}: {url}" for name, url in self.config.REWRITE_SOURCES.items()],
            ""
        ]
        
        # 添加其他所有标签的内容
        for section, contents in rules['sections'].items():
            if '[mitm]' not in section:  # 跳过MITM部分留到最后
                content.extend([
                    section.upper(),  # 添加标签，转换为大写
                    *contents,  # 展开该标签下的所有内容
                    ""        # 添加空行分隔
                ])
        
        # 最后添加 [MITM] 部分
        if rules['host']:
            content.extend([
                "[MITM]",
                f"hostname = {','.join(sorted(rules['host']))}",
                ""
            ])
        
        return '\n'.join(content)

    def update_readme(self, rules: Dict[str, any]):
        """更新README文件"""
        beijing_time = datetime.datetime.utcnow() + timedelta(hours=8)
        
        # 统计每个标签下的规则数量
        section_counts = {}
        for section, contents in rules['sections'].items():
            # 只统计非注释行
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
        # 创建输出目录
        os.makedirs(os.path.join(config.REPO_PATH, config.REWRITE_DIR), exist_ok=True)
        
        # 合并规则
        rules = processor.merge_rules()
        
        # 生成输出文件
        output = processor.generate_output(rules)
        
        # 写入文件
        output_path = os.path.join(config.REPO_PATH, config.REWRITE_DIR, config.OUTPUT_FILE)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
            
        # 更新 README
        processor.update_readme(rules)
        
        print("Successfully generated rules and README")
        
    except Exception as e:
        print(f"Error in main process: {e}")
        raise

if __name__ == "__main__":
    main()
