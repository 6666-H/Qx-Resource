import os
import requests
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def fetch_and_save_rules():
    urls = [
        'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Surge/Game/Game.list',
        'https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Steam.list',
        'https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Epic.list',
        'https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Sony.list',
        'https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Nintendo.list'
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/plain'
    }
    
    rules = set()
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=10)
            response.encoding = 'utf-8'  # 明确指定编码
            
            if not response.ok:
                print(f"获取失败 {url}: HTTP {response.status_code}")
                continue
                
            # 验证内容是否为纯文本
            if not response.text.isprintable():
                print(f"警告: {url} 返回的内容可能不是有效的文本")
                continue
                
            for line in response.text.splitlines():
                line = line.strip()
                if line and not line.startswith(('#', '!')):
                    if line.startswith('HOST'):
                        line = 'DOMAIN' + line[4:]
                    rules.add(line)
            
            print(f"成功从 {url} 获取规则")
            
        except Exception as e:
            print(f"处理 {url} 时发生错误: {str(e)}")
    
    if rules:
        os.makedirs('rules', exist_ok=True)
        try:
            with open('rules/game_list.text', 'w', encoding='utf-8') as f:
                f.write(f'# 更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'# 规则数量: {len(rules)}\n\n')
                f.write('\n'.join(sorted(rules)))
            print(f"\n成功保存 {len(rules)} 条规则")
        except Exception as e:
            print(f"保存文件时发生错误: {str(e)}")
    else:
        print("\n警告: 没有获取到任何规则")

if __name__ == '__main__':
    fetch_and_save_rules()
