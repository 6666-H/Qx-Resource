import os
import requests
import datetime
from datetime import timedelta
from typing import Dict, Set, List

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
            "网易云音乐去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E7%BD%91%E6%98%93%E4%BA%91%E9%9F%B3%E4%B9%90%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
            "京东比价": "https://raw.githubusercontent.com/mw418/Loon/main/script/jd_price.js",
            "1998解锁": "https://raw.githubusercontent.com/Yu9191/Rewrite/main/1998.js",
            "TF多账号合并":"https://raw.githubusercontent.com/NobyDa/Script/master/Surge/Module/TestFlightAccount.sgmodule"
        }

class RuleProcessor:
    def __init__(self, config):
        self.config = config
        self.rule_types = {
            'general': set(),      
            'rule': set(),         
            'rewrite': set(),      
            'url_rewrite': set(),  
            'header_rewrite': set(), 
            'script': set(),       
            'host': set(),         
            'mitm': set(),         
            'panel': set(),        
            'map_local': set(),    
            'url_regex': set(),    
            'domain_suffix': set(), 
            'ip_cidr': set(),      
            'ssid_setting': set(), 
            'filter': set(),       
            'dns': set(),          
            'policy': set()        
        }

    def _process_reject_rules(self, rules: Set[str]) -> Set[str]:
        """处理reject规则的优先级"""
        url_rules = {}
        
        priorities = {
            'reject-dict': 3,
            'reject-array': 3,
            'reject-200': 2,
            'reject-img': 2,
            'reject': 1
        }

        for rule in rules:
            try:
                url_pattern = rule.split('url')[0].strip()
                action = rule.split('url')[1].strip()

                current_priority = 0
                for action_type, priority in priorities.items():
                    if action_type in action:
                        current_priority = priority
                        break

                if url_pattern in url_rules:
                    existing_action = url_rules[url_pattern].split('url')[1].strip()
                    existing_priority = 0
                    for action_type, priority in priorities.items():
                        if action_type in existing_action:
                            existing_priority = priority
                            break
                    
                    if current_priority > existing_priority:
                        url_rules[url_pattern] = rule
                else:
                    url_rules[url_pattern] = rule

            except Exception as e:
                print(f"Error processing rule: {rule}")
                continue

        return set(url_rules.values())

    def _process_response_rules(self, rules: Set[str]) -> Set[str]:
        """处理response规则的优先级"""
        url_rules = {}
        
        priorities = {
            'random-response': 2,
            'response-body': 1
        }

        for rule in rules:
            try:
                url_pattern = rule.split('url')[0].strip()
                action = rule.split('url')[1].strip()

                current_priority = 0
                for action_type, priority in priorities.items():
                    if action_type in action:
                        current_priority = priority
                        break

                if url_pattern in url_rules:
                    existing_action = url_rules[url_pattern].split('url')[1].strip()
                    existing_priority = 0
                    for action_type, priority in priorities.items():
                        if action_type in existing_action:
                            existing_priority = priority
                            break
                    
                    if current_priority > existing_priority:
                        url_rules[url_pattern] = rule
                else:
                    url_rules[url_pattern] = rule

            except Exception as e:
                print(f"Error processing rule: {rule}")
                continue

        return set(url_rules.values())

    def _process_script_rules(self, rules: Set[str]) -> Set[str]:
        """处理脚本规则，保留第一个遇到的规则"""
        url_rules = {}
        
        for rule in rules:
            try:
                parts = rule.split('url')
                if len(parts) != 2:
                    continue
                    
                url_pattern = parts[0].strip()
                
                if url_pattern not in url_rules:
                    url_rules[url_pattern] = rule

            except Exception as e:
                print(f"Error processing script rule: {rule}")
                continue

        return set(url_rules.values())

    def _process_request_rules(self, rules: Set[str]) -> Set[str]:
        """处理http-request类规则,保持原格式不变"""
        return rules

    def process_rules(self, content: str) -> Dict[str, Set[str]]:
        """处理规则内容"""
        if not content:
            return self.rule_types.copy()
            
        current_section = None
        in_js_block = False
        temp_rules = {
            'reject_rules': set(),
            'response_rules': set(),
            'script_rules': set(),
            'request_rules': set(),
            'other_rules': set()
        }
        
        lines = content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳过空行和单行注释
            if not line or line.startswith('#'):
                i += 1
                continue
                
            # 检测 JavaScript 代码块开始
            if line.startswith('/*'):
                in_js_block = True
                i += 1
                continue
                
            # 检测 JavaScript 代码块结束
            if line.startswith('*/'):
                in_js_block = False
                i += 1
                continue
                
            # 在 JavaScript 代码块中跳过处理
            if in_js_block:
                i += 1
                continue
                
            # 检测其他可能的 JavaScript 代码标记
            if (line.startswith('function') or 
                line.startswith('var') or 
                line.startswith('let') or 
                line.startswith('const') or
                line.startswith('class') or
                line.startswith('return') or
                line.startswith('if') or
                line.startswith('for')):
                i += 1
                continue

            section = self._detect_section(line)
            if section:
                current_section = section
                i += 1
                continue
                
            if 'http-request' in line:
                temp_rules['request_rules'].add(line)
            elif 'script-response-body' in line or 'script-request-body' in line:
                temp_rules['script_rules'].add(line)
            elif 'reject' in line:
                temp_rules['reject_rules'].add(line)
            elif 'response-body' in line or 'random-response' in line:
                temp_rules['response_rules'].add(line)
            else:
                temp_rules['other_rules'].add(line)
                
            i += 1

        processed_reject_rules = self._process_reject_rules(temp_rules['reject_rules'])
        processed_response_rules = self._process_response_rules(temp_rules['response_rules'])
        processed_script_rules = self._process_script_rules(temp_rules['script_rules'])
        processed_request_rules = self._process_request_rules(temp_rules['request_rules'])
        
        self.rule_types['rewrite'].update(processed_reject_rules)
        self.rule_types['rewrite'].update(processed_response_rules)
        self.rule_types['rewrite'].update(processed_script_rules)
        self.rule_types['rewrite'].update(processed_request_rules)
        self.rule_types['rewrite'].update(temp_rules['other_rules'])
        
        return self.rule_types

    def _detect_section(self, line: str) -> str:
        """检测规则所属段落"""
        line_lower = line.lower()
        
        section_markers = {
            'general': ['[general]'],
            'rule': ['[rule]'],
            'rewrite': ['[rewrite]', '[rewrite_local]'],
            'url_rewrite': ['[url rewrite]', '[url_rewrite]'],
            'header_rewrite': ['[header rewrite]', '[header_rewrite]'],
            'script': ['[script]'],
            'mitm': ['[mitm]'],
            'panel': ['[panel]'],
            'map_local': ['[map local]', '[map_local]'],
            'filter': ['[filter]'],
            'dns': ['[dns]'],
            'policy': ['[policy]']
        }
        
        for section, markers in section_markers.items():
            if any(line_lower.startswith(marker) for marker in markers):
                return section
        return None

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

    def merge_rules(self) -> Dict[str, Set[str]]:
        """合并所有规则"""
        for name, url in self.config.REWRITE_SOURCES.items():
            print(f"Downloading {name}...")
            _, content = self.download_rule(name, url)
            if content:
                self.process_rules(content)
        return self.rule_types

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

        sections = [
            ('GENERAL', 'general'),
            ('RULE', 'rule'),
            ('REWRITE', 'rewrite'),
            ('URL-REWRITE', 'url_rewrite'),
            ('HEADER-REWRITE', 'header_rewrite'),
            ('SCRIPT', 'script'),
            ('PANEL', 'panel'),
            ('MAP-LOCAL', 'map_local'),
            ('DOMAIN-SUFFIX', 'domain_suffix'),
            ('IP-CIDR', 'ip_cidr'),
            ('SSID-SETTING', 'ssid_setting'),
            ('FILTER', 'filter'),
            ('DNS', 'dns'),
            ('POLICY', 'policy')
        ]

        for section_name, section_key in sections:
            if rules[section_key]:
                content.extend([
                    f"[{section_name}]",
                    *sorted(rules[section_key]),
                    ""
                ])

        if rules['host']:
            content.extend([
                "[MITM]",
                f"hostname = {self.deduplicate_hostnames(rules['host'])}",
                ""
            ])

        return '\n'.join(content)

    def update_readme(self, rules: Dict[str, Set[str]]):
        """更新README文件"""
        beijing_time = datetime.datetime.utcnow() + timedelta(hours=8)
        
        content = f"""# 自建重写规则合集

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 规则说明
本重写规则集合并自各个开源规则，去除重复规则。
- 重写规则数量：{len(rules['rewrite'])}
- 主机名数量：{len(rules['host'])}
- 脚本数量：{len(rules['script'])}

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
