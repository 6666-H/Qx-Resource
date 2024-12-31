import os
import requests
import datetime
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def validate_rule(rule):
    """验证规则格式并返回标准化的规则"""
    # 移除所有空白字符
    rule = rule.strip()
    
    # 跳过空行和注释
    if not rule or rule.startswith(('!', '#')):
        return None
        
    # 分割规则，只保留主要部分
    parts = rule.split(',')
    if not parts:
        return None
        
    # 获取规则类型和域名
    rule_type = parts[0]
    if rule_type.startswith("HOST"):
        rule_type = "DOMAIN"
    
    # 如果有域名部分
    if len(parts) >= 2:
        domain = parts[1]
        return f"{rule_type},{domain}"
    elif ',' not in rule:
        # 处理可能没有类型前缀的规则
        return f"DOMAIN,{rule}"
        
    return parts[0]

def read_rules_from_file(file_path):
    rules = {}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                normalized = validate_rule(line.strip())
                if normalized:
                    rules[normalized] = normalized
    return rules

def process_rules(content):
    rules = {}
    count = 0
    for line in content.splitlines():
        normalized = validate_rule(line)
        if normalized:
            rules[normalized] = normalized
            count += 1
    return rules, count

def fetch_remote_rules(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        rules, count = process_rules(response.text)
        print(f"Fetched {count} rules from {url}")
        return rules, count
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")
        return {}, 0

def get_remote_rules():
    urls = list(set([
        'https://whatshub.top/rule/AntiAD.list',
        'https://github.com/thNylHx/Tools/raw/main/Ruleset/Surge/Block/Ads_ml.list',
        'https://raw.githubusercontent.com/Code-Dramatist/Rule_Actions/main/Reject_Rule/Reject_Rule.rule',
        'https://raw.githubusercontent.com/zqzess/rule_for_quantumultX/refs/heads/master/QuantumultX/rules/AdBlock.list',
        'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/QuantumultX/AdvertisingLite/AdvertisingLite.list',
        'https://raw.githubusercontent.com/Irrucky/Tool/main/Surge/rules/Reject.list',
        'https://ruleset.skk.moe/List/non_ip/reject.conf',
        'https://raw.githubusercontent.com/dler-io/Rules/refs/heads/main/Surge/Surge%203/Provider/AdBlock.list',
        'https://ruleset.skk.moe/List/ip/reject.conf',
        'https://raw.githubusercontent.com/NobyDa/Script/master/QuantumultX/AdRule.list',
        'https://adrules.top/adrules.list'
    ]))
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    all_rules = {}
    source_stats = {}
    
    for url in urls:
        rules, count = fetch_remote_rules(url, headers)
        all_rules.update(rules)
        if count > 0:
            source_stats[url] = count
            
    return sorted(all_rules.values()), source_stats

def write_rules_to_file(file_path, rules, source_stats):
    try:
        current_time = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f'# 更新时间: {current_time}\n')
            f.write(f'# 规则数量: {len(rules)}\n\n')
            for rule in sorted(rules):
                f.write(f'{rule}\n')
        return current_time
    except Exception as e:
        print(f"Error writing to file: {str(e)}")
        return None

def update_local_rules():
    file_path = 'rules/ad_list.text'
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    existing_rules = read_rules_from_file(file_path)
    remote_rules, source_stats = get_remote_rules()
    
    # 合并现有规则和远程规则
    all_rules = {**existing_rules}
    for rule in remote_rules:
        all_rules[rule] = rule
    
    # 写入更新后的规则到文件
    current_time = write_rules_to_file(file_path, all_rules.values(), source_stats)
    if current_time:
        print(f"\n成功更新规则于 {current_time}")
        print(f"总规则数: {len(all_rules)}")
        print(f"新增规则数: {len(all_rules) - len(existing_rules)}")
        print("\n来源统计 (去重前):")
        for url, count in source_stats.items():
            print(f"{url}: {count} 条规则")

if __name__ == '__main__':
    update_local_rules()
