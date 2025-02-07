import os
import requests
import datetime
from datetime import timedelta
import git
from pathlib import Path
import re

# 配置项
REPO_PATH = "Rule"
FILTER_DIR = "Direct"
OUTPUT_FILE = "China_Max.list"
README_PATH = "README_China_Max.md"

FILTER_SOURCES = {
    "GEOIP":"https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/Manual/Rule/Direct.list",
    "China": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/China/China.list",
    "ChinaIPs": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/QuantumultX/ChinaIPs/ChinaIPs.list",
    "ChinaMax": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/ChinaMax/ChinaMax.list",
    "ChinaMaxNoIP": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/ChinaMaxNoIP/ChinaMaxNoIP.list",
}

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.datetime.utcnow()
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time

def setup_directory():
    """创建必要的目录"""
    Path(os.path.join(REPO_PATH, FILTER_DIR)).mkdir(parents=True, exist_ok=True)

def is_ipv4(text):
    """判断是否为 IPv4 地址"""
    try:
        parts = text.split('.')
        return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
    except (ValueError, AttributeError):
        return False

def is_ipv6(text):
    """判断是否为 IPv6 地址"""
    try:
        parts = text.split(':')
        return len(parts) <= 8 and all(len(part) <= 4 and all(c in '0123456789abcdefABCDEF' for c in part) for part in parts if part)
    except (ValueError, AttributeError):
        return False

def standardize_rule(line):
    """标准化规则格式"""
    if not line or line.startswith('#'):
        return None, None, None

    # 规则格式转换映射
    replacements = {
        'HOST-SUFFIX,': 'DOMAIN-SUFFIX,',
        'HOST,': 'DOMAIN,',
        'HOST-KEYWORD,': 'DOMAIN-KEYWORD,',
        'IP-CIDR,': 'IP-CIDR,',
        'IP6-CIDR,': 'IP6-CIDR,',
        'HOST-REGEX,': 'DOMAIN-REGEX,',
        'USER-AGENT,': 'USER-AGENT,'
    }
    
    line = line.strip()
    for old, new in replacements.items():
        line = line.replace(old, new)
    
    parts = line.split(',')
    if len(parts) < 2:
        return None, None, None

    rule_type = parts[0]
    content = parts[1]
    options = parts[2] if len(parts) > 2 else None

    # 处理 IP-CIDR 规则
    if rule_type in ['IP-CIDR', 'IP6-CIDR']:
        if '/' not in content:
            content = f"{content}/{'32' if rule_type == 'IP-CIDR' else '128'}"

    return rule_type, content, options

def get_rule_priority(rule_type):
    """获取规则优先级"""
    priorities = {
        'DOMAIN-REGEX': 1,
        'DOMAIN': 2,
        'DOMAIN-SUFFIX': 3,
        'DOMAIN-KEYWORD': 4,
        'IP-CIDR': 5,
        'IP6-CIDR': 5,
        'USER-AGENT': 6
    }
    return priorities.get(rule_type, 0)

def download_and_merge_rules():
    """下载并合并分流规则"""
    beijing_time = get_beijing_time()
    header = f"""# 国内分流规则合集
# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in FILTER_SOURCES.items()])}

"""
    
    # 存储规则的字典，键为内容，值为元组(规则类型, 选项, 优先级)
    rules_dict = {}
    
    # 下载和处理规则
    for name, url in FILTER_SOURCES.items():
        try:
            print(f"Downloading rules from {name}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            for line in response.text.splitlines():
                rule_type, content, options = standardize_rule(line.strip())
                if content:
                    new_priority = get_rule_priority(rule_type)
                    
                    # 如果规则已存在，比较优先级
                    if content in rules_dict:
                        current_type, current_options, current_priority = rules_dict[content]
                        if new_priority > current_priority:
                            rules_dict[content] = (rule_type, options, new_priority)
                    else:
                        rules_dict[content] = (rule_type, options, new_priority)

        except Exception as e:
            print(f"Error downloading {name}: {str(e)}")

    # 规则分组
    rule_groups = {
        'DOMAIN-REGEX': [],
        'DOMAIN': [],
        'DOMAIN-SUFFIX': [],
        'DOMAIN-KEYWORD': [],
        'IP-CIDR': [],
        'IP6-CIDR': [],
        'USER-AGENT': []
    }

    # 整理规则到分组
    for content, (rule_type, options, _) in rules_dict.items():
        rule = f"{rule_type},{content}"
        if options:
            rule += f",{options}"
        
        if rule_type in rule_groups:
            rule_groups[rule_type].append(rule)

    # 组合最终内容
    final_content = header
    
    # 按组添加规则
    for group_name in rule_groups:
        if rule_groups[group_name]:
            final_content += f"\n# {group_name}\n"
            final_content += '\n'.join(sorted(rule_groups[group_name]))
            final_content += '\n'

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
    content = f"""# 国内分流

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 规则说明
本规则集合并自各个开源规则，将 HOST 类规则统一转换为 DOMAIN 格式。
当前规则数量：{rule_count}

## 规则来源
{chr(10).join([f'- {name}: {url}' for name, url in FILTER_SOURCES.items()])}

## 使用方法
规则文件地址: https://raw.githubusercontent.com/[你的用户名]/[仓库名]/main/{FILTER_DIR}/{OUTPUT_FILE}
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
