import requests
import datetime
import os
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

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
    
    all_rules = set()  # 使用set进行去重
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
                    all_rules.add(line)
                    rules_count += 1
            
            source_stats[url] = rules_count
            print(f"Fetched {rules_count} rules from {url}")
            
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            continue
    
    return sorted(all_rules), source_stats

def update_local_rules():
    # 获取新的规则
    remote_rules, source_stats = get_remote_rules()
    
    try:
        # 确保目录存在
        os.makedirs('rules/ad_list.text', exist_ok=True)
        
        current_time = datetime.datetime.now() + datetime.timedelta(hours=8)
        date_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存到指定路径
        with open('rules/ad_list.text', 'w', encoding='utf-8') as f:
            f.write(f'# 由whatshub.top自动维护 {date_str}\n')
            f.write(f'# 总规则条数：{len(remote_rules)}\n')
            
            for rule in remote_rules:
                f.write(f'{rule}\n')
                
        print(f"\nSuccessfully updated rules at {date_str}")
        print(f"Total unique rules: {len(remote_rules)}")
        print("\nSource statistics (before deduplication):")
        for url, count in source_stats.items():
            print(f"{url}: {count} rules")
        
    except Exception as e:
        print(f"Error writing to file: {str(e)}")

if __name__ == '__main__':
    update_local_rules()
