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

def convert_surge_to_quanx(line):
    """将 Surge 模块规则转换为 QuantumultX 格式"""
    if not line or line.startswith('#'):
        return line

    # 处理脚本类型
    if 'script-path' in line:
        try:
            # 解析 Surge 脚本格式
            if 'type=http-response' in line:
                pattern = r'script-path\s*=\s*([^,]+).*argument\s*=\s*([^,]+)?'
                match = re.search(pattern, line)
                if match:
                    script_path = match.group(1).strip()
                    argument = match.group(2).strip() if match.group(2) else ''
                    # 提取路径匹配规则
                    path_match = re.search(r'pattern\s*=\s*([^,]+)', line)
                    if path_match:
                        path = path_match.group(1).strip()
                        return f'url script-response-body {path} {script_path}'
                    
            elif 'type=http-request' in line:
                pattern = r'script-path\s*=\s*([^,]+).*argument\s*=\s*([^,]+)?'
                match = re.search(pattern, line)
                if match:
                    script_path = match.group(1).strip()
                    argument = match.group(2).strip() if match.group(2) else ''
                    # 提取路径匹配规则
                    path_match = re.search(r'pattern\s*=\s*([^,]+)', line)
                    if path_match:
                        path = path_match.group(1).strip()
                        return f'url script-request-body {path} {script_path}'

        except Exception as e:
            print(f"Error converting script rule: {line}")
            return None

    # 处理重定向规则
    elif '302' in line or '307' in line:
        try:
            pattern = r'(.+?)\s+30[27]\s+(.+)'
            match = re.search(pattern, line)
            if match:
                source, destination = match.groups()
                return f'url 302 {source.strip()} {destination.strip()}'
        except Exception as e:
            print(f"Error converting redirect rule: {line}")
            return None

    # 处理 URL 重写规则
    elif '^http' in line:
        try:
            if 'reject' in line:
                # 处理 reject 类型规则
                pattern = r'(.+?)\s+reject'
                match = re.search(pattern, line)
                if match:
                    return f'url reject-200 {match.group(1).strip()}'
            else:
                # 处理其他重写规则
                parts = line.split()
                if len(parts) >= 2:
                    return f'url {parts[1]} {parts[0]}'
        except Exception as e:
            print(f"Error converting URL rewrite rule: {line}")
            return None

    return line

class RuleProcessor:
    def __init__(self):
        self.REPO_PATH = "ad"
        self.REWRITE_DIR = "rewrite"
        self.OUTPUT_FILE = "ad_rewrite.conf"
        self.README_PATH = "README-rewrite.md"
        self.RETRY_COUNT = 3
        self.TIMEOUT = 30
        
        # 确保目录存在
        self.setup_directory()

    def setup_directory(self):
        """创建必要的目录"""
        Path(os.path.join(self.REPO_PATH, self.REWRITE_DIR)).mkdir(parents=True, exist_ok=True)

    def get_beijing_time(self):
        """获取北京时间"""
        return datetime.datetime.utcnow() + timedelta(hours=8)

    def download_rules(self, name, url):
        """下载规则，带重试机制"""
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
        """验证规则格式是否正确"""
        if not rule or rule.startswith('#'):
            return False
        # 扩展规则验证
        valid_patterns = [
            'url reject',
            'url reject-200',
            'url reject-img',
            'url reject-dict',
            'url reject-array',
            'url script-response-body',
            'url script-request-body',
            'url script-response-header',
            'url script-request-header',
            'url 302',
            'url 307',
            '^http'
        ]
        return any(pattern in rule for pattern in valid_patterns)

    def parse_rules(self, content):
        """解析规则内容"""
        rules = set()
        hostnames = set()
        comments = []

        if not content:
            return rules, hostnames, comments

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith('#'):
                comments.append(line)
            elif line.startswith('hostname'):
                try:
                    hosts = line.split('=')[1].strip().split(',')
                    hostnames.update(h.strip() for h in hosts if h.strip())
                except IndexError:
                    print(f"Warning: Invalid hostname line: {line}")
            else:
                # 转换 Surge 规则为 QuantumultX 格式
                converted_rule = convert_surge_to_quanx(line)
                if converted_rule and self.is_valid_rule(converted_rule):
                    rules.add(converted_rule)

        return rules, hostnames, comments

    def merge_rules(self, sources):
        """合并所有规则"""
        all_rules = set()
        all_hostnames = set()
        all_comments = []
        
        total_sources = len(sources)
        current = 0
        
        for name, url in sources.items():
            current += 1
            print(f"Processing {current}/{total_sources}: {name}")
            content = self.download_rules(name, url)
            if content:
                rules, hostnames, comments = self.parse_rules(content)
                all_rules.update(rules)
                all_hostnames.update(hostnames)
                all_comments.extend([f"\n# ======== {name} ========"] + comments)

        return all_rules, all_hostnames, all_comments

    def generate_output(self, rules, hostnames, comments):
        """生成输出内容"""
        header = f"""# 广告拦截重写规则合集
# 更新时间：{self.get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 规则数量：{len(rules)}
# Hostname数量：{len(hostnames)}

"""
        content = header
        content += "\n".join(comments)
        content += "\n\n# ======== 去重后的规则 ========\n"
        content += '\n'.join(sorted(rules))
        
        if hostnames:
            content += "\n\n# ======== Hostname ========\n"
            content += f"hostname = {','.join(sorted(hostnames))}\n"
        
        return content

    def save_rules(self, content):
        """保存规则到文件"""
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
        """更新 README 文件"""
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
    """提交更改到 Git"""
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
    rules, hostnames, comments = processor.merge_rules(REWRITE_SOURCES)
    content = processor.generate_output(rules, hostnames, comments)
    
    if processor.save_rules(content):
        print(f"Successfully processed {len(rules)} rules and {len(hostnames)} hostnames")
        # 更新 README
        processor.update_readme(len(rules), len(hostnames))
        # Git 提交
        git_push(processor.REPO_PATH)
    else:
        print("Failed to save rules")

if __name__ == "__main__":
    main()
