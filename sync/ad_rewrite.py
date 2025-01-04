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
                return response.text
            except Exception as e:
                if attempt == self.RETRY_COUNT - 1:
                    print(f"Failed to download {name} after {self.RETRY_COUNT} attempts: {str(e)}")
                    return None
                print(f"Retry after error: {str(e)}")
                time.sleep(2)
        return None

    def is_valid_rule(self, rule):
        if not rule or rule.startswith('#'):
            return False
            
        if 'url' in rule:
            try:
                parts = rule.split()
                if len(parts) < 3:
                    return False
                if not any(parts[1] == pattern for pattern in [
                    'reject', 'reject-200', 'reject-img', 'reject-dict', 'reject-array',
                    'script-response-body', 'script-request-body',
                    'script-response-header', 'script-request-header',
                    '302', '307'
                ]):
                    return False
                if not (parts[2].startswith('^http') or parts[2].startswith('http')):
                    return False
            except:
                return False
                
        return True

    def convert_surge_to_quanx(self, line):
        if not line or line.startswith('#'):
            return line

        try:
            line = line.replace('\t', ' ').strip()
            
            if 'script-path' in line:
                if 'type=http-response' in line:
                    pattern = r'pattern\s*=\s*([^,]+).*script-path\s*=\s*([^,\s]+)'
                    match = re.search(pattern, line)
                    if match:
                        path, script_path = match.groups()
                        return f'url script-response-body {path.strip()} {script_path.strip()}'
                        
                elif 'type=http-request' in line:
                    pattern = r'pattern\s*=\s*([^,]+).*script-path\s*=\s*([^,\s]+)'
                    match = re.search(pattern, line)
                    if match:
                        path, script_path = match.groups()
                        return f'url script-request-body {path.strip()} {script_path.strip()}'

            elif '302' in line or '307' in line:
                pattern = r'([^\s]+)\s+30[27]\s+([^\s]+)'
                match = re.search(pattern, line)
                if match:
                    source, destination = match.groups()
                    return f'url 302 {source.strip()} {destination.strip()}'

            elif 'reject' in line:
                if '^http' in line or 'http' in line:
                    pattern = r'([^\s]+)\s+reject'
                    match = re.search(pattern, line)
                    if match:
                        return f'url reject-200 {match.group(1).strip()}'

            elif '^http' in line or 'http' in line:
                parts = line.split()
                if len(parts) >= 2:
                    return f'url {parts[1]} {parts[0]}'

        except Exception as e:
            print(f"Error converting rule: {line}")
            return None

        return line

    def parse_rules(self, content):
        rules = set()
        hostnames = set()
        js_methods = set()
        
        if not content:
            return rules, hostnames, js_methods

        in_mitm_section = False
        in_js_section = False
        
        lines = content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue

            if line.startswith('[MITM]') or line.lower().startswith('hostname'):
                in_mitm_section = True
                in_js_section = False
            elif any(js_marker in line.lower() for js_marker in ['[script]', 'function', 'var ', 'let ', 'const ']):
                in_js_section = True
                in_mitm_section = False
                js_content = []
                while i < len(lines):
                    js_line = lines[i]
                    if js_line.strip() and not any(marker in js_line for marker in ['[MITM]', 'hostname=']):
                        js_content.append(js_line)
                    i += 1
                if js_content:
                    js_methods.add('\n'.join(js_content))
                continue

            if in_mitm_section:
                if line.startswith('hostname'):
                    try:
                        hosts = line.split('=')[1].strip().split(',')
                        hostnames.update(h.strip() for h in hosts if h.strip())
                    except IndexError:
                        print(f"Warning: Invalid hostname line: {line}")
                elif '%APPEND%' in line:
                    try:
                        hosts = line.split('%APPEND%')[1].strip().split(',')
                        hostnames.update(h.strip() for h in hosts if h.strip())
                    except IndexError:
                        print(f"Warning: Invalid APPEND hostname line: {line}")
            
            elif not in_js_section:
                converted_rule = self.convert_surge_to_quanx(line)
                if converted_rule and self.is_valid_rule(converted_rule):
                    rules.add(converted_rule)

            i += 1

        return rules, hostnames, js_methods

    def generate_output(self, rules, hostnames, js_methods):
        header = f"""# 广告拦截重写规则合集
# 更新时间：{self.get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 规则数量：{len(rules)}
# Hostname数量：{len(hostnames)}
# JavaScript方法数量：{len(js_methods)}

"""
        content = header
        
        if js_methods:
            content += "# JavaScript Methods\n"
            for js in js_methods:
                content += f"{js}\n\n"
        
        content += "# Rewrite Rules\n"
        content += '\n'.join(sorted(rules))
        
        if hostnames:
            content += "\n\n# Hostname\n"
            content += f"hostname = {','.join(sorted(hostnames))}\n"
        
        return content

    def merge_rules(self, sources):
        all_rules = set()
        all_hostnames = set()
        all_js_methods = set()
        
        total_sources = len(sources)
        current = 0
        
        for name, url in sources.items():
            current += 1
            print(f"Processing {current}/{total_sources}: {name}")
            content = self.download_rules(name, url)
            if content:
                rules, hostnames, js_methods = self.parse_rules(content)
                all_rules.update(rules)
                all_hostnames.update(hostnames)
                all_js_methods.update(js_methods)

        return all_rules, all_hostnames, all_js_methods

    def save_rules(self, content):
        output_path = os.path.join(self.REPO_PATH, self.REWRITE_DIR, self.OUTPUT_FILE)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Successfully saved rules to {output_path}")
            return True
        except Exception as e:
            print(f"Error saving rules: {str(e)}")
            return False

    def update_readme(self, rule_count, hostname_count):
        beijing_time = self.get_beijing_time()
        content = f"""# 广告拦截重写规则合集

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 规则说明
本重写规则集合并自各个开源规则，去除重复规则。
- 当前规则数量：{rule_count}
- 当前 Hostname 数量：{hostname_count}

## 规则来源
{chr(10).join([f'- {name}: {url}' for name, url in REWRITE_SOURCES.items()])}

## 使用方法
规则文件地址: https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/main/rewrite/ad_rewrite.conf
"""
        
        readme_path = os.path.join(self.REPO_PATH, self.README_PATH)
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Successfully updated README at {readme_path}")
            return True
        except Exception as e:
            print(f"Error updating README: {str(e)}")
            return False

def git_push(repo_path):
    try:
        repo = git.Repo(repo_path)
        repo.git.add(all=True)
        beijing_time = datetime.datetime.utcnow() + timedelta(hours=8)
        repo.index.commit(f"Update rewrite rules: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
        origin = repo.remote(name='origin')
        origin.push()
        print("Successfully pushed to repository")
    except Exception as e:
        print(f"Error pushing to repository: {str(e)}")

def main():
    processor = RuleProcessor()
    rules, hostnames, js_methods = processor.merge_rules(REWRITE_SOURCES)
    content = processor.generate_output(rules, hostnames, js_methods)
    
    if processor.save_rules(content):
        print(f"Successfully processed {len(rules)} rules, {len(hostnames)} hostnames, and {len(js_methods)} JavaScript methods")
        processor.update_readme(len(rules), len(hostnames))
        git_push(processor.REPO_PATH)
    else:
        print("Failed to save rules")

if __name__ == "__main__":
    main()
