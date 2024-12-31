import requests
import datetime
import os
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def get_remote_rules():
    urls = list(set([
        'https://whatshub.top/rewrite/adultraplus.conf',
        'https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/%E6%96%B0%E6%89%8B%E5%8F%8B%E5%A5%BD%E3%81%AE%E5%8E%BB%E5%B9%BF%E5%91%8A%E9%9B%86%E5%90%88.official.sgmodule',
        'https://kelee.one/Tool/Loon/Plugin/WexinMiniPrograms_Remove_ads.plugin',
        'https://whatshub.top/rewrite/wechatad.conf',
        'https://raw.githubusercontent.com/chxm1023/Advertising/main/AppAd.conf'
    ]))
    
    all_content = []
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
                if line:
                    all_content.append(line)
                    if not line.startswith('#') and not line.startswith('!'):
                        rules_count += 1
            
            source_stats[url] = rules_count
            print(f"Fetched {rules_count} rules from {url}")
            
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            continue
    
    return all_content, source_stats

def update_local_rules():
    content, source_stats = get_remote_rules()
    
    try:
        os.makedirs('rewrite/ad', exist_ok=True)
        
        current_time = datetime.datetime.now() + datetime.timedelta(hours=8)
        date_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        rule_count = sum(1 for line in content if line and not line.startswith('#') and not line.startswith('!'))
        
        with open('rewrite/ad/Ad.config', 'w', encoding='utf-8') as f:
            f.write(f'# Auto maintained: {date_str}\n')
            f.write(f'# Total rules: {rule_count}\n\n')
            
            for line in content:
                f.write(f'{line}\n')
                
        print(f"\nSuccessfully updated rules at {date_str}")
        print(f"Total rules (excluding comments): {rule_count}")
        print("\nSource statistics:")
        for url, count in source_stats.items():
            print(f"{url}: {count} rules")
        
    except Exception as e:
        print(f"Error writing to file: {str(e)}")

if __name__ == '__main__':
    update_local_rules()
