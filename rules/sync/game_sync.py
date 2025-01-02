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
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    rules = set()
    
    for url in urls:
        try:
            session = requests.Session()
            response = session.get(url, headers=headers, verify=False, timeout=15)
            
            # 检查是否是 Cloudflare 验证页面
            if 'challenge-platform' in response.text:
                print(f"警告: {url} 需要通过 Cloudflare 验证")
                continue
                
            for line in response.text.splitlines():
                line = line.strip()
                if line and not line.startswith(('#', '!')):
                    if line.startswith('HOST'):
                        line = 'DOMAIN' + line[4:]
                    rules.add(line)
            
            print(f"成功获取 {url} 的规则")
            
        except Exception as e:
            print(f"获取规则失败 {url}: {e}")
            continue
    
    # 保存规则
    if rules:
        os.makedirs('rules', exist_ok=True)
        with open('rules/game_list.text', 'w', encoding='utf-8') as f:
            f.write(f'# 更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write(f'# 规则数量: {len(rules)}\n\n')
            f.write('\n'.join(sorted(rules)))
        print(f"\n已保存 {len(rules)} 条规则")
    else:
        print("\n警告: 没有获取到任何规则")

if __name__ == '__main__':
    fetch_and_save_rules()
