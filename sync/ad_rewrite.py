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

    def download_rules(self, name, url):
        """下载规则内容"""
        for attempt in range(self.RETRY_COUNT):
            try:
                logger.info(f"Downloading rules from {name}... (Attempt {attempt + 1})")
                response = requests.get(url, timeout=self.TIMEOUT)
                response.raise_for_status()
                return response.text
            except Exception as e:
                if attempt == self.RETRY_COUNT - 1:
                    logger.error(f"Failed to download {name}: {str(e)}")
                    return None
                time.sleep(2)
        return None

    def parse_rules(self, content):
        """解析规则内容"""
        rules = set()
        hostnames = set()
        scripts = {}  # 存储脚本信息
        current_section = None
        
        if not content:
            return rules, hostnames, scripts

        lines = content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line or line.startswith('#'):
                i += 1
                continue

            # 检测段落标记
            if line.startswith('['):
                current_section = line.strip('[]').upper()
                i += 1
                continue

            # 处理脚本部分
            if current_section == 'SCRIPT':
                script_info = self.parse_script_section(lines[i:])
                if script_info:
                    name, pattern, script = script_info
                    scripts[name] = {
                        'pattern': pattern,
                        'script': script
                    }
                    i += 3  # 跳过已处理的脚本行
                else:
                    i += 1
                continue

            # 转换和验证规则
            converted_rule = self.convert_surge_to_quanx(line)
            if converted_rule and self.is_valid_rule(converted_rule):
                rules.add(converted_rule)
                
                # 提取 hostname
                url_pattern = re.search(r'https?://([^/]+)', converted_rule)
                if url_pattern:
                    domain = url_pattern.group(1).split(':')[0]
                    if '.' in domain:
                        hostnames.add(domain)

            i += 1

        return rules, hostnames, scripts

    def parse_script_section(self, lines):
        """解析脚本部分"""
        try:
            # 获取前三行
            if len(lines) < 3:
                return None
                
            name_line = lines[0].strip()
            pattern_line = lines[1].strip()
            script_line = lines[2].strip()
            
            # 提取脚本名称
            if name_line.startswith('#'):
                name = name_line[1:].strip()
            else:
                return None
                
            # 提取匹配模式
            pattern_match = re.search(r'^(http[^\s]+)', pattern_line)
            if not pattern_match:
                return None
            pattern = pattern_match.group(1)
            
            # 提取脚本URL
            script_match = re.search(r'script-path\s*=\s*([^\s,]+)', script_line)
            if not script_match:
                return None
            script = script_match.group(1)
            
            return name, pattern, script
            
        except Exception as e:
            logger.error(f"Error parsing script section: {str(e)}")
            return None

    def convert_surge_to_quanx(self, line):
        """转换规则到 QuantumultX 格式"""
        if not line or line.startswith('#'):
            return line

        try:
            line = line.replace('\t', ' ').strip()
            
            # 处理已经是 QX 格式的规则
            if ' url ' in line:
                return line

            # 处理 Surge 脚本
            if 'type=http-response' in line or 'type=http-request' in line:
                pattern = re.search(r'pattern=([^,]+).*script-path=([^,\s]+)', line)
                if pattern:
                    url, script = pattern.groups()
                    requires_body = 'requires-body=true' in line
                    script_type = 'response' if 'http-response' in line else 'request'
                    body_type = '-body' if requires_body else ''
                    return f'{url.strip()} url script-{script_type}{body_type} {script.strip()}'

            # 处理 URL-REGEX
            if 'URL-REGEX' in line:
                pattern = re.search(r'URL-REGEX,([^,]+)', line)
                if pattern:
                    url = pattern.group(1).strip()
                    if not url.startswith('^'):
                        url = '^' + url
                    return f'{url} url reject-200'

            # 处理重定向
            if '302' in line or '307' in line:
                pattern = r'([^\s]+)\s+30[27]\s+([^\s]+)'
                match = re.search(pattern, line)
                if match:
                    source, destination = match.groups()
                    if not source.startswith('^'):
                        source = '^' + source
                    return f'{source} url 302 {destination}'

            return None

        except Exception as e:
            logger.error(f"Error converting rule: {line}")
            return None

    def is_valid_rule(self, rule):
        """验证规则格式"""
        if not rule or rule.startswith('#'):
            return False
            
        try:
            if ' url ' not in rule:
                return False
                
            parts = rule.split(' url ')
            if len(parts) != 2:
                return False
                
            pattern, action = parts
            
            valid_actions = [
                'reject', 'reject-200', 'reject-img', 'reject-dict', 'reject-array',
                'script-response-body', 'script-request-body', '302', '307'
            ]
            
            return any(act in action for act in valid_actions)
            
        except:
            return False

    def generate_output(self, rules, hostnames, scripts):
        """生成输出文件"""
        current_time = self.get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')
        
        output = f"""# AD Rewrite Rules
# Update: {current_time}
# Total rules: {len(rules)}
# Maintainer: Centralmatrix3
"""
        # 添加脚本部分
        if scripts:
            output += "\n[rewrite_local]\n"
            for name, script_info in scripts.items():
                output += f"# {name}\n"
                output += f"{script_info['pattern']} url script-response-body {script_info['script']}\n"

        # 添加重写规则
        if rules:
            if not scripts:  # 如果前面没有添加 [rewrite_local]
                output += "\n[rewrite_local]\n"
            for rule in sorted(rules):
                if not rule.startswith('#'):
                    output += f"{rule}\n"

        # 添加主机名
        if hostnames:
            output += "\n[mitm]\n"
            output += f"hostname = {', '.join(sorted(hostnames))}\n"

        return output

    def run(self):
        """主运行逻辑"""
        all_rules = set()
        all_hostnames = set()
        all_scripts = {}

        # 处理每个规则源
        for name, url in REWRITE_SOURCES.items():
            content = self.download_rules(name, url)
            if content:
                rules, hostnames, scripts = self.parse_rules(content)
                all_rules.update(rules)
                all_hostnames.update(hostnames)
                all_scripts.update(scripts)

        # 生成输出文件
        output = self.generate_output(all_rules, all_hostnames, all_scripts)
        
        # 保存文件
        output_path = os.path.join(self.REPO_PATH, self.REWRITE_DIR, self.OUTPUT_FILE)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)

        logger.info(f"Generated rules file: {output_path}")
        logger.info(f"Total rules: {len(all_rules)}")
        logger.info(f"Total hostnames: {len(all_hostnames)}")
        logger.info(f"Total scripts: {len(all_scripts)}")

if __name__ == "__main__":
    processor = RuleProcessor()
    processor.run()
