import os
import requests
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def fetch_and_save_rules():
    urls = [
        'https://whatshub.top/rule/Steam.list',
        'https://whatshub.top/rule/Epic.list',
        'https://whatshub.top/rule/Nintendo.list',
        'https://whatshub.top/rule/Sony.list'
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    rules = set()  # 使用集合去重
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=10)
            for line in response.text.splitlines():
                line = line.strip()
                if line and not line.startswith(('#', '!')):
                    if line.startswith('HOST'):
                        line = 'DOMAIN' + line[4:]
                    rules.add(line)
        except Exception as e:
            print(f"获取规则失败 {url}: {e}")
    
    # 保存规则
    os.makedirs('rules', exist_ok=True)
    with open('rules/game_list.text', 'w', encoding='utf-8') as f:
        f.write(f'# 更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'# 规则数量: {len(rules)}\n\n')
        f.write('\n'.join(sorted(rules)))
    
    print(f"已保存 {len(rules)} 条规则")

if __name__ == '__main__':
    fetch_and_save_rules()
