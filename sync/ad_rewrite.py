import os
import requests
import datetime
from datetime import timedelta
import git
from pathlib import Path
import re

# 配置项
REPO_PATH = "ad"
REWRITE_DIR = "rewrite"
OUTPUT_FILE = "ad_rewrite.conf"
README_PATH = "README-rewrite.md"

# 规则源列表
REWRITE_SOURCES = {
    "阻止常见的 HTTPDNS 服务器": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/%E6%8B%A6%E6%88%AAHTTPDNS.official.sgmodule",
    "广告平台拦截器": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%B9%BF%E5%91%8A%E5%B9%B3%E5%8F%B0%E6%8B%A6%E6%88%AA%E5%99%A8.sgmodule",
    "whatshubs开屏屏蔽": "https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/manual/rewrite/adultraplus.conf",
    "whatshub微信屏蔽": "https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/manual/rewrite/wechatad.conf",
    "whatshubAdBlock": "https://raw.githubusercontent.com/deezertidal/QuantumultX-Rewrite/refs/heads/master/rewrite/AdBlock.conf",
    "surge去广告": "https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/manual/rewrite/surge.config",
    "chxm去广告": "https://raw.githubusercontent.com/chxm1023/Advertising/main/AppAd.conf",
    "墨鱼微信广告": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/Applet.conf",
    "墨鱼去开屏V2.0": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/StartUp.conf",
    "广告拦截精简版": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/QuantumultX/AdvertisingLite/AdvertisingLite.conf",
    "去广告重写": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/chongxie.txt",
    "整合广告拦截": "https://raw.githubusercontent.com/weiyesing/QuantumultX/GenMuLu/ChongXieGuiZe/QuGuangGao/To%20advertise.conf",
    "YouTube去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/Youtube%20%E5%8E%BB%E5%B9%BF%E5%91%8A%20(%E4%B8%8D%E5%8E%BB%E8%B4%B4%E7%89%87).official.sgmodule",
    "YouTube双语翻译": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Beta/YouTube%E7%BF%BB%E8%AF%91.beta.sgmodule",
    "小红书去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%B0%8F%E7%BA%A2%E4%B9%A6%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "微博去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%BE%AE%E5%8D%9A%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "小黑盒去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%B0%8F%E9%BB%91%E7%9B%92%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "微信小程序去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%BE%AE%E4%BF%A1%E5%B0%8F%E7%A8%8B%E5%BA%8F%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "百度网页去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E7%99%BE%E5%BA%A6%E6%90%9C%E7%B4%A2%E7%BD%91%E9%A1%B5%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "网易云音乐去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E7%BD%91%E6%98%93%E4%BA%91%E9%9F%B3%E4%B9%90%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "拼多多去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E6%8B%BC%E5%A4%9A%E5%A4%9A%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "Google搜索重定向": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Google%E9%87%8D%E5%AE%9A%E5%90%91.sgmodule",
    "京东比价": "https://raw.githubusercontent.com/mw418/Loon/main/script/jd_price.js",
    "汤头条解锁": "https://raw.githubusercontent.com/Yu9191/Rewrite/main/lsp/Tangtoutiao.js",
    "1998解锁": "https://raw.githubusercontent.com/Yu9191/Rewrite/main/1998.js"
}

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.datetime.utcnow()
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time

def setup_directory():
    """创建必要的目录"""
    Path(os.path.join(REPO_PATH, REWRITE_DIR)).mkdir(parents=True, exist_ok=True)

def parse_rule_type(line):
    """判断规则类型"""
    if not line or line.startswith('#'):
        return None
    
    line = line.strip()
    
    if 'hostname' in line.lower():
        return 'MITM'
    elif line.startswith('AND,') or line.startswith('OR,') or line.startswith('NOT,') or line.startswith('DOMAIN,') or line.startswith('DOMAIN-SUFFIX,') or line.startswith('DOMAIN-KEYWORD,') or line.startswith('IP-CIDR,') or line.startswith('IP-CIDR6,') or line.startswith('URL-REGEX,'):
        return 'RULE'
    elif 'url script-' in line:
        return 'SCRIPT'
    elif 'url reject' in line or 'url 302' in line:
        return 'URL REWRITE'
    elif line.startswith('^'):
        return 'REWRITE'
    elif line.startswith('force-http-engine-hosts') or line.startswith('skip-proxy'):
        return 'GENERAL'
    else:
        return 'RULE'

def extract_hostnames(line):
    """从 MITM 规则中提取 hostname"""
    if 'hostname' in line.lower():
        if '=' in line:
            hostnames = line.split('=')[1].strip()
            hostnames = hostnames.replace('%APPEND%', '').strip()
            return [h.strip() for h in hostnames.split(',') if h.strip()]
    return []

def parse_rules(content):
    """解析规则内容"""
    sections = {
        'GENERAL': set(),
        'RULE': set(),
        'URL REWRITE': set(),
        'MITM': set(),
        'REWRITE': set(),
        'SCRIPT': set()
    }
    
    current_section = None
    
    for line in content.splitlines():
        line = line.strip()
        
        # 跳过空行和注释
        if not line or line.startswith('#'):
            continue
            
        # 检查是否是新节
        if line.startswith('[') and line.endswith(']'):
            current_section = line[1:-1].upper()
            continue
            
        # 确定规则类型
        rule_type = parse_rule_type(line)
        if rule_type:
            sections[rule_type].add(line)

    return sections

def merge_rules(all_rules, new_rules):
    """合并规则集合"""
    for section, rules in new_rules.items():
        all_rules[section].update(rules)

def download_and_merge_rules():
    """下载并合并重写规则"""
    beijing_time = get_beijing_time()
    header = f"""# 广告拦截重写规则合集
# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in REWRITE_SOURCES.items()])}

"""
    
    # 存储所有规则
    all_rules = {
        'GENERAL': set(),
        'RULE': set(),
        'URL REWRITE': set(),
        'MITM': set(),
        'REWRITE': set(),
        'SCRIPT': set()
    }
    
    all_hostnames = set()

    for name, url in REWRITE_SOURCES.items():
        try:
            print(f"Downloading rules from {name}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text
            
            # 解析规则
            sections = parse_rules(content)
            
            # 处理 MITM hostname
            for rule in sections['MITM']:
                all_hostnames.update(extract_hostnames(rule))
            
            # 合并其他规则
            merge_rules(all_rules, sections)

        except Exception as e:
            print(f"Error downloading {name}: {str(e)}")

    # 生成最终内容
    final_content = header
    
    # 按节输出规则
    for section, rules in all_rules.items():
        if rules and section != 'MITM':
            final_content += f"\n[{section}]\n"
            final_content += '\n'.join(sorted(rules)) + '\n'
    
    # 输出 MITM 配置
    if all_hostnames:
        final_content += "\n[MITM]\n"
        final_content += f"hostname = {', '.join(sorted(all_hostnames))}\n"

    # 写入文件
    output_path = os.path.join(REPO_PATH, REWRITE_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    rule_count = sum(len(rules) for section, rules in all_rules.items() if section != 'MITM')
    hostname_count = len(all_hostnames)
    script_count = len(all_rules['SCRIPT'])
    
    print(f"Successfully merged {rule_count} unique rules, {hostname_count} hostnames, and {script_count} scripts to {OUTPUT_FILE}")
    return rule_count, hostname_count, script_count

def update_readme(rule_count, hostname_count, script_count):
    """更新 README.md"""
    beijing_time = get_beijing_time()
    content = f"""# 广告拦截重写规则合集

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 规则说明
本重写规则集合并自各个开源规则，去除重复规则。
- 当前规则数量：{rule_count}
- 当前 hostname 数量：{hostname_count}
- 当前 脚本 数量：{script_count}

## 规则来源
{chr(10).join([f'- {name}: {url}' for name, url in REWRITE_SOURCES.items()])}

## 使用方法
规则文件地址: https://raw.githubusercontent.com/[你的用户名]/[仓库名]/main/rewrite/ad_rewrite.conf
"""
    
    with open(os.path.join(REPO_PATH, README_PATH), 'w', encoding='utf-8') as f:
        f.write(content)

def git_push():
    """提交更改到 Git"""
    try:
        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)
        beijing_time = get_beijing_time()
        repo.index.commit(f"Update rewrite rules: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
        origin = repo.remote(name='origin')
        origin.push()
        print("Successfully pushed to repository")
    except Exception as e:
        print(f"Error pushing to repository: {str(e)}")

def main():
    setup_directory()
    rule_count, hostname_count, script_count = download_and_merge_rules()
    update_readme(rule_count, hostname_count, script_count)
    git_push()

if __name__ == "__main__":
    main()
