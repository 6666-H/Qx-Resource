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
            'rewrite': set(),
            'host': set()
        }

    def _validate_rule(self, rule: str) -> bool:
        """验证规则格式是否正确"""
        if not rule or rule.startswith('#'):
            return False
            
        # 验证重写规则格式
        if 'http-request' in rule or 'http-response' in rule:
            try:
                parts = rule.split(',')
                if len(parts) < 2:
                    return False
            except:
                return False
                
        return True

    def _convert_rule_format(self, rule: str) -> str:
        """转换不同格式的规则到统一格式"""
        # Surge/Loon格式转换
        if rule.startswith('http-') and ' requires-body=true' in rule:
            parts = rule.split(',')
            new_parts = []
            for part in parts:
                part = part.strip()
                if part.startswith('pattern='):
                    new_parts.insert(0, part.replace('pattern=', ''))
                elif part.startswith('script-path='):
                    new_parts.append(part)
                elif part.startswith('tag='):
                    new_parts.append(part)
            return ', '.join(new_parts)
            
        return rule

    def process_rules(self, content: str) -> Dict[str, Set[str]]:
        """处理规则内容"""
        if not content:
            return self.rule_types.copy()
            
        lines = content.splitlines()
        current_section = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳过注释和空行
            if not line or line.startswith('#') or line.startswith('/*') or line.startswith('*/'):
                i += 1
                continue
                
            # 检查是否是重写规则部分
            if '[rewrite_local]' in line.lower():
                i += 1
                while i < len(lines):
                    rule = lines[i].strip()
                    if not rule or rule.startswith('#'):
                        i += 1
                        continue
                    if rule.startswith('['):
                        break
                    if self._validate_rule(rule):
                        rule = self._convert_rule_format(rule)
                        self.rule_types['rewrite'].add(rule)
                    i += 1
                continue
                
            # 检查是否是MITM部分
            if '[mitm]' in line.lower():
                i += 1
                while i < len(lines):
                    rule = lines[i].strip()
                    if not rule or rule.startswith('#'):
                        i += 1
                        continue
                    if rule.startswith('['):
                        break
                    if 'hostname' in rule:
                        self._process_hostname(rule)
                    i += 1
                continue
                
            # 检查是否是完整规则
            if ('http-request' in line or 'http-response' in line or 'reject' in line) and not line.startswith('['):
                if self._validate_rule(line):
                    rule = self._convert_rule_format(line)
                    self.rule_types['rewrite'].add(rule)
                
            i += 1
                
        return self.rule_types

    def _process_hostname(self, line: str):
        """处理hostname规则"""
        if '=' in line:
            hostnames = line.split('=')[1].strip()
            hostnames = hostnames.replace('%APPEND%', '').strip()
            for hostname in hostnames.split(','):
                hostname = hostname.strip()
                if hostname and not hostname.startswith('#'):
                    self.rule_types['host'].add(hostname)

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
        # 对规则进行分类
        rewrite_rules = {
            'request': set(),
            'response': set(),
            'reject': set(),
            'other': set()
        }
        
        for rule in rules['rewrite']:
            if 'http-request' in rule:
                rewrite_rules['request'].add(rule)
            elif 'http-response' in rule:
                rewrite_rules['response'].add(rule)
            elif 'reject' in rule:
                rewrite_rules['reject'].add(rule)
            else:
                rewrite_rules['other'].add(rule)
        
        content = ["[rewrite_local]"]
        
        # 按照类型添加规则
        if rewrite_rules['request']:
            content.extend(sorted(rewrite_rules['request']))
        if rewrite_rules['response']:
            content.extend(sorted(rewrite_rules['response']))
        if rewrite_rules['reject']:
            content.extend(sorted(rewrite_rules['reject']))
        if rewrite_rules['other']:
            content.extend(sorted(rewrite_rules['other']))
        
        content.append("")
        
        # 添加MITM配置
        if rules['host']:
            content.extend([
                "[mitm]",
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
