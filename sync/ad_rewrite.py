import os
import re
import requests
import datetime
from datetime import timedelta
import git
from pathlib import Path
import time
from collections import defaultdict
import logging

# 设置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 规则源列表
REWRITE_SOURCES = {
    "阻止常见的 HTTPDNS 服务器": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/%E6%8B%A6%E6%88%AAHTTPDNS.official.sgmodule",
    "广告平台拦截器": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%B9%BF%E5%91%8A%E5%B9%B3%E5%8F%B0%E6%8B%A6%E6%88%AA%E5%99%A8.sgmodule",
    "whatshubs开屏屏蔽": "https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/manual/rewrite/adultraplus.conf",
    "whatshub微信屏蔽": "https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/manual/rewrite/wechatad.conf",
    "whatshubAdBlock":"https://raw.githubusercontent.com/deezertidal/QuantumultX-Rewrite/refs/heads/master/rewrite/AdBlock.conf",
    "surge去广告":"https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/%E6%96%B0%E6%89%8B%E5%8F%8B%E5%A5%BD%E3%81%AE%E5%8E%BB%E5%B9%BF%E5%91%8A%E9%9B%86%E5%90%88.official.sgmodule",
    "chxm去广告": "https://raw.githubusercontent.com/chxm1023/Advertising/main/AppAd.conf",
    "墨鱼微信广告": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/Applet.conf",
    "墨鱼去开屏V2.0": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/StartUp.conf",
    "广告拦截精简版": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/QuantumultX/AdvertisingLite/AdvertisingLite.conf",
    "去广告重写": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/chongxie.txt",
    "整合广告拦截": "https://raw.githubusercontent.com/weiyesing/QuantumultX/GenMuLu/ChongXieGuiZe/QuGuangGao/To%20advertise.conf",
    "YouTube去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/Youtube%20%E5%8E%BB%E5%B9%BF%E5%91%8A%20(%E4%B8%8D%E5%8E%BB%E8%B4%B4%E7%89%87).official.sgmodule",
    "YouTube双语翻译": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Beta/YouTube%E7%BF%BB%E8%AF%91.beta.sgmodule",
    "可莉广告过滤器": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%8F%AF%E8%8E%89%E5%B9%BF%E5%91%8A%E8%BF%87%E6%BB%A4%E5%99%A8.sgmodule",
    "小红书去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%B0%8F%E7%BA%A2%E4%B9%A6%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "微博去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%BE%AE%E5%8D%9A%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "小黑盒去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%B0%8F%E9%BB%91%E7%9B%92%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "微信小程序去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%BE%AE%E4%BF%A1%E5%B0%8F%E7%A8%8B%E5%BA%8F%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "百度网页去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E7%99%BE%E5%BA%A6%E6%90%9C%E7%B4%A2%E7%BD%91%E9%A1%B5%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "网易云音乐去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E7%BD%91%E6%98%93%E4%BA%91%E9%9F%B3%E4%B9%90%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "拼多多去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E6%8B%BC%E5%A4%9A%E5%A4%9A%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "Google搜索重定向": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Google%E9%87%8D%E5%AE%9A%E5%90%91.sgmodule",
    "京东比价": "https://raw.githubusercontent.com/mw418/Loon/main/script/jd_price.js",
    "汤头条解锁": "https://raw.githubusercontent.com/Yu9191/Rewrite/main/lsp/Tangtoutiao.js",
    "1998解锁": "https://raw.githubusercontent.com/Yu9191/Rewrite/main/1998.js"
}

class RuleProcessor:
    def __init__(self):
        self.REPO_PATH = "ad"
        self.REWRITE_DIR = "rewrite"
        self.OUTPUT_FILE = "ad_rewrite.conf"
        self.README_PATH = "README-rewrite.md"
        self.RETRY_COUNT = 3
        self.TIMEOUT = 30
        
        self.setup_directory()

    def setup_directory(self):
        """设置必要的目录结构"""
        Path(os.path.join(self.REPO_PATH, self.REWRITE_DIR)).mkdir(parents=True, exist_ok=True)

    def get_beijing_time(self):
        """获取北京时间"""
        return datetime.datetime.utcnow() + timedelta(hours=8)

    def analyze_rule_source(self, name, content):
        """分析规则源的格式和有效性"""
        logger.info(f"\nAnalyzing {name}...")
        
        total_rules = 0
        valid_rules = 0
        sections = set()
        
        try:
            lines = content.splitlines()
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                total_rules += 1
                
                # 检测段落标记
                if line.startswith('['):
                    section = line.strip('[]').upper()
                    sections.add(section)
                    continue
                
                # 验证规则转换
                converted = self.convert_surge_to_quanx(line)
                if converted and self.is_valid_rule(converted):
                    valid_rules += 1
                    
            # 输出分析结果
            logger.info(f"Source: {name}")
            logger.info(f"Total rules: {total_rules}")
            logger.info(f"Valid rules: {valid_rules}")
            logger.info(f"Sections found: {', '.join(sections)}")
            if total_rules > 0:
                logger.info(f"Conversion rate: {valid_rules/total_rules*100:.1f}%")
            
            return valid_rules > 0
            
        except Exception as e:
            logger.error(f"Error analyzing {name}: {str(e)}")
            return False

    def download_rules(self, name, url):
        """下载规则内容"""
        for attempt in range(self.RETRY_COUNT):
            try:
                logger.info(f"Downloading rules from {name}... (Attempt {attempt + 1})")
                response = requests.get(url, timeout=self.TIMEOUT)
                response.raise_for_status()
                content = response.text
                logger.debug(f"Downloaded content for {name} (first 500 chars):\n{content[:500]}")
                return content
            except Exception as e:
                if attempt == self.RETRY_COUNT - 1:
                    logger.error(f"Failed to download {name} after {self.RETRY_COUNT} attempts: {str(e)}")
                    return None
                logger.warning(f"Retry after error: {str(e)}")
                time.sleep(2)
        return None

    def test_rule(self, rule):
        """测试单个规则的有效性"""
        try:
            # 基本语法检查
            if not rule or rule.startswith('#'):
                return False
                
            # 检查URL格式
            if 'url' in rule:
                url_pattern = re.search(r'https?://([^/]+)', rule)
                if not url_pattern:
                    return False
                    
            # 检查动作有效性
            valid_actions = ['reject', 'reject-200', 'reject-img', 'reject-dict', 
                           'reject-array', 'script-response-body', 'script-request-body']
            has_valid_action = any(action in rule for action in valid_actions)
            if not has_valid_action:
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error testing rule {rule}: {str(e)}")
            return False

    def convert_surge_to_quanx(self, line):
        """转换 Surge 规则到 QuantumultX 格式"""
        if not line or line.startswith('#'):
            return line

        try:
            # 保存原始行用于调试
            original_line = line
            line = line.replace('\t', ' ').strip()
            
            # Surge URL 重写格式
            if ' url ' in line:
                parts = line.split(' url ')
                if len(parts) == 2:
                    pattern = parts[0].strip()
                    action = parts[1].strip()
                    
                    # 确保pattern是有效的URL格式
                    if not pattern.startswith(('http://', 'https://')):
                        pattern = f"https?://{pattern}"
                        
                    return f'url {action} {pattern}'

            # Surge 规则格式
            if line.startswith('URL-REGEX'):
                pattern = re.search(r'URL-REGEX,([^,]+)', line)
                if pattern:
                    return f'url reject {pattern.group(1)}'

            # DOMAIN 规则
            if line.startswith('DOMAIN'):
                parts = line.split(',')
                if len(parts) >= 2:
                    return f'host,{parts[1].strip()},reject'

            # 脚本规则
            if 'script-path' in line:
                pattern = re.search(r'pattern=([^,]+).*script-path=([^,\s]+)', line)
                if pattern:
                    url, script = pattern.groups()
                    return f'url script-response-body {url.strip()} {script.strip()}'

            # Map Local 规则
            if 'data=' in line or 'data-type=' in line:
                url = line.split()[0]
                return f'url reject-dict {url}'

            # 如果转换失败,记录日志
            logger.warning(f"Failed to convert rule: {original_line}")
            return None

        except Exception as e:
            logger.error(f"Error converting rule: {line}")
            logger.error(f"Error details: {str(e)}")
            return None

    def is_valid_rule(self, rule):
        """验证规则的有效性"""
        if not rule or rule.startswith('#'):
            return False
            
        # 验证基本格式
        try:
            if 'url' in rule:
                parts = rule.split()
                if len(parts) < 3:  # url action pattern [script]
                    return False
                    
                # 验证动作
                valid_actions = ['reject', 'reject-200', 'reject-img', 'reject-dict',
                               'reject-array', 'script-response-body', 'script-request-body']
                if not any(action in rule for action in valid_actions):
                    return False
                    
            elif rule.startswith('host'):
                parts = rule.split(',')
                if len(parts) != 3:  # host,domain,action
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error validating rule {rule}: {str(e)}")
            return False

    def parse_rules(self, content):
        """解析规则内容"""
        rules = set()
        hostnames = set()
        js_methods = set()
        rule_types = set()
        
        if not content:
            return rules, hostnames, js_methods, rule_types

        current_section = None
        section_pattern = r'^\[(.*?)\]'
        
        for line in content.splitlines():
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue

            # 检测段落标记
            section_match = re.match(section_pattern, line)
            if section_match:
                current_section = section_match.group(1).upper()
                rule_types.add(current_section)
                continue

            # 转换和验证规则
            converted_rule = self.convert_surge_to_quanx(line)
            if converted_rule and self.is_valid_rule(converted_rule):
                rules.add(converted_rule)
                
                # 提取域名
                if 'url' in converted_rule:
                    domain_match = re.search(r'https?://([^/]+)', converted_rule)
                    if domain_match:
                        domain = domain_match.group(1).split(':')[0]
                        if '.' in domain:
                            hostnames.add(domain)

                elif converted_rule.startswith('host'):
                    parts = converted_rule.split(',')
                    if len(parts) >= 2:
                        hostnames.add(parts[1].strip())

            # 收集脚本内容
            if current_section == 'SCRIPT' and 'script-path' in line:
                js_methods.add(line)

        return rules, hostnames, js_methods, rule_types

    def generate_output(self, rules, hostnames, js_methods, rule_types):
        """生成输出内容"""
        header = f"""# 广告拦截重写规则合集
# 更新时间：{self.get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 规则数量：{len(rules)}
# Hostname数量：{len(hostnames)}
# JavaScript方法数量：{len(js_methods)}

"""
        content = header

        # 按规则类型分组
        rule_groups = defaultdict(list)
        
        # 智能分类规则
        for rule in sorted(rules):
            if 'script' in rule:
                rule_groups['SCRIPT'].append(rule)
            elif 'reject-dict' in rule or 'reject-array' in rule:
                rule_groups['MAP LOCAL'].append(rule)
            elif 'url reject' in rule:
                rule_groups['URL REWRITE'].append(rule)
            elif rule.startswith('host'):
                rule_groups['RULE'].append(rule)

        # 生成输出内容
        for group_name in ['SCRIPT', 'MAP LOCAL', 'URL REWRITE', 'RULE']:
            group_rules = rule_groups.get(group_name, [])
            if group_rules:
                content += f"[{group_name}]\n"
                content += '\n'.join(sorted(group_rules))
                content += '\n\n'

        # 添加Hostname
        if hostnames:
            content += "[MITM]\n"
            content += f"hostname = {', '.join(sorted(hostnames))}"

        return content

    def validate_source(self, name, url):
        """验证规则源的有效性"""
        content = self.download_rules(name, url)
        if not content:
            logger.error(f"Failed to download {name}")
            return False
            
        # 分析规则源
        is_valid = self.analyze_rule_source(name, content)
        if not is_valid:
            logger.error(f"Invalid rule source: {name}")
            return False
            
        return content

    def run(self):
        """主要运行逻辑"""
        all_rules = set()
        all_hostnames = set()
        all_js_methods = set()
        all_rule_types = set()

        # 处理每个规则源
        for name, url in REWRITE_SOURCES.items():
            content = self.validate_source(name, url)
            if content:
                rules, hostnames, js_methods, rule_types = self.parse_rules(content)
                
                # 验证规则
                valid_rules = {rule for rule in rules if self.test_rule(rule)}
                if len(valid_rules) < len(rules):
                    logger.warning(f"Removed {len(rules) - len(valid_rules)} invalid rules from {name}")
                
                all_rules.update(valid_rules)
                all_hostnames.update(hostnames)
                all_js_methods.update(js_methods)
                all_rule_types.update(rule_types)
            else:
                logger.error(f"Skipping invalid source: {name}")

        # 生成输出
        output = self.generate_output(all_rules, all_hostnames, all_js_methods, all_rule_types)
        output_path = os.path.join(self.REPO_PATH, self.REWRITE_DIR, self.OUTPUT_FILE)
        
        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
            
        logger.info(f"Successfully generated rules file: {output_path}")
        logger.info(f"Total rules: {len(all_rules)}")
        logger.info(f"Total hostnames: {len(all_hostnames)}")
        logger.info(f"Total js methods: {len(all_js_methods)}")

if __name__ == "__main__":
    processor = RuleProcessor()
    processor.run()
