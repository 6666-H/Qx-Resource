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
            
            # 1. 处理 Surge 脚本规则
            if any(keyword in line for keyword in ['type=http-response', 'type=http-request', 'script-path=']):
                pattern = r'pattern=([^,]+).*script-path=([^,\s]+)'
                match = re.search(pattern, line)
                if match:
                    url, script = match.groups()
                    script_type = 'response' if 'http-response' in line else 'request'
                    return f'url script-{script_type}-body {url.strip()} {script.strip()}'

            # 2. 处理 Map Local 规则
            if ('data-type=' in line or 'data=' in line) and line.startswith('^http'):
                url_pattern = r'^([^\s]+)'
                match = re.search(url_pattern, line)
                if match:
                    return f'url reject-dict {match.group(1)}'

            # 3. 处理域名规则
            domain_types = ['DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD']
            for domain_type in domain_types:
                if line.startswith(f'{domain_type},'):
                    pattern = f'{domain_type},([^,]+),?([^,]*)'
                    match = re.search(pattern, line)
                    if match:
                        domain, action = match.groups()
                        action = action.strip() if action else 'reject'
                        host_type = 'host' if domain_type == 'DOMAIN' else domain_type.lower().replace('domain-', 'host-')
                        return f'{host_type}, {domain.strip()}, {action.lower()}'

            # 4. 处理 URL 规则
            if 'URL-REGEX' in line or 'url-regex' in line:
                pattern = r'URL-REGEX,([^,]+),?([^,]*)'
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    url, action = match.groups()
                    action = action.strip() if action else 'reject'
                    return f'url reject-200 {url.strip()}'

            # 5. 处理重定向规则
            if '302' in line or '307' in line:
                pattern = r'([^\s]+)\s+30[27]\s+([^\s]+)'
                match = re.search(pattern, line)
                if match:
                    source, destination = match.groups()
                    return f'url 302 {source.strip()} {destination.strip()}'

            # 6. 处理普通 reject 规则
            if 'reject' in line.lower():
                # 处理带逗号的格式
                if ',' in line:
                    pattern = r'([^,]+),\s*reject'
                    match = re.search(pattern, line)
                    if match:
                        return f'url reject-200 {match.group(1).strip()}'
                # 处理空格分隔的格式
                else:
                    parts = line.split()
                    if len(parts) >= 2 and 'reject' in parts[1].lower():
                        return f'url reject-200 {parts[0]}'

            # 7. 处理 AND 规则
            if line.startswith('AND,'):
                url_pattern = r'URL-REGEX,"([^"]+)"'
                match = re.search(url_pattern, line)
                if match:
                    return f'url reject {match.group(1)}'

            # 8. 处理其他 URL 规则
            if '^http' in line or 'http' in line:
                parts = line.split()
                if len(parts) >= 2:
                    return f'url {parts[1]} {parts[0]}'

        except Exception as e:
            print(f"Error converting rule: {line}")
            print(f"Error details: {str(e)}")
            return None

        return line

    def is_valid_rule(self, rule):
        if not rule or rule.startswith('#'):
            return False
                
        try:
            parts = rule.split()
            if len(parts) < 2:
                return False
                
            valid_types = {
                'url': ['reject', 'reject-200', 'reject-img', 'reject-dict', 'reject-array',
                       'script-response-body', 'script-request-body',
                       'script-response-header', 'script-request-header',
                       'request-header', 'response-header', '302', '307'],
                'host': ['reject'],
                'host-suffix': ['reject'],
                'host-keyword': ['reject']
            }
            
            rule_type = parts[0]
            if rule_type in valid_types:
                if len(parts) < 3:
                    return False
                action = parts[1]
                return any(action.startswith(valid_action) for valid_action in valid_types[rule_type])
                    
        except Exception as e:
            print(f"Error validating rule: {rule}")
            print(f"Error details: {str(e)}")
            return False
                        
        return True

    def parse_rules(self, content):
        rules = set()
        hostnames = set()
        js_methods = set()
        
        if not content:
            return rules, hostnames, js_methods

        current_section = None
        in_script = False
        script_content = []
        
        for line in content.splitlines():
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue

            # 检测段落标记
            if line.startswith('['):
                current_section = line.strip('[]').upper()
                in_script = False
                if script_content:
                    js_methods.add('\n'.join(script_content))
                    script_content = []
                continue

            # 处理 MITM 部分
            if current_section == 'MITM' or 'hostname' in line.lower():
                if '%APPEND%' in line:
                    hosts = line.split('%APPEND%')[1].strip().split(',')
                elif 'hostname' in line.lower() and '=' in line:
                    hosts = line.split('=')[1].strip().split(',')
                else:
                    hosts = line.strip().split(',')
                
                hostnames.update(h.strip() for h in hosts if h.strip() and not h.startswith('#'))
                continue

            # 处理脚本内容
            if current_section == 'SCRIPT' or 'function' in line or 'var ' in line:
                in_script = True
                script_content.append(line)
                continue
            
            if in_script:
                script_content.append(line)
                continue

            # 处理规则部分
            if current_section in ['RULE', 'URL REWRITE', 'MAP LOCAL', None]:
                converted = self.convert_surge_to_quanx(line)
                if converted and self.is_valid_rule(converted):
                    rules.add(converted)

        # 添加最后的脚本内容
        if script_content:
            js_methods.add('\n'.join(script_content))

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
            hostname_list = sorted(hostnames)
            # 分组显示，每组最多50个hostname
            GROUP_SIZE = 50
            for i in range(0, len(hostname_list), GROUP_SIZE):
                group = hostname_list[i:i + GROUP_SIZE]
                content += f"hostname = {', '.join(group)}\n"
        
        return content

    def merge_rules(self, sources):
        all_rules = set()
        all_hostnames = set()
        all_js_methods = set()
        
        total_sources = len(sources)
        current = 0
        
        for name, url in sources.items():
            current += 1
            print(f"\nProcessing {current}/{total_sources}: {name}")
            content = self.download_rules(name, url)
            if content:
                try:
                    rules, hostnames, js_methods = self.parse_rules(content)
                    print(f"Found {len(rules)} rules, {len(hostnames)} hostnames, {len(js_methods)} scripts")
                    all_rules.update(rules)
                    all_hostnames.update(hostnames)
                    all_js_methods.update(js_methods)
                except Exception as e:
                    print(f"Error processing {name}: {str(e)}")

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
