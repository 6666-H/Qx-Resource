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
README_PATH = "README.md"

# 分流规则源列表
FILTER_SOURCES = {
    "Lan":"https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Surge/Lan/Lan.list",
    "ChinaMax": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/ChinaMax/ChinaMax.list",
    "ChinaMax_2": "https://raw.githubusercontent.com/deezertidal/QuantumultX-Rewrite/refs/heads/master/rule/ChinaMax.list",
    "Direct_Rule": "https://raw.githubusercontent.com/Code-Dramatist/Rule_Actions/main/Direct_Rule/Direct_Rule.rule",
    "GEOIP": "https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/Manual/Rule/Direct.list"
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

def is_ipv6(ip):
    """判断是否为 IPv6 地址"""
    return ':' in ip

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
        'IP6-CIDR,': 'IP-CIDR6,',
        'HOST-REGEX,': 'DOMAIN-REGEX,',
        'GEOIP,': 'GEOIP,'
    }
    
    line = line.strip()
    for old, new in replacements.items():
        line = line.replace(old, new)
    
    parts = line.split(',')
    if len(parts) >= 2:
        rule_type = parts[0]
        domain = parts[1]
        params = ','.join(parts[2:]) if len(parts) > 2 else ""
        
        # 处理 IP-CIDR 和 IP-CIDR6 规则
        if rule_type == 'IP-CIDR':
            ip_parts = domain.split('/')
            if len(ip_parts) >= 1:
                ip = ip_parts[0]
                # 如果是 IPv6 地址，将规则类型改为 IP-CIDR6
                if is_ipv6(ip):
                    rule_type = 'IP-CIDR6'
                cidr = ip_parts[1] if len(ip_parts) > 1 else "32" if not is_ipv6(ip) else "128"
                domain = f"{ip}/{cidr}"
        
        return rule_type, domain, params
    return None, None, None

def get_rule_priority(rule_type):
    """获取规则优先级"""
    priorities = {
        'DOMAIN-REGEX': 3,
        'DOMAIN-KEYWORD': 2,
        'DOMAIN-SUFFIX': 1,
        'DOMAIN': 4,
        'IP-CIDR': 5,
        'IP-CIDR6': 6,
        'GEOIP': 7
    }
    return priorities.get(rule_type, 0)

def remove_duplicates(rules):
    """去除重复规则，优先保留带参数的规则"""
    unique_rules = {}
    
    for rule in rules:
        rule_type, domain, params = standardize_rule(rule)
        if domain:
            # 使用域名作为键
            key = domain
            
            # 获取新规则的优先级
            new_priority = get_rule_priority(rule_type)
            
            # 如果规则已存在
            if key in unique_rules:
                current_type, current_priority, current_params = unique_rules[key]
                # 如果新规则有参数且旧规则没有参数，或者新规则优先级更高
                if (params and not current_params) or new_priority > current_priority:
                    unique_rules[key] = (rule_type, new_priority, params)
            else:
                unique_rules[key] = (rule_type, new_priority, params)
    
    # 转换回规则格式
    result = []
    for domain, (rule_type, _, params) in unique_rules.items():
        if rule_type in ['IP-CIDR', 'IP-CIDR6']:
            rule = f"{rule_type},{domain}"
        else:
            rule = f"{rule_type},{domain}"
            
        # 添加额外参数（如果有）
        if params:
            rule += f",{params}"
        
        result.append(rule)
    
    return sorted(result)

def download_and_merge_rules():
    """下载并合并分流规则"""
    beijing_time = get_beijing_time()
    
    # 存储规则的字典
    rules_dict = {}
    comments = []

    # 按规则类型分组
    rule_groups = {
        'DOMAIN-REGEX': [],
        'DOMAIN-KEYWORD': [],
        'DOMAIN-SUFFIX': [],
        'DOMAIN': [],
        'IP-CIDR': [],
        'IP-CIDR6': [],
        'USER-AGENT': [],
        'GEOIP': []
    }

    # 下载和处理规则
    for name, url in FILTER_SOURCES.items():
        try:
            print(f"Downloading rules from {name}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text

            comments.append(f"\n# ======== {name} ========")
            
            for line in content.splitlines():
                rule_type, domain, params = standardize_rule(line.strip())
                if rule_type and domain:
                    if rule_type in rule_groups:
                        rule = f"{rule_type},{domain}"
                        if params:
                            rule += f",{params}"
                        rule_groups[rule_type].append(rule)

        except Exception as e:
            print(f"Error downloading {name}: {str(e)}")

    # 统计去重前的规则数量
    total_before = sum(len(rules) for rules in rule_groups.values())
    
    # 生成去重统计信息
    dedup_stats = ["# 规则去重统计:"]
    dedup_stats.append(f"# 去重前规则总数: {total_before}")
    
    # 对规则进行去重
    for rule_type in rule_groups:
        original_count = len(rule_groups[rule_type])
        rule_groups[rule_type] = remove_duplicates(rule_groups[rule_type])
        new_count = len(rule_groups[rule_type])
        dedup_stats.append(f"# {rule_type}: {original_count} -> {new_count} ({original_count - new_count} 条重复)")
        print(f"{rule_type}: 去重前 {original_count} 条，去重后 {new_count} 条")

    # 统计去重后的总规则数量
    total_after = sum(len(rules) for rules in rule_groups.values())
    dedup_stats.append(f"# 去重后规则总数: {total_after}")
    dedup_stats.append(f"# 重复规则数: {total_before - total_after}")
    print(f"总计：去重前 {total_before} 条，去重后 {total_after} 条")

    # 组合文件头部内容
    header = f"""# 国内分流规则合集
# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in FILTER_SOURCES.items()])}

{chr(10).join(dedup_stats)}

"""

    # 组合最终内容
    final_content = header
    final_content += "\n".join(comments)
    final_content += "\n\n# ======== 去重后的规则 ========\n"
    
    # 按组添加规则（保持优先级顺序）
    for group_name in ['DOMAIN-REGEX', 'DOMAIN-KEYWORD', 'DOMAIN-SUFFIX', 'DOMAIN', 'IP-CIDR', 'IP-CIDR6', 'USER-AGENT', 'GEOIP']:
        if rule_groups[group_name]:
            final_content += f"\n# {group_name}\n"
            final_content += '\n'.join(sorted(rule_groups[group_name]))
            final_content += '\n'

    # 写入合并后的文件
    output_path = os.path.join(REPO_PATH, FILTER_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"Successfully merged {total_after} unique rules to {OUTPUT_FILE}")
    return total_after

def update_readme(rule_count):
    """更新 README.md"""
    beijing_time = get_beijing_time()
    content = f"""# 国内分流规则合集

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 规则说明
本规则集合并自各个开源规则，将 HOST 类规则统一转换为 DOMAIN 格式。
当前规则数量：{rule_count}

## 规则来源
{chr(10).join([f'- {name}: {url}' for name, url in FILTER_SOURCES.items()])}

## 使用方法
规则文件地址: https://raw.githubusercontent.com/[你的用户名]/[仓库名]/main/Rule/Direct/China_Max.list
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
