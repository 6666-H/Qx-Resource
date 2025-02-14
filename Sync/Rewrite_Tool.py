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
        self.MAX_WORKERS = 10
        self.TIMEOUT = 30
        
        # 规则源
        self.REWRITE_SOURCES = {
            "京东比价": "https://raw.githubusercontent.com/mw418/Loon/main/script/jd_price.js",
            "1998解锁": "https://raw.githubusercontent.com/Yu9191/Rewrite/main/1998.js"
        }

class RuleProcessor:
    def __init__(self, config):
        self.config = config
        # 定义reject规则优先级
        self.REJECT_PRIORITY = {
            'reject-dict': 1,
            'reject-array': 2,
            'reject-200': 3,
            'reject-img': 4,
            'reject': 5
        }
        # 定义script规则类型
        self.SCRIPT_TYPES = {
            'script-response-body',
            'script-request-body',
            'script-response-header',
            'script-request-header'
        }

    def _convert_surge_rule(self, line: str) -> str:
        """将 Surge 格式的规则转换为 QuantumultX 格式"""
        try:
            # 解析规则
            name, content = line.split('=', 1)
            content = content.strip()
            
            # 提取关键信息
            rule_type = None
            pattern = None
            script_path = None
            requires_body = False
            
            # 解析参数
            params = []
            current_param = ''
            in_quote = False
            
            # 先处理引号内的内容
            for char in content:
                if char == ',' and not in_quote:
                    if current_param.strip():
                        params.append(current_param.strip())
                    current_param = ''
                elif char == '"':
                    in_quote = not in_quote
                    current_param += char
                else:
                    current_param += char
            if current_param.strip():
                params.append(current_param.strip())

            # 解析参数
            for param in params:
                param = param.strip()
                if param.startswith('type='):
                    rule_type = param.split('=')[1]
                elif param.startswith('pattern='):
                    pattern = param.split('=', 1)[1].strip('"')
                elif param.startswith('script-path='):
                    script_path = param.split('=', 1)[1].strip('"')
                elif param.startswith('requires-body='):
                    requires_body = param.split('=')[1].lower() == 'true'
            
            if not pattern or not script_path:
                return line

            # 转换规则类型
            if rule_type == 'http-response':
                qx_type = 'script-response-body' if requires_body else 'script-response-header'
            elif rule_type == 'http-request':
                qx_type = 'script-request-body' if requires_body else 'script-request-header'
            else:
                return line
                
            # 构建 QuantumultX 格式的规则
            return f"{pattern} url {qx_type} {script_path}"
        except Exception as e:
            print(f"Error converting rule: {e}")
            return line

    def _normalize_url_pattern(self, url: str) -> str:
        """标准化URL模式，便于比较"""
        # 移除 ^ 和 $ 符号
        url = url.strip('^$')
        # 将 https?:\/\/ 统一处理
        url = url.replace('https?://', '').replace('http?://', '')
        # 移除转义符
        url = url.replace('\\', '')
        # 处理尾部斜杠，统一移除
        url = url.rstrip('/')
        # 处理可选的问号
        url = url.rstrip('?')
        # 处理版本号通配符
        url = url.replace('/v\\d', '/v*')
        return url

    def _sort_rules(self, rules: Set[str]) -> List[str]:
        """根据优先级对规则进行排序"""
        sorted_rules = sorted(list(rules))
        return sorted_rules

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
            'rewrite_local': set(),  # 用于存储重写规则
            'host': set()           # 用于存储mitm主机名
        }
        
        if not content:
            return rules
            
        lines = content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳过空行和普通注释
            if not line or line.startswith('//'):
                i += 1
                continue
                
            # 如果找到mitm hostname
            if 'hostname' in line.lower() and '=' in line:
                if 'host' not in rules:
                    rules['host'] = set()
                self._process_hostname(line, rules)
                i += 1
                continue
                
            # 如果是重写规则（通常包含url和script-path）
            if ('url script-' in line.lower() or 
                'http-request' in line.lower() or 
                'http-response' in line.lower()):
                # 清理并标准化规则
                line = line.strip()
                if not line.startswith('#'):  # 跳过注释的规则
                    rules['rewrite_local'].add(line)
                i += 1
                continue
                
            # 如果遇到js代码块，跳过整个代码块
            if line.startswith('/*'):
                while i < len(lines) and '*/' not in lines[i]:
                    i += 1
                i += 1  # 跳过结束的 */
                continue
            
            i += 1
        
        return rules

    def _process_hostname(self, line: str, rules: Dict[str, Set[str]]):
        """处理hostname规则"""
        if '=' in line:
            hostnames = line.split('=')[1].strip()
            hostnames = hostnames.replace('%APPEND%', '').strip()
            for hostname in hostnames.split(','):
                hostname = hostname.strip()
                if hostname and not hostname.startswith('#'):
                    rules['host'].add(hostname)

    def deduplicate_hostnames(self, hostnames: Set[str]) -> str:
        """去重和排序hostname"""
        # 转换为list并排序
        hostname_list = sorted(hostnames)
        
        # 处理通配符域名
        wildcards = set()
        specific = set()
        
        for hostname in hostname_list:
            if hostname.startswith('*'):
                wildcards.add(hostname)
            else:
                specific.add(hostname)
        
        # 移除被通配符覆盖的具体域名
        final_specific = set()
        for hostname in specific:
            should_keep = True
            for wildcard in wildcards:
                if self._is_covered_by_wildcard(hostname, wildcard):
                    should_keep = False
                    break
            if should_keep:
                final_specific.add(hostname)
        
        # 合并结果
        final_hostnames = sorted(wildcards | final_specific)
        return ','.join(final_hostnames)
    
    def _is_covered_by_wildcard(self, hostname: str, wildcard: str) -> bool:
        """检查域名是否被通配符覆盖"""
        if not wildcard.startswith('*'):
            return False
        domain_suffix = wildcard[1:]
        return hostname.endswith(domain_suffix)
    
    def merge_rules(self) -> Dict[str, Set[str]]:
        """合并所有规则"""
        merged_rules = {}
        
        # 下载和处理所有规则
        for name, url in self.config.REWRITE_SOURCES.items():
            print(f"Downloading {name}...")
            _, content = self.download_rule(name, url)
            if content:
                rules = self.process_rules(content)
                # 确保所有遇到的标签类型都在merged_rules中存在
                for key in rules:
                    if key not in merged_rules:
                        merged_rules[key] = set()
                    merged_rules[key].update(rules[key])
        
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
        if 'host' in rules and rules['host']:
            content.extend([
                "[MITM]",
                f"hostname = {self.deduplicate_hostnames(rules['host'])}",
                ""
            ])
        
        # 然后添加重写规则
        if 'rewrite_local' in rules and rules['rewrite_local']:
            content.extend([
                "[REWRITE_LOCAL]",
                *sorted(rules['rewrite_local']),  # 对规则进行排序
                ""
            ])
        
        return '\n'.join(content)

    def update_readme(self, rules: Dict[str, Set[str]]):
        """更新README文件"""
        beijing_time = datetime.datetime.utcnow() + timedelta(hours=8)
        
        # 生成规则统计信息
        rule_counts = []
        for section, rules_set in rules.items():
            rule_counts.append(f"- {section.title()} 规则数量：{len(rules_set)}")
        
        content = f"""# 自建重写规则合集

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 规则说明
本重写规则集合并自各个开源规则，去除重复规则。
{chr(10).join(rule_counts)}

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
