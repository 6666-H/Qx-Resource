import requests
import datetime
import os
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def get_remote_rules():
    urls = list(set([
        'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/QuantumultX/Redirect/Redirect.conf',
        'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/QuantumultX/SafeRedirect/SafeRedirect.conf',
        'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/Loon/BlockHTTPDNS/BlockHTTPDNS.plugin'
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
        current_time = datetime.datetime.now() + datetime.timedelta(hours=8)
        date_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存到指定路径
        with open('rewrite/ad/text.config', 'w', encoding='utf-8') as f:
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
