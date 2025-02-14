import os
import re
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
            "网易云音乐去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E7%BD%91%E6%98%93%E4%BA%91%E9%9F%B3%E4%B9%90%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule"
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
            binary_body_mode = False
            
            # 解析参数
            params = content.split(',')
            for param in params:
                param = param.strip()
                if 'type=' in param:
                    rule_type = param.split('=')[1]
                elif 'pattern=' in param:
                    pattern = param.split('=')[1]
                elif 'script-path=' in param:
                    script_path = param.split('=')[1]
                elif 'requires-body=' in param:
                    requires_body = param.split('=')[1].lower() == 'true'
                elif 'binary-body-mode=' in param:
                    binary_body_mode = param.split('=')[1].lower() == 'true'
            
            # 如果缺少必要参数，返回原始行
            if not all([rule_type, pattern, script_path]):
                return line
                
            # 转换规则类型
            if rule_type == 'http-response':
                qx_type = 'script-response-body' if requires_body else 'script-response-header'
            elif rule_type == 'http-request':
                qx_type = 'script-request-body' if requires_body else 'script-request-header'
            else:
                return line
                
            # 构建 QuantumultX 格式的规则
            converted_rule = f"{pattern} url {qx_type} {script_path}"
            
            # 如果有binary-body-mode参数，添加到规则末尾
            if binary_body_mode:
                converted_rule += ", requires-body=true, binary-body-mode=true"
                
            return converted_rule
            
        except Exception as e:
            print(f"Error converting rule: {line}")
            print(f"Error details: {str(e)}")
            return line

    def _normalize_url_pattern(self, url: str) -> str:
        """标准化URL模式，便于比较"""
        try:
            # 获取URL部分（去除reject等后缀）
            url = url.split()[0] if ' ' in url else url
            
            # 移除 ^ 和 $ 符号
            url = url.strip('^$')
            
            # 将 https?:\/\/ 统一处理
            url = url.replace('https?://', '').replace('http?://', '')
            
            # 移除转义符
            url = url.replace('\\', '')
            
            # 处理尾部斜杠
            url = url.rstrip('/')  # 移除所有尾部斜杠
            
            # 处理版本号通配符
            url = url.replace('/v\\d', '/v*')
            
            return url
        except:
            return url

    def _is_url_pattern_covered(self, url1: str, url2: str) -> bool:
        """检查url1是否被url2覆盖"""
        try:
            # 获取标准化的URL
            pattern1 = self._normalize_url_pattern(url1)
            pattern2 = self._normalize_url_pattern(url2)
            
            # 如果完全相同，返回False（在其他地方处理）
            if pattern1 == pattern2:
                return False
                
            # 特殊处理尾部可选参数
            if pattern1.rstrip('?') == pattern2.rstrip('?'):
                return True
                
            # 处理括号中的多选项
            if '(' in pattern2:
                base_pattern2 = pattern2[:pattern2.find('(')]
                options = pattern2[pattern2.find('(')+1:pattern2.find(')')].split('|')
                for option in options:
                    full_pattern = base_pattern2 + option
                    if pattern1 == full_pattern:
                        return True
                        
            # 将模式转换为正则表达式格式
            pattern1 = pattern1.replace('*', '[^/]+').replace('?', '.?')
            pattern2 = pattern2.replace('*', '[^/]+').replace('?', '.?')
            
            # 检查包含关系
            return bool(re.match(f"^{pattern2}$", pattern1))
        except:
            return False

    def _get_rule_type(self, rule: str) -> tuple:
        """获取规则的类型和类别"""
        # 检查reject类规则
        for rule_type in self.REJECT_PRIORITY.keys():
            if f" {rule_type}" in rule:
                return ('reject', rule_type)
                
        # 检查script类规则
        for script_type in self.SCRIPT_TYPES:
            if script_type in rule:
                return ('script', script_type)
                
        return ('other', 'other')

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

    def _sort_rules(self, rules: Set[str]) -> List[str]:
        """根据优先级对规则进行排序"""
        reject_rules = []
        script_rules = []
        other_rules = []
        
        # 将规则分类并预处理
        url_rules_map = {}  # 用于存储相同URL的不同规则
        
        for rule in rules:
            category, rule_type = self._get_rule_type(rule)
            
            # 获取URL部分
            url = rule.split()[0]
            normalized_url = self._normalize_url_pattern(url)
            
            # 将规则按照标准化后的URL分组
            if normalized_url not in url_rules_map:
                url_rules_map[normalized_url] = []
            url_rules_map[normalized_url].append((category, rule_type, rule))
        
        # 处理每组相同URL的规则
        for normalized_url, url_rules in url_rules_map.items():
            # 分离不同类型的规则
            reject_group = [(rt, r) for c, rt, r in url_rules if c == 'reject']
            script_group = [(rt, r) for c, rt, r in url_rules if c == 'script']
            other_group = [r for c, rt, r in url_rules if c == 'other']
            
            # 对于reject规则，保留优先级最高的
            if reject_group:
                best_reject = min(reject_group, key=lambda x: self.REJECT_PRIORITY[x[0]])
                reject_rules.append(best_reject)
                
            # 对于script规则，保留每种类型的第一个
            if script_group:
                seen_types = set()
                for rule_type, rule in script_group:
                    if rule_type not in seen_types:
                        script_rules.append((rule_type, rule))
                        seen_types.add(rule_type)
                        
            # 其他规则直接添加
            other_rules.extend(other_group)
        
        # 最终排序
        final_reject_rules = [rule for _, rule in sorted(reject_rules, key=lambda x: (x[1].split()[0], self.REJECT_PRIORITY[x[0]]))]
        final_script_rules = [rule for _, rule in sorted(script_rules, key=lambda x: (x[1].split()[0], x[0]))]
        final_other_rules = sorted(other_rules)
        
        return final_reject_rules + final_script_rules + final_other_rules

    def process_rules(self, content: str) -> Dict[str, Set[str]]:
        """处理规则内容"""
        rules = {'url-rewrite': set()}
        
        if not content:
            return rules
            
        current_section = 'url-rewrite'
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue
                
            # 检查是否是标签行
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1].lower()
                if current_section not in rules:
                    rules[current_section] = set()
                continue
                
            # 特殊处理 hostname
            if 'hostname' in line.lower():
                if 'host' not in rules:
                    rules['host'] = set()
                self._process_hostname(line, rules)
                continue
            
            # 检查是否是 Surge 格式的规则并转换
            if ' = type=' in line:
                line = self._convert_surge_rule(line)
            
            # 将规则添加到当前标签下
            if current_section and line:
                rules[current_section].add(line)
                    
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
        
        for section, rules_set in rules.items():
            if rules_set:
                if section == 'host':
                    content.extend([
                        "[MITM]",
                        f"hostname = {self.deduplicate_hostnames(rules_set)}",
                        ""
                    ])
                else:
                    section_name = section.upper()
                    content.extend([
                        f"[{section_name}]",
                        *self._sort_rules(rules_set),
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
