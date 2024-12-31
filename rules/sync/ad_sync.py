import os
import requests
import datetime
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
    
    # 文件路径
    file_path = 'rules/ad_list.text'
    
    # 读取已有规则
    existing_rules = set()
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                rule = line.strip()
                if rule and not rule.startswith('#'):
                    existing_rules.add(rule)
    
    # 计算新增规则
    new_rules = set(remote_rules) - existing_rules
    
    if not new_rules:
        print("No new rules to add.")
        return
    
    try:
        current_time = datetime.datetime.now() + datetime.timedelta(hours=8)
        date_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 使用追加模式
        with open(file_path, 'a', encoding='utf-8') as f:
            # 如果文件存在且有内容，添加一个换行
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                f.write('\n')
            
            f.write(f'# 更新于: {date_str}，新增规则 {len(new_rules)} 条\n')
            for rule in new_rules:
                f.write(f'{rule}\n')
        
        print(f"\nSuccessfully updated rules at {date_str}")
        print(f"Total new rules added: {len(new_rules)}")
        print("\nSource statistics (before deduplication):")
        for url, count in source_stats.items():
            print(f"{url}: {count} rules")
        
    except Exception as e:
        print(f"Error writing to file: {str(e)}")

if __name__ == '__main__':
    update_local_rules()

