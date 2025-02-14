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
        
        # 规则源
        self.REWRITE_SOURCES = {
            "京东比价": "https://raw.githubusercontent.com/mw418/Loon/main/script/jd_price.js",
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

    def process_rules(self, content: str) -> Dict[str, Set[str]]:
        """处理规则内容"""
        rules = {
            'sections': [],     # 使用列表存储所有标签内容(包含标签名、注释和规则)
            'host': set()       # 单独存储所有hostname用于最后合并
        }
        
        if not content:
            return rules
                
        lines = content.splitlines()
        current_section = None
        current_comment = None
        
        for line in lines:
            line = line.strip()
            
            # 跳过空行
            if not line:
                continue
                
            # 检查是否是标签行 - 匹配[xxx]格式
            if line.startswith('[') and line.endswith(']'):
                current_section = line
                if not any(line in section for section, _ in rules['sections']):
                    rules['sections'].append([line, []])  # [标签名, [内容列表]]
                continue
                
            # 处理注释行
            if line.startswith('#') or line.startswith('//'):
                current_comment = line
                continue
                
            # 处理规则内容
            if current_section:
                for section, contents in rules['sections']:
                    if section == current_section:
                        if current_comment:  # 如果有注释,添加注释
                            contents.append(current_comment)
                            current_comment = None
                        contents.append(line)
                        # 如果是hostname行,额外收集
                        if 'hostname' in line.lower():
                            hostname = line.split('=')[1].strip()
                            if hostname:
                                rules['host'].update(hostname.split(','))
                        break
        
        return rules

    def merge_rules(self) -> Dict[str, Set[str]]:
        """合并所有规则"""
        merged_rules = {
            'sections': [],
            'host': set()
        }
        
        # 下载和处理所有规则
        for name, url in self.config.REWRITE_SOURCES.items():
            print(f"Downloading {name}...")
            _, content = self.download_rule(name, url)
            if content:
                rules = self.process_rules(content)
                merged_rules['sections'].extend(rules['sections'])
                merged_rules['host'].update(rules['host'])
        
        return merged_rules

    def generate_output(self, rules: Dict[str, Set[str]]) -> str:
        """生成最终的规则文件"""
        beijing_time = datetime.datetime.utcnow() + timedelta(hours=8)
        
        content = [
            f"#!name = 自建重写规则合集",
            f"#!desc = 自建重写规则合集",
            f"# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)",
            "# 合并自以下源：",
            *[f"# {name}: {url}" for name, url in self.config.REWRITE_SOURCES.items()],
            ""
        ]
        
        # 首先添加 [MITM] 部分
        if rules['host']:
            content.extend([
                "[MITM]",
                f"hostname = {','.join(sorted(rules['host']))}",
                ""
            ])
        
        # 添加其他所有标签的内容
        for section, contents in rules['sections']:
            if '[mitm]' not in section.lower():  # 跳过MITM部分因为已经合并了
                content.extend([
                    section,  # 添加标签
                    *contents,  # 展开该标签下的所有内容
                    ""        # 添加空行分隔
                ])
        
        return '\n'.join(content)

    def update_readme(self, rules: Dict[str, Set[str]]):
        """更新README文件"""
        beijing_time = datetime.datetime.utcnow() + timedelta(hours=8)
        
        # 统计每个标签下的规则数量
        section_counts = {}
        for section, contents in rules['sections']:
            # 只统计非注释行
            rule_count = len([line for line in contents if not line.startswith('#') and not line.startswith('//')])
            section_counts[section] = rule_count
        
        content = f"""# 自建重写规则合集

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 规则说明
本重写规则集合并自各个开源规则。

## 规则统计
- MITM主机数量：{len(rules['host'])}
{"".join([f'- {section} 规则数量：{count}\n' for section, count in section_counts.items()])}

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
