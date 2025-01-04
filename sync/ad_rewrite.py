import os
import re
import requests
import datetime
from datetime import timedelta
import git
from pathlib import Path
import time

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
        Path(os.path.join(self.REPO_PATH, self.REWRITE_DIR)).mkdir(parents=True, exist_ok=True)

    def get_beijing_time(self):
        return datetime.datetime.utcnow() + timedelta(hours=8)

    def download_rules(self, name, url):
        for attempt in range(self.RETRY_COUNT):
            try:
                print(f"Downloading rules from {name}... (Attempt {attempt + 1})")
                response = requests.get(url, timeout=self.TIMEOUT)
                response.raise_for_status()
                content = response.text
                print(f"Downloaded content for {name}:")
                print(content[:500])  # 打印前500个字符用于调试
                return content
            except Exception as e:
                if attempt == self.RETRY_COUNT - 1:
                    print(f"Failed to download {name} after {self.RETRY_COUNT} attempts: {str(e)}")
                    return None
                print(f"Retry after error: {str(e)}")
                time.sleep(2)
        return None

    def convert_surge_to_quanx(self, line):
        if not line or line.startswith('#'):
            return line

        try:
            line = line.replace('\t', ' ').strip()
            
            # 处理 AND 规则
            if line.startswith('AND,'):
                url_regex = re.search(r'URL-REGEX,"([^"]+)"', line)
                user_agent = re.search(r'USER-AGENT,"([^"]+)"', line)
                if url_regex:
                    return f'url reject {url_regex.group(1)}'

            # 处理 DOMAIN 规则
            if line.startswith('DOMAIN,'):
                parts = line.split(',')
                if len(parts) >= 2:
                    domain = parts[1].strip()
                    action = 'reject'
                    if 'REJECT-NO-DROP' in line:
                        action = 'reject-no-drop'
                    return f'host, {domain}, {action}'

            # 处理 Map Local 规则
            if ('data-type=' in line or 'data=' in line):
                pattern = r'^([^\s]+)'
                match = re.search(pattern, line)
                if match:
                    url = match.group(1)
                    return f'url reject-dict {url}'

            # 处理脚本规则
            if ('type=http-response' in line or 'type=http-request' in line) and 'script-path=' in line:
                pattern = r'pattern=([^,]+).*script-path=([^,\s]+)'
                match = re.search(pattern, line)
                if match:
                    url, script = match.groups()
                    requires_body = 'requires-body=true' in line
                    script_type = 'response' if 'http-response' in line else 'request'
                    body_type = '-body' if requires_body else ''
                    return f'url script-{script_type}{body_type} {url.strip()} {script.strip()}'

            # 处理 URL-REGEX 规则
            if 'URL-REGEX' in line or 'url-regex' in line:
                pattern = r'URL-REGEX,([^,]+),?([^,]*)'
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    url, action = match.groups()
                    action = action.strip() if action else 'reject'
                    return f'url reject-200 {url.strip()}'

            # 处理重定向规则
            if '302' in line or '307' in line:
                pattern = r'([^\s]+)\s+30[27]\s+([^\s]+)'
                match = re.search(pattern, line)
                if match:
                    source, destination = match.groups()
                    return f'url 302 {source.strip()} {destination.strip()}'

            # 处理普通 reject 规则
            if 'reject' in line.lower():
                if ',' in line:
                    pattern = r'([^,]+),\s*reject'
                    match = re.search(pattern, line)
                    if match:
                        return f'url reject-200 {match.group(1).strip()}'
                else:
                    parts = line.split()
                    if len(parts) >= 2 and 'reject' in parts[1].lower():
                        return f'url reject-200 {parts[0]}'

        except Exception as e:
            print(f"Error converting rule: {line}")
            print(f"Error details: {str(e)}")
            return None

        return line

    def parse_rules(self, content):
        rules = set()
        hostnames = set()
        js_methods = set()
        rule_types = set()  # 用于收集所有的规则类型
        
        if not content:
            return rules, hostnames, js_methods, rule_types

        current_section = None
        in_script = False
        script_content = []
        
        # 使用正则匹配所有 [xxx] 格式的规则类型
        section_pattern = r'^\[(.*?)\]'
        
        for line in content.splitlines():
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue

            # 检测段落标记
            section_match = re.match(section_pattern, line)
            if section_match:
                current_section = section_match.group(1).upper()
                rule_types.add(current_section)  # 收集规则类型
                if in_script:
                    in_script = False
                    if script_content:
                        js_methods.add('\n'.join(script_content))
                        script_content = []
                continue

            # 处理 MITM 部分
            if current_section == 'MITM' or 'hostname' in line.lower():
                # 处理 %APPEND% 格式
                if '%APPEND%' in line:
                    hosts = line.split('%APPEND%')[1].strip().split(',')
                # 处理 hostname = 格式
                elif 'hostname' in line.lower() and '=' in line:
                    hosts = line.split('=')[1].strip().split(',')
                # 处理直接的域名列表
                else:
                    hosts = line.split(',')

                # 清理和验证每个hostname
                for host in hosts:
                    host = host.strip()
                    if host and not host.startswith('#'):
                        # 移除可能的前缀
                        host = host.replace('*.', '')
                        # 基本的域名格式验证
                        if '.' in host and not any(c in host for c in [' ', '"', "'", '(', ')']):
                            hostnames.add(host)
                continue

            # 处理脚本内容
            if current_section == 'SCRIPT':
                if 'pattern=' in line or 'script-path=' in line:
                    converted = self.convert_surge_to_quanx(line)
                    if converted and self.is_valid_rule(converted):
                        rules.add(converted)
                else:
                    script_content.append(line)
                continue

            # 处理其他规则
            converted = self.convert_surge_to_quanx(line)
            if converted and self.is_valid_rule(converted):
                rules.add(converted)
                
                # 从规则中提取域名
                if 'url' in converted:
                    try:
                        url_pattern = re.search(r'https?://([^/]+)', converted)
                        if url_pattern:
                            domain = url_pattern.group(1)
                            domain = domain.split(':')[0]
                            if '.' in domain and not any(c in domain for c in [' ', '"', "'", '(', ')']):
                                hostnames.add(domain)
                    except:
                        pass

        # 添加最后的脚本内容
        if script_content:
            js_methods.add('\n'.join(script_content))

        return rules, hostnames, js_methods, rule_types

    def is_valid_rule(self, rule):
        if not rule or rule.startswith('#'):
            return False
