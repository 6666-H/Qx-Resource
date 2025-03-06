import os
import requests
import datetime
from datetime import timedelta
import git
from pathlib import Path
import re

# 配置项
REPO_PATH = "Rule"
FILTER_DIR = "Advertising"
OUTPUT_FILE = "Ad_Lite.list"
README_PATH = "README_Ad_Lite.md"
WHITE_LIST_URL = "https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/Manual/Rule/Ad_White_list.list"

# 分流规则源列表
FILTER_SOURCES = {
    "ADLite":"https://raw.githubusercontent.com/deezertidal/shadowrocket-rules/refs/heads/main/rule/ADLite.list",
    "AdvertisingLite": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/QuantumultX/AdvertisingLite/AdvertisingLite.list"
}

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.datetime.utcnow()
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time

def setup_directory():
    """创建必要的目录"""
    Path(os.path.join(REPO_PATH, FILTER_DIR)).mkdir(parents=True, exist_ok=True)

def is_ip_address(text):
    """判断是否为 IP 地址"""
    parts = text.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False

def standardize_rule(line):
    """标准化规则格式"""
    if not line or line.startswith('#'):
        return None, None
    
    # 规则格式转换映射
    replacements = {
        'HOST-SUFFIX,': 'DOMAIN-SUFFIX,',
        'HOST,': 'DOMAIN,',
        'HOST-KEYWORD,': 'DOMAIN-KEYWORD,',
        'IP-CIDR,': 'IP-CIDR,',
        'IP6-CIDR,': 'IP-CIDR6,',
        'IP6-CIDR,': 'IP-CIDR6,',
        'HOST-REGEX,': 'DOMAIN-REGEX,'  # 添加 REGEX 规则转换
    }
    
    line = line.strip()
    for old, new in replacements.items():
        line = line.replace(old, new)
    
    # 处理 IP-CIDR 规则
    if line.startswith('IP-CIDR,'):
        match = re.match(r'IP-CIDR,([^,]+)', line)
        if match:
            ip_cidr = match.group(1)
            # 提取 IP 和 CIDR
            ip_parts = ip_cidr.split('/')
            if len(ip_parts) >= 1:
                ip = ip_parts[0]
                # 如果没有 CIDR，添加 /32
                cidr = ip_parts[1] if len(ip_parts) > 1 else "32"
                return 'IP-CIDR', f"{ip}/{cidr}"
    
    parts = line.split(',')
    if len(parts) >= 2:
        return parts[0], parts[1].strip()
    return None, None

def get_rule_priority(rule_type):
    """获取规则优先级"""
    priorities = {
        'DOMAIN-REGEX': 1,    # 最高优先级
        'DOMAIN-KEYWORD': 4,  # 调整其他优先级
        'DOMAIN-SUFFIX': 3,
        'DOMAIN': 2,
        'IP-CIDR': 5,
        'IP-CIDR6': 5
    }
    return priorities.get(rule_type, 0)

def get_white_list():
    """获取白名单规则"""
    try:
        response = requests.get(WHITE_LIST_URL, timeout=30)
        response.raise_for_status()
        white_list = set()
        for line in response.text.splitlines():
            _, domain = standardize_rule(line.strip())
            if domain:
                white_list.add(domain)
        return white_list
    except Exception as e:
        print(f"Error downloading white list: {str(e)}")
        return set()

def download_and_merge_rules():
    """下载并合并分流规则"""
    beijing_time = get_beijing_time()
    header = f"""# 广告拦截分流规则合集
# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in FILTER_SOURCES.items()])}

"""
    
    # 存储规则的字典，键为域名/IP，值为元组(规则类型, 优先级)
    rules_dict = {}
    comments = []

    # 获取白名单
    white_list = get_white_list()
    print(f"Loaded {len(white_list)} white list rules")

    # 下载和处理规则
    for name, url in FILTER_SOURCES.items():
        try:
            print(f"Downloading rules from {name}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text

            comments.append(f"\n# ======== {name} ========")
            
            for line in content.splitlines():
                rule_type, domain = standardize_rule(line.strip())
                if domain and domain not in white_list:
                    # 处理 IP 地址
                    if is_ip_address(domain):
                        rules_dict[domain] = ("IP-CIDR", 4)
                        continue

                    # 获取新规则的优先级
                    new_priority = get_rule_priority(rule_type)
                    
                    # 如果域名已存在，比较优先级
                    if domain in rules_dict:
                        current_type, current_priority = rules_dict[domain]
                        if new_priority > current_priority:
                            rules_dict[domain] = (rule_type, new_priority)
                    else:
                        rules_dict[domain] = (rule_type, new_priority)

        except Exception as e:
            print(f"Error downloading {name}: {str(e)}")

    # 按规则类型分组
    rule_groups = {
        'DOMAIN-REGEX': [],   # 添加 REGEX 组
        'DOMAIN-KEYWORD': [],
        'DOMAIN-SUFFIX': [],
        'DOMAIN': [],
        'IP-CIDR': [],
        'IP-CIDR6': [],
        'USER-AGENT': []
    }

    # 整理规则到分组
    for domain, (rule_type, _) in rules_dict.items():
        if rule_type == "IP-CIDR":
            # 检查是否已经包含 CIDR
            if '/' in domain:
                rule = f"IP-CIDR,{domain}"
            else:
                rule = f"IP-CIDR,{domain}/32"
        else:
            rule = f"{rule_type},{domain}"
        
        if rule_type in rule_groups:
            rule_groups[rule_type].append(rule)

    # 组合最终内容
    final_content = header
    final_content += "\n".join(comments)
    final_content += "\n\n# ======== 去重后的规则 ========\n"
    
    # 按组添加规则（保持优先级顺序）
    for group_name in ['DOMAIN-REGEX', 'DOMAIN-KEYWORD', 'DOMAIN-SUFFIX', 'DOMAIN', 'IP-CIDR', 'IP-CIDR6', 'USER-AGENT']:
        if rule_groups[group_name]:
            final_content += f"\n# {group_name}\n"
            final_content += '\n'.join(sorted(rule_groups[group_name]))

    # 写入合并后的文件
    output_path = os.path.join(REPO_PATH, FILTER_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    total_rules = sum(len(rules) for rules in rule_groups.values())
    print(f"Successfully merged {total_rules} unique rules to {OUTPUT_FILE}")
    return total_rules

def update_readme(rule_count):
    """更新 README.md"""
    beijing_time = get_beijing_time()
    content = f"""# 广告拦截分流规则合集

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 规则说明
本规则集合并自各个开源规则，将 HOST 类规则统一转换为 DOMAIN 格式。
当前规则数量：{rule_count}

## 规则来源
{chr(10).join([f'- {name}: {url}' for name, url in FILTER_SOURCES.items()])}

## 使用方法
规则文件地址: https://raw.githubusercontent.com/[你的用户名]/[仓库名]/main/filter/ad_filter.list
"""
    
    with open(os.path.join(REPO_PATH, README_PATH), 'w', encoding='utf-8') as f:
        f.write(content)

def git_push():
    """提交更改到 Git"""
    try:
        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)
        beijing_time = get_beijing_time()
        repo.index.commit(f"Update rules: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
        origin = repo.remote(name='origin')
        origin.push()
        print("Successfully pushed to repository")
    except Exception as e:
        print(f"Error pushing to repository: {str(e)}")

def main():
    setup_directory()
    rule_count = download_and_merge_rules()
    update_readme(rule_count)
    git_push()

if __name__ == "__main__":
    main()
