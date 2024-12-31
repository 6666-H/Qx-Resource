import os
import requests
import datetime
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def normalize_rule(rule):
    return "DOMAIN" + rule[4:] if rule.startswith("HOST") else rule

def read_rules_from_file(file_path):
    rules = {}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in filter(lambda x: x.strip() and not x.startswith('#'), f):
                normalized = normalize_rule(line.strip())
                rules[normalized] = normalized
    return rules

def process_rules(content):
    rules = {}
    count = 0
    for line in filter(lambda x: x.strip() and not x.startswith(('!', '#')), content.splitlines()):
        normalized = normalize_rule(line.strip())
        if normalized not in rules or (normalized.startswith("DOMAIN") and rules[normalized].startswith("HOST")):
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
    existing_rules = read_rules_from_file(file_path)
    remote_rules, source_stats = get_remote_rules()
    
    # Merge existing and remote rules
    all_rules = {**existing_rules}
    for rule in remote_rules:
        normalized = normalize_rule(rule)
        if normalized not in all_rules or (normalized.startswith("DOMAIN") and all_rules[normalized].startswith("HOST")):
            all_rules[normalized] = normalized
    
    # Write updated rules to file
    current_time = write_rules_to_file(file_path, all_rules.values(), source_stats)
    if current_time:
        print(f"\nSuccessfully updated rules at {current_time}")
        print(f"Total rules: {len(all_rules)}")
        print(f"New rules added: {len(all_rules) - len(existing_rules)}")
        print("\nSource statistics (before deduplication):")
        for url, count in source_stats.items():
            print(f"{url}: {count} rules")

if __name__ == '__main__':
    update_local_rules()
