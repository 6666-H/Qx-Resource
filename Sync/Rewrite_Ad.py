import os
import requests
import datetime
from datetime import timedelta
import git
from pathlib import Path
import logging
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from typing import Dict, Set, List

class Config:
    def __init__(self):
        self.REPO_PATH = "Rewrite"
        self.REWRITE_DIR = "Advertising"
        self.OUTPUT_FILE = "Ad.conf"
        self.README_PATH = "README_Rewrite.md"
        self.MAX_WORKERS = 10
        self.TIMEOUT = 30
        
        # 直接在代码中定义规则源
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
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('rewrite_update.log'),
                logging.StreamHandler()
            ]
        )

    def download_rule(self, name: str, url: str) -> tuple:
        """下载单个规则源"""
        try:
            response = requests.get(url, timeout=self.config.TIMEOUT)
            response.raise_for_status()
            content = response.text
            
            # 验证下载的内容
            if not content or len(content.strip()) == 0:
                logging.warning(f"Empty content downloaded from {url}")
                return name, None
                
            return name, content
        except requests.RequestException as e:
            logging.error(f"Error downloading {name} from {url}: {str(e)}")
            return name, None
        except Exception as e:
            logging.error(f"Unexpected error while downloading {name}: {str(e)}")
            return name, None
    
    def clean_rule(self, rule: str) -> str:
        """清理和标准化规则"""
        # 移除注释
        rule = re.sub(r'#.*$', '', rule)
        # 移除前后空白
        rule = rule.strip()
        # 标准化空格
        rule = re.sub(r'\s+', ' ', rule)
        return rule

    def normalize_hostname(self, hostname: str) -> str:
        """标准化主机名"""
        return hostname.lower().strip('.*')

    def is_valid_rule(self, rule: str) -> bool:
        """验证规则有效性"""
        if not rule or rule.startswith('#'):
            return False
        # 检查基本语法
        if rule.startswith('^') and ('url' in rule or 'hostname' in rule):
            return True
        # 检查脚本规则
        if '.js' in rule and ('script-response-body' in rule or 'script-request-body' in rule):
            return True
        return False

    def deduplicate_rules(self, rules: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
        """去除重复规则并根据优先级保留规则"""
        result = {
            'rewrite': set(),
            'mitm': set(),
            'host': set(),
            'script': set()
        }
        
        # 创建临时字典存储URL模式和对应的规则
        url_pattern_rules = {}
        
        # 定义reject类型的优先级
        reject_priority = {
            'reject-dict': 3,
            'reject-200': 2,
            'reject': 1
        }

        # 对重写规则进行去重和合并
        for rule in rules['rewrite']:
            normalized_rule = self.clean_rule(rule)
            if not self.is_valid_rule(normalized_rule):
                continue
                
            # 提取URL模式和reject类型
            pattern_match = re.match(r'^(.*?)\s+url\s+(reject(?:-dict|-200)?)', normalized_rule)
            if pattern_match:
                url_pattern = pattern_match.group(1)
                reject_type = pattern_match.group(2)
                
                # 如果URL模式已存在，比较优先级
                if url_pattern in url_pattern_rules:
                    existing_reject_type = re.search(r'reject(?:-dict|-200)?', url_pattern_rules[url_pattern]).group(0)
                    if reject_priority.get(reject_type, 0) > reject_priority.get(existing_reject_type, 0):
                        url_pattern_rules[url_pattern] = normalized_rule
                else:
                    url_pattern_rules[url_pattern] = normalized_rule
            else:
                result['rewrite'].add(normalized_rule)
        
        # 将处理后的规则添加到结果集
        result['rewrite'].update(url_pattern_rules.values())
        
        # 对主机名进行去重和标准化
        for host in rules['host']:
            normalized_host = self.normalize_hostname(host)
            if normalized_host:
                result['host'].add(normalized_host)
                
        # 对脚本规则进行去重
        result['script'] = set(rules['script'])
        
        return result

    def process_rules(self, content: str) -> Dict[str, Set[str]]:
        """处理规则内容"""
        rules = {
            'rewrite': set(),
            'mitm': set(),
            'host': set(),
            'script': set()
        }
        
        if not content:
            return rules
            
        for line in content.splitlines():
            line = self.clean_rule(line)
            if not line:
                continue
                
            # 处理主机名规则
            if 'hostname' in line.lower():
                self._process_hostname(line, rules)
            # 处理重写规则
            elif line.startswith('^'):
                rules['rewrite'].add(line)
            # 处理脚本规则
            elif '.js' in line:
                rules['script'].add(line)
                
        return rules

    def _process_hostname(self, line: str, rules: Dict[str, Set[str]]):
        """处理主机名规则"""
        if '=' in line:
            hostnames = line.split('=')[1].strip()
            hostnames = hostnames.replace('%APPEND%', '').strip()
            for hostname in hostnames.split(','):
                if hostname := self.normalize_hostname(hostname):
                    rules['host'].add(hostname)

    def merge_rules(self) -> Dict[str, Set[str]]:
        """合并所有规则"""
        logging.info("Starting rules merge...")
        
        merged_rules = {
            'rewrite': set(),
            'mitm': set(),
            'host': set(),
            'script': set()
        }
        
        with ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS) as executor:
            future_to_url = {
                executor.submit(self.download_rule, name, url): (name, url) 
                for name, url in self.config.REWRITE_SOURCES.items()
            }
            
            for future in as_completed(future_to_url):
                name, url = future_to_url[future]
                try:
                    _, content = future.result()
                    if content:
                        rules = self.process_rules(content)
                        # 合并规则
                        for key in merged_rules:
                            merged_rules[key].update(rules[key])
                except Exception as e:
                    logging.error(f"Error processing {name} ({url}): {str(e)}")
        
        # 去重和清理规则
        return self.deduplicate_rules(merged_rules)

    def generate_output(self, rules: Dict[str, Set[str]]) -> str:
        """生成最终的规则文件"""
        beijing_time = self.get_beijing_time()
        
        content = [self._generate_header(beijing_time)]
        
        # 添加重写规则
        if rules['rewrite']:
            content.append("\n[REWRITE]")
            content.extend(sorted(rules['rewrite']))
        
        # 添加主机名规则
        if rules['host']:
            content.append("\n[MITM]")
            content.append(f"hostname = {','.join(sorted(rules['host']))}")
        
        # 添加脚本规则
        if rules['script']:
            content.append("\n[SCRIPT]")
            content.extend(sorted(rules['script']))
        
        return '\n'.join(content)

    def _generate_header(self, time):
        """生成规则文件头部"""
        return f"""#!name = 自建重写规则合集
#!desc = 自建重写规则合集     
# 更新时间：{time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 合并自以下源：
{chr(10).join([f'# {name}: {url}' for name, url in self.config.REWRITE_SOURCES.items()])}
"""

    def get_beijing_time(self):
        """获取北京时间"""
        utc_now = datetime.datetime.utcnow()
        beijing_time = utc_now + timedelta(hours=8)
        return beijing_time

    def validate_output(self, content: str) -> bool:
        """验证输出内容的有效性"""
        required_sections = ['[REWRITE]', '[MITM]', '[SCRIPT]']
        for section in required_sections:
            if section not in content:
                logging.warning(f"Missing section: {section}")
                return False
        return True

    def update_readme(self, rules: Dict[str, Set[str]]):
        """更新 README 文件"""
        beijing_time = self.get_beijing_time()
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
        
        with open(os.path.join(self.config.REPO_PATH, self.config.README_PATH), 'w', encoding='utf-8') as f:
            f.write(content)

def main():
    config = Config()
    processor = RuleProcessor(config)
    
    try:
        # 创建输出目录
        Path(os.path.join(config.REPO_PATH, config.REWRITE_DIR)).mkdir(parents=True, exist_ok=True)
        
        # 合并规则
        rules = processor.merge_rules()
        
        # 生成输出文件
        output = processor.generate_output(rules)
        
        # 验证输出
        if not processor.validate_output(output):
            logging.error("Generated output validation failed")
            return
            
        # 写入文件
        output_path = os.path.join(config.REPO_PATH, config.REWRITE_DIR, config.OUTPUT_FILE)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
            
        # 更新 README
        processor.update_readme(rules)
        
        # Git 提交
        try:
            repo = git.Repo(config.REPO_PATH)
            repo.git.add(all=True)
            repo.index.commit(f"Update rewrite rules: {processor.get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
            origin = repo.remote(name='origin')
            origin.push()
            logging.info("Successfully pushed to repository")
        except Exception as e:
            logging.error(f"Error pushing to repository: {str(e)}")
            
    except Exception as e:
        logging.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main()
