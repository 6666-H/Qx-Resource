import os
import requests
import datetime
from datetime import timedelta
from pathlib import Path
import logging
from typing import Dict, Set, List, Tuple
import git

class RuleProcessor:
    """规则处理核心类"""
    
    def __init__(self):
        """初始化配置"""
        self.setup_config()
        self.setup_logging()
        self.rules_collection = {}
        self.metadata_collection = []  # 存储规则文件的元数据
        self.hostnames = set()
        
    def setup_config(self):
        """设置基础配置"""
        self.config = {
            'repo_path': "Rewrite",
            'rewrite_dir': "Advertising",
            'output_file': "Ad.conf",
            'readme_path': "README_Rewrite.md",
            'sources': {
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
        }

    def setup_logging(self):
        """配置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('rule_processor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def fetch_rule(self, name: str, url: str) -> str:
        """从URL获取规则内容"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            self.logger.info(f"Successfully downloaded rules from {name}")
            return response.text
        except Exception as e:
            self.logger.error(f"Failed to download rules from {name}: {e}")
            return ""

def parse_section(self, content: str) -> Tuple[Dict[str, Set[str]], Dict[str, str]]:
    """解析规则内容"""
    sections = {}
    current_section = None
    metadata = {}
    in_comment_block = False
    
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 处理多行注释
        if line.startswith('/*'):
            in_comment_block = True
            i += 1
            continue
        elif line.endswith('*/'):
            in_comment_block = False
            i += 1
            continue
        elif in_comment_block:
            i += 1
            continue
            
        # 跳过空行和单行注释
        if not line or line.startswith('//') or line.startswith('#'):
            i += 1
            continue
            
        # 处理重写规则部分
        if line.startswith('[rewrite_local]'):
            current_section = 'Script'
            if current_section not in sections:
                sections[current_section] = set()
            i += 1
            continue
            
        # 处理mitm部分
        if line.startswith('[mitm]'):
            current_section = 'MITM'
            if current_section not in sections:
                sections[current_section] = set()
            i += 1
            continue
            
        # 处理hostname
        if line.startswith('hostname'):
            if 'MITM' not in sections:
                sections['MITM'] = set()
            sections['MITM'].add(line)
            i += 1
            continue
            
        # 将内容添加到当前section
        if current_section and line:
            if current_section == 'Script':
                # 处理重写规则
                parts = line.split('script-path=')
                if len(parts) > 1:
                    pattern = parts[0].split(None, 1)[0]
                    script_config = parts[1].split(',')
                    script_path = script_config[0]
                    
                    # 提取额外参数
                    extra_params = []
                    for param in script_config[1:]:
                        param = param.strip()
                        if param:
                            extra_params.append(param)
                    
                    script_line = f"{pattern} = type=http-request,script-path={script_path}"
                    
                    # 添加额外参数
                    if extra_params:
                        script_line += f",{','.join(extra_params)}"
                        
                    sections[current_section].add(script_line)
            else:
                sections[current_section].add(line)
        
        i += 1
    
    return sections, metadata


    def generate_header(self) -> str:
        """生成规则文件头部信息"""
        beijing_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
        return f"""#!name = 自建重写规则合集
#!desc = 整合多个去广告规则
# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

"""

    def update_readme(self, stats: Dict[str, int]):
        """更新README文件"""
        beijing_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
        readme_content = f"""# 自建重写规则合集

## 规则说明
本规则集合并自各个开源规则，经过整理和去重。

## 规则统计
- 总规则数：{stats['total']}
- hostname数：{len(self.hostnames)}
{chr(10).join([f'- {section}规则数：{count}' for section, count in stats.items() if section not in ['total', 'hostnames']])}

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 规则来源
{chr(10).join([f'- {name}: {url}' for name, url in self.config['sources'].items()])}
"""
        
        readme_path = os.path.join(self.config['repo_path'], self.config['readme_path'])
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

    def git_push(self):
        """提交更改到Git仓库"""
        try:
            repo = git.Repo(self.config['repo_path'])
            repo.git.add(all=True)
            beijing_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
            commit_message = f"Update rules: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)"
            repo.index.commit(commit_message)
            origin = repo.remote(name='origin')
            origin.push()
            self.logger.info("Successfully pushed to repository")
        except Exception as e:
            self.logger.error(f"Failed to push to repository: {e}")

    def process(self):
        """主处理流程"""
        # 创建输出目录
        Path(os.path.join(self.config['repo_path'], self.config['rewrite_dir'])).mkdir(parents=True, exist_ok=True)
        
        # 处理每个规则源
        for name, url in self.config['sources'].items():
            content = self.fetch_rule(name, url)
            if content:
                sections, metadata = self.parse_section(content)
                if metadata:
                    self.metadata_collection.append(metadata)
                self.rules_collection[name] = sections
        
        # 合并规则并获取统计信息
        merged_content, stats = self.merge_rules()
        
        # 写入合并后的规则文件
        output_path = os.path.join(self.config['repo_path'], self.config['rewrite_dir'], self.config['output_file'])
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(merged_content)
            
        # 更新README
        self.update_readme(stats)
        
        # 提交到Git
        self.git_push()
        
        return stats

def main():
    processor = RuleProcessor()
    stats = processor.process()
    print(f"Processing completed. Total rules: {stats['total']}")

if __name__ == "__main__":
    main()
