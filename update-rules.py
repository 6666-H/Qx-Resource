import requests
import datetime
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def get_remote_rules():
    # 使用集合去重 URLs
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
        'https://adrules.top/adrules.list'
    ]))
    
    rules = set()
    source_stats = {}  # 用于记录每个源的规则数量
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            response.raise_for_status()
            content = response.text
            
            # 为每个源创建一个临时集合
            source_rules = set()
            
            # 处理每一行规则
            for line in content.splitlines():
                line = line.strip()
                if line and line.startswith('||') and '^' in line:
                    source_rules.add(line)
            
            # 记录这个源的规则数量
            source_stats[url] = len(source_rules)
            
            # 将这个源的规则添加到总规则集合中
            rules.update(source_rules)
            
            print(f"Fetched {len(source_rules)} rules from {url}")
            
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            continue
    
    return rules, source_stats

def update_local_rules():
    # 获取远程规则和统计信息
    remote_rules, source_stats = get_remote_rules()
    
    # 读取本地规则
    try:
        with open('ad-list', 'r', encoding='utf-8') as f:
            local_content = f.read()
    except FileNotFoundError:
        print("Local file not found, creating new one")
        local_content = ''
    except Exception as e:
        print(f"Error reading local file: {str(e)}")
        local_content = ''
    
    # 解析本地规则
    local_rules = set()
    for line in local_content.splitlines():
        line = line.strip()
        if line and line.startswith('||') and '^' in line:
            local_rules.add(line)
    
    # 合并规则并去重
    merged_rules = local_rules | remote_rules
    
    # 写入文件
    try:
        # 获取北京时间
        current_time = datetime.datetime.now() + datetime.timedelta(hours=8)
        date_str = current_time.strftime('%Y-%m-%d')
        time_str = current_time.strftime('%H:%M:%S')
        
        with open('ad-list', 'w', encoding='utf-8') as f:
            f.write(f'! Updated: {date_str} {time_str} (UTC+8)\n')
            f.write('! Title: Combined Ad Rules\n')
            f.write(f'! Total count: {len(merged_rules)}\n')
            
            # 添加每个源的统计信息
            f.write('\n! Source Statistics:\n')
            for url, count in source_stats.items():
                f.write(f'! {url}: {count} rules\n')
            
            f.write('\n')  # 添加空行分隔
            
            # 排序并写入规则
            for rule in sorted(merged_rules):
                f.write(f'{rule}\n')
                
        print(f"\nSuccessfully updated rules at {date_str} {time_str}")
        print(f"Total unique rules: {len(merged_rules)}")
        print("\nSource statistics:")
        for url, count in source_stats.items():
            print(f"{url}: {count} rules")
        
    except Exception as e:
        print(f"Error writing to file: {str(e)}")

if __name__ == '__main__':
    update_local_rules()
