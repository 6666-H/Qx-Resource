import os
import requests
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def fetch_and_save_rules():
    urls = {
        'Steam': 'https://whatshub.top/rule/Steam.list',
        'Epic': 'https://whatshub.top/rule/Epic.list',
        'Nintendo': 'https://whatshub.top/rule/Nintendo.list',
        'Sony': 'https://whatshub.top/rule/Sony.list'
    }
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    os.makedirs('rules', exist_ok=True)
    total_rules = 0
    
    with open('rules/game_list.text', 'w', encoding='utf-8') as f:
        f.write(f'# 更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        
        for name, url in urls.items():
            try:
                print(f"正在获取 {name} 规则...")
                response = requests.get(url, headers=headers, verify=False, timeout=10)
                rules = []
                
                for line in response.text.splitlines():
                    line = line.strip()
                    if line and not line.startswith(('#', '!')):
                        if line.startswith('HOST'):
                            line = 'DOMAIN' + line[4:]
                        rules.append(line)
                
                # 写入当前来源的规则
                f.write(f'\n# {name} Rules ({len(rules)} rules)\n')
                f.write('\n'.join(rules) + '\n')
                total_rules += len(rules)
                
                print(f"已添加 {len(rules)} 条 {name} 规则")
                
            except Exception as e:
                print(f"获取 {name} 规则失败: {e}")
                f.write(f'\n# Error fetching {name} rules: {str(e)}\n')
    
        # 在文件开头附近添加总规则数
        with open('rules/game_list.text', 'r', encoding='utf-8') as f:
            content = f.read()
        with open('rules/game_list.text', 'w', encoding='utf-8') as f:
            f.write(content.replace('# 更新时间', f'# 更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n# 总规则数: {total_rules}'))
    
    print(f"\n所有规则已保存，共 {total_rules} 条规则")

if __name__ == '__main__':
    fetch_and_save_rules()
