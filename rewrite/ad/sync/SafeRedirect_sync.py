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
        with open('rewrite/ad/Ad.config', 'w', encoding='utf-8') as f:
            f.write(f'# 自动维护: {date_str}\n')
            f.write(f'# 总规则条数：{len(remote_rules)}\n')
            
            for rule in remote_rules:
              if not rule.startswith('#'):
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
