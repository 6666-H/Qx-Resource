import os
import requests
import datetime
from datetime import timedelta
from typing import Dict, Set, List, Tuple

class Config:
    def __init__(self):
        self.REPO_PATH = "Rewrite"
        self.REWRITE_DIR = "Advertising"
        self.OUTPUT_FILE = "Ad.conf"
        self.README_PATH = "README_Rewrite.md"
        self.MAX_WORKERS = 10
        self.TIMEOUT = 30
        
        # 规则源
        self.REWRITE_SOURCES = {
            "阻止常见的 HTTPDNS 服务器": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/%E6%8B%A6%E6%88%AAHTTPDNS.official.sgmodule",
            "广告平台拦截器": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%B9%BF%E5%91%8A%E5%B9%B3%E5%8F%B0%E6%8B%A6%E6%88%AA%E5%99%A8.sgmodule",
            "whatshubs开屏屏蔽": "https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/Manual/Rewrite/Adultraplus.config",
            "whatshubAdBlock":"https://raw.githubusercontent.com/deezertidal/QuantumultX-Rewrite/refs/heads/master/rewrite/AdBlock.conf",
            "chxm去广告": "https://raw.githubusercontent.com/chxm1023/Advertising/main/AppAd.conf",
            "墨鱼去开屏V2.0": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/StartUp.conf",
            "广告拦截精简版": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/QuantumultX/AdvertisingLite/AdvertisingLite.conf",
            "去广告重写": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/chongxie.txt",
            "整合广告拦截": "https://raw.githubusercontent.com/weiyesing/QuantumultX/GenMuLu/ChongXieGuiZe/QuGuangGao/To%20advertise.conf",
            "surge去广告":"https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/%E6%96%B0%E6%89%8B%E5%8F%8B%E5%A5%BD%E3%81%AE%E5%8E%BB%E5%B9%BF%E5%91%8A%E9%9B%86%E5%90%88.official.sgmodule",
            "YouTube去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/Youtube%20%E5%8E%BB%E5%B9%BF%E5%91%8A%20(%E4%B8%8D%E5%8E%BB%E8%B4%B4%E7%89%87).official.sgmodule",
            "YouTube双语翻译": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Beta/YouTube%E7%BF%BB%E8%AF%91.beta.sgmodule",
            "小红书去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%B0%8F%E7%BA%A2%E4%B9%A6%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
            "微博去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%BE%AE%E5%8D%9A%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
            "小黑盒去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%B0%8F%E9%BB%91%E7%9B%92%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
            "网易云音乐去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E7%BD%91%E6%98%93%E4%BA%91%E9%9F%B3%E4%B9%90%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule"
        }

class RuleProcessor:
    def __init__(self, config):
        self.config = config
        self.action_priority = {
            'reject-dict': 5,
            'reject-array': 4,
            'reject-200': 3,
            'reject-img': 2,
            'reject': 1
        }

    def download_rule(self, name: str, url: str) -> Tuple[str, str]:
        """下载规则源"""
        try:
            response = requests.get(url, timeout=self.config.TIMEOUT)
            response.raise_for_status()
            content = response.text
            return name, content
        except Exception as e:
            print(f"Error downloading {name}: {e}")
            return name, None

    def normalize_rule(self, rule: str) -> Tuple[str, str, str]:
        """解析规则，返回 (URL模式, 动作, 完整规则)"""
        if ' = type=' in rule:  # Surge格式
            try:
                name, rule_content = rule.split(' = type=', 1)
                parts = rule_content.split(', ')
                rule_type = parts[0]
                pattern = None
                script_path = None
                for part in parts:
                    if part.startswith('pattern='):
                        pattern = part.split('=', 1)[1]
                    elif part.startswith('script-path='):
                        script_path = part.split('=', 1)[1]
                
                if pattern and script_path:
                    action = 'script-response-body' if rule_type == 'http-response' else 'script-request-body'
                    full_rule = f'{pattern} url {action} {script_path}'
                    return (pattern, action, full_rule)
            except Exception as e:
                print(f"Error processing Surge rule: {e}")
                return None
        else:  # QuantumultX格式
            parts = rule.strip().split()
            if len(parts) >= 3:
                return (parts[0], parts[2], rule)
        return None

    def get_action_priority(self, action: str) -> int:
        """获取动作的优先级"""
        return self.action_priority.get(action, 0)

    def process_rules(self, content: str) -> Dict[str, Set[str]]:
        """处理规则内容"""
        temp_rules = {
            'url-rewrite': [],  # 使用列表存储未处理的规则
            'script': [],
            'host': set()
        }
        
        if not content:
            return {k: set() for k in temp_rules.keys()}
        
        # 首先处理内容,仅移除以//开头的注释行
        lines = []
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
                
            # 仅跳过以//开头的注释行    
            if line.startswith('//'):
                continue
                
            # 处理特殊的 hostname 行
            if line.startswith('#>'):
                hostname_line = line[2:].strip()
                if hostname_line:
                    for hostname in hostname_line.split(','):
                        hostname = hostname.strip()
                        if hostname:
                            temp_rules['host'].add(hostname)
                continue
                
            # 跳过其他注释行
            if line.startswith('#'):
                continue
            
            lines.append(line)
        
        # 处理剩余的有效行
        current_section = 'url-rewrite'
        for line in lines:
            # 检查是否是标签行
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1].lower()
                continue
                
            # 处理常规hostname
            if 'hostname' in line.lower():
                self._process_hostname(line, temp_rules)
                continue
            
            # 处理规则
            parsed = self.normalize_rule(line)
            if not parsed:
                continue
                
            url_pattern, action, full_rule = parsed
            
            # 根据规则类型分类存储
            if action.startswith('script'):
                temp_rules['script'].append((url_pattern, action, full_rule))
            else:
                temp_rules['url-rewrite'].append((url_pattern, action, full_rule))
        
        # 处理完所有规则后，进行优先级处理和去重
        final_rules = {
            'url-rewrite': set(),
            'script': set(),
            'host': temp_rules['host']
        }
        
        # 处理 URL rewrite 规则
        url_rules = {}  # 用于存储URL模式及其对应的规则
        for url_pattern, action, full_rule in temp_rules['url-rewrite']:
            if action.startswith('reject'):
                # reject类规则使用优先级处理
                current_priority = self.get_action_priority(action)
                if url_pattern in url_rules:
                    existing_rule, existing_action = url_rules[url_pattern]
                    existing_priority = self.get_action_priority(existing_action)
                    if current_priority > existing_priority:
                        url_rules[url_pattern] = (full_rule, action)
                else:
                    url_rules[url_pattern] = (full_rule, action)
            else:
                # 其他类型规则只保留第一个
                if url_pattern not in url_rules:
                    url_rules[url_pattern] = (full_rule, action)
        
        # 添加处理后的URL rewrite规则
        for _, (full_rule, _) in url_rules.items():
            final_rules['url-rewrite'].add(full_rule)
        
        # 处理脚本规则
        for _, _, full_rule in temp_rules['script']:
            final_rules['script'].add(full_rule)
        
        return final_rules

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
        hostname_list = sorted(hostnames)
        wildcards = set()
        specific = set()
        
        for hostname in hostname_list:
            if hostname.startswith('*'):
                wildcards.add(hostname)
            else:
                specific.add(hostname)
        
        final_specific = set()
        for hostname in specific:
            should_keep = True
            for wildcard in wildcards:
                if self._is_covered_by_wildcard(hostname, wildcard):
                    should_keep = False
                    break
            if should_keep:
                final_specific.add(hostname)
        
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
        
        for name, url in self.config.REWRITE_SOURCES.items():
            print(f"Downloading {name}...")
            _, content = self.download_rule(name, url)
            if content:
                rules = self.process_rules(content)
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
        
        if 'script' in rules and rules['script']:
            content.extend([
                "[Script]",
                *sorted(rules['script']),
                ""
            ])

        if 'url-rewrite' in rules and rules['url-rewrite']:
            content.extend([
                "[URL Rewrite]",
                *sorted(rules['url-rewrite']),
                ""
            ])
        
        if 'host' in rules and rules['host']:
            content.extend([
                "[MITM]",
                f"hostname = {self.deduplicate_hostnames(rules['host'])}",
                ""
            ])
        
        return '\n'.join(content)

    def update_readme(self, rules: Dict[str, Set[str]]):
        """更新README文件"""
        beijing_time = datetime.datetime.utcnow() + timedelta(hours=8)
        
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
