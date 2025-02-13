import os
import requests
import datetime
from datetime import timedelta
import git
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置类
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
            "whatshubs开屏屏蔽": "https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/manual/rewrite/adultraplus.conf",
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

# 规则处理类
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
    
    def clean_rule(self, rule):
        """清理和标准化规则"""
        rule = rule.strip()
        if '#' in rule:
            rule = rule.split('#')[0].strip()
        return rule
    
    def is_valid_rule(self, rule):
        """验证规则有效性"""
        return bool(rule and not rule.startswith('#'))

    def download_rule(self, name, url):
        """下载单个规则源"""
        try:
            response = requests.get(url, timeout=self.config.TIMEOUT)
            response.raise_for_status()
            return name, response.text
        except Exception as e:
            logging.error(f"Error downloading {name}: {str(e)}")
            return name, None

    def process_rules(self, content):
        """处理规则内容"""
        rules = {
            'rewrite': set(),
            'mitm': set(),
            'host': set(),
            'script': []
        }
        
        if not content:
            return rules
            
        for line in content.splitlines():
            line = self.clean_rule(line)
            if not self.is_valid_rule(line):
                continue
                
            if 'hostname' in line.lower():
                self._process_hostname(line, rules)
            elif line.startswith('^'):
                rules['rewrite'].add(line)
            elif line.endswith('.js'):
                rules['script'].append(line)
                
        return rules

    def _process_hostname(self, line, rules):
        """处理 hostname 规则"""
        if '=' in line:
            hostnames = line.split('=')[1].strip()
            hostnames = hostnames.replace('%APPEND%', '').strip()
            rules['host'].update(h.strip() for h in hostnames.split(',') if h.strip())

    def merge_rules(self):
        """合并所有规则"""
        logging.info("Starting rules merge...")
        
        merged_rules = {
            'rewrite': set(),
            'mitm': set(),
            'host': set(),
            'script': []
        }
        
        # 并发下载规则
        with ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS) as executor:
            future_to_url = {
                executor.submit(self.download_rule, name, url): name 
                for name, url in self.config.REWRITE_SOURCES.items()
            }
            
            for future in concurrent.futures.as_completed(future_to_url):
                name = future_to_url[future]
                try:
                    name, content = future.result()
                    if content:
                        rules = self.process_rules(content)
                        # 合并规则
                        merged_rules['rewrite'].update(rules['rewrite'])
                        merged_rules['host'].update(rules['host'])
                        merged_rules['script'].extend(rules['script'])
                except Exception as e:
                    logging.error(f"Error processing {name}: {str(e)}")
                    
        return merged_rules

    def generate_output(self, rules):
        """生成最终的规则文件"""
        beijing_time = self.get_beijing_time()
        
        # 生成文件头
        header = self._generate_header(beijing_time)
        
        # 组合规则内容
        content = []
        content.append(header)
        
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

    def update_readme(self, rules):
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
    # 初始化配置
    config = Config()
    
    # 创建规则处理器
    processor = RuleProcessor(config)
    
    try:
        # 创建输出目录
        Path(os.path.join(config.REPO_PATH, config.REWRITE_DIR)).mkdir(parents=True, exist_ok=True)
        
        # 合并规则
        rules = processor.merge_rules()
        
        # 生成输出文件
        output = processor.generate_output(rules)
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
