import requests
import datetime

def get_remote_rules():
    urls = [
        'https://whatshub.top/rule/AntiAD.list',
        'https://github.com/thNylHx/Tools/raw/main/Ruleset/Surge/Block/Ads_ml.list',
        'https://raw.githubusercontent.com/Code-Dramatist/Rule_Actions/main/Reject_Rule/Reject_Rule.rule',
        'https://raw.githubusercontent.com/zqzess/rule_for_quantumultX/refs/heads/master/QuantumultX/rules/AdBlock.list',
        'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/QuantumultX/AdvertisingLite/AdvertisingLite.list',
        'https://raw.githubusercontent.com/Irrucky/Tool/main/Surge/rules/Reject.list',
        'https://ruleset.skk.moe/List/non_ip/reject.conf'
        'https://raw.githubusercontent.com/dler-io/Rules/refs/heads/main/Surge/Surge%203/Provider/AdBlock.list',
        'https://ruleset.skk.moe/List/ip/reject.conf',
        'https://adrules.top/adrules.list',
        'https://ruleset.skk.moe/List/ip/reject.conf'
    ]
    
    rules = set()
    for url in urls:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                content = response.text
                for line in content.splitlines():
                    if line.startswith('||') and '^' in line:
                        rules.add(line.strip())
        except:
            continue
    
    return rules

def update_local_rules():
    # 获取远程规则
    remote_rules = get_remote_rules()
    
    # 读取本地规则
    try:
        with open('ad-list', 'r', encoding='utf-8') as f:
            local_content = f.read()
    except:
        local_content = ''
    
    # 解析本地规则
    local_rules = set()
    for line in local_content.splitlines():
        if line.startswith('||') and '^' in line:
            local_rules.add(line.strip())
    
    # 合并规则
    merged_rules = local_rules | remote_rules
    
    # 写入文件
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    with open('ad-list', 'w', encoding='utf-8') as f:
        f.write(f'! {current_date}\n')
        for rule in sorted(merged_rules):
            f.write(f'{rule}\n')

if __name__ == '__main__':
    update_local_rules()
