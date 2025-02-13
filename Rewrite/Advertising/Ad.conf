import os
import requests
import datetime
import re
from datetime import timedelta
from typing import Dict, Set, List
from concurrent.futures import ThreadPoolExecutor

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

class RuleType:
    """规则类型枚举"""
    GENERAL = 'general'
    RULE = 'rule'
    REWRITE = 'rewrite'
    URL_REWRITE = 'url_rewrite'
    HEADER_REWRITE = 'header_rewrite'
    SCRIPT = 'script'
    HOST = 'host'
    MITM = 'mitm'
    PANEL = 'panel'
    MAP_LOCAL = 'map_local'
    URL_REGEX = 'url_regex'
    DOMAIN_SUFFIX = 'domain_suffix'
    IP_CIDR = 'ip_cidr'
    SSID_SETTING = 'ssid_setting'
    FILTER = 'filter'
    DNS = 'dns'
    POLICY = 'policy'

class Rule:
    """规则对象"""
    def __init__(self, content: str, rule_type: str, enabled: bool = True):
        self.content = content.strip()
        self.type = rule_type
        self.enabled = enabled
        self.priority = self._get_priority()

    def _get_priority(self) -> int:
        """获取规则优先级"""
        priorities = {
            RuleType.GENERAL: 100,
            RuleType.MITM: 90,
            RuleType.SCRIPT: 80,
            RuleType.REWRITE: 70,
            RuleType.RULE: 60,
        }
        return priorities.get(self.type, 0)

    def __eq__(self, other):
        return self.content == other.content and self.type == other.type

    def __hash__(self):
        return hash((self.content, self.type))

class RuleProcessor:
    def __init__(self, config: Config):
        self.config = config
        self.rules: Dict[str, Set[Rule]] = {
            RuleType.GENERAL: set(),
            RuleType.RULE: set(),
            RuleType.REWRITE: set(),
            RuleType.URL_REWRITE: set(),
            RuleType.HEADER_REWRITE: set(),
            RuleType.SCRIPT: set(),
            RuleType.HOST: set(),
            RuleType.MITM: set(),
            RuleType.PANEL: set(),
            RuleType.MAP_LOCAL: set(),
            RuleType.URL_REGEX: set(),
            RuleType.DOMAIN_SUFFIX: set(),
            RuleType.IP_CIDR: set(),
            RuleType.SSID_SETTING: set(),
            RuleType.FILTER: set(),
            RuleType.DNS: set(),
            RuleType.POLICY: set(),
        }

    def download_rule(self, name: str, url: str) -> tuple:
        """下载规则源"""
        try:
            response = requests.get(url, timeout=self.config.TIMEOUT)
            response.raise_for_status()
            return name, response.text
        except Exception as e:
            print(f"Error downloading {name}: {e}")
            return name, None

    def identify_rule_type(self, line: str) -> str:
        """识别规则类型"""
        line = line.strip().lower()
        
        # 忽略注释和空行
        if not line or line.startswith('#') or line.startswith('//'):
            return None
            
        # 忽略 JSON 格式的内容
        if (line.startswith('{') or line.startswith('[') or 
            line.startswith('"') or line.startswith("'")):
            return None
            
        # 忽略函数定义和变量声明
        if (line.startswith('function') or line.startswith('var') or 
            line.startswith('let') or line.startswith('const')):
            return None
        
        # 识别特定的规则头部
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1].lower()
            if section in ['general', 'rule', 'rewrite', 'script', 'mitm', 'panel']:
                return section
                
        # 识别具体的规则类型
        if 'hostname' in line:
            return RuleType.MITM
        elif 'domain-suffix' in line:
            return RuleType.DOMAIN_SUFFIX
        elif 'ip-cidr' in line:
            return RuleType.IP_CIDR
        elif 'url-regex' in line:
            return RuleType.URL_REGEX
        elif line.startswith('^https?://'):
            return RuleType.REWRITE
        elif '.js' in line and ('url script-' in line or 'requires-body=1' in line):
            return RuleType.SCRIPT
            
        # 如果不符合任何规则格式，返回 None
        return None

    def process_rule(self, line: str):
        """处理单条规则"""
        line = line.strip()
        if not line:
            return
            
        rule_type = self.identify_rule_type(line)
        if rule_type:  # 只添加识别出类型的规则
            rule = Rule(line, rule_type)
            self.rules[rule_type].add(rule)

    def process_rules(self, content: str):
        """处理规则内容"""
        if not content:
            return

        current_section = None
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line.startswith('[') and line.endswith(']'):
                current_section = line.lower()[1:-1]
                continue

            self.process_rule(line)

    def merge_rules(self):
        """合并所有规则"""
        with ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS) as executor:
            future_to_url = {
                executor.submit(self.download_rule, name, url): name 
                for name, url in self.config.REWRITE_SOURCES.items()
            }
            
            for future in future_to_url:
                name = future_to_url[future]
                try:
                    _, content = future.result()
                    if content:
                        self.process_rules(content)
                except Exception as e:
                    print(f"Error processing {name}: {e}")

    def generate_output(self) -> str:
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

        # 按优先级排序并添加各类型规则
        for rule_type, rules in self.rules.items():
            if rules:
                sorted_rules = sorted(rules, key=lambda x: (-x.priority, x.content))
                content.extend([
                    f"[{rule_type.upper()}]",
                    *[rule.content for rule in sorted_rules],
                    ""
                ])

        return '\n'.join(content)

    def update_readme(self):
        """更新README文件"""
        beijing_time = datetime.datetime.utcnow() + timedelta(hours=8)
        
        total_rules = sum(len(rules) for rules in self.rules.values())
        
        content = f"""# 自建重写规则合集

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 规则统计
总规则数：{total_rules}
"""

        # 添加各类型规则统计
        for rule_type, rules in self.rules.items():
            if rules:
                content += f"- {rule_type}: {len(rules)}条规则\n"

        content += "\n## 规则来源\n"
        content += '\n'.join([f'- {name}: {url}' for name, url in self.config.REWRITE_SOURCES.items()])

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
        processor.merge_rules()
        
        # 生成输出文件
        output = processor.generate_output()
        
        # 写入文件
        output_path = os.path.join(config.REPO_PATH, config.REWRITE_DIR, config.OUTPUT_FILE)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
            
        # 更新 README
        processor.update_readme()
        
        print("Successfully generated rules and README")
        
    except Exception as e:
        print(f"Error in main process: {e}")
        raise

if __name__ == "__main__":
    main()
