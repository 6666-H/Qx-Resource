import os
import requests
import datetime
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def normalize_rule(rule):
    if rule.startswith("HOST"):
        return "DOMAIN" + rule[4:]
    return rule

def get_remote_rules():
    urls = [
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
    ]
    urls = list(set(urls))
    all_rules = {}
    source_stats = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            response.raise_for_status()
            content = response.text
            rules_count = 0
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith('!') and not line.startswith('#'):
                    normalized = normalize_rule(line)
                    if normalized not in all_rules or (normalized.startswith("DOMAIN") and all_rules[normalized].startswith("HOST")):
                        all_rules[normalized] = normalized
                    rules_count += 1
            source_stats[url] = rules_count
            print(f"Fetched {rules_count} rules from {url}")
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            continue
    return sorted(all_rules.values()), source_stats

def update_local_rules():
    remote_rules, source_stats = get_remote_rules()
    file_path = 'rules/ad_list.text'
    existing_rules = {}
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    normalized = normalize_rule(line)
                    if normalized not in existing_rules or (normalized.startswith("DOMAIN") and existing_rules[normalized].startswith("HOST")):
                        existing_rules[normalized] = normalized
    
    all_rules = existing_rules.copy()
    for rule in remote_rules:
        normalized = normalize_rule(rule)
        if normalized not in all_rules or (normalized.startswith("DOMAIN") and all_rules[normalized].startswith("HOST")):
            all_rules[normalized] = normalized
    
    try:
        current_time = datetime.datetime.now() + datetime.timedelta(hours=8)
        date_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f'# 更新时间: {date_str}\n')
            f.write(f'# 规则数量: {len(all_rules)}\n\n')
            for rule in sorted(all_rules.values()):
                f.write(f'{rule}\n')
        
        print(f"\nSuccessfully updated rules at {date_str}")
        print(f"Total rules: {len(all_rules)}")
        print(f"New rules added: {len(all_rules) - len(existing_rules)}")
        print("\nSource statistics (before deduplication):")
        for url, count in source_stats.items():
            print(f"{url}: {count} rules")
    except Exception as e:
        print(f"Error writing to file: {str(e)}")

if __name__ == '__main__':
    update_local_rules()

