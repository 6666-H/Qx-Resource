import os
import requests
import datetime
from datetime import timedelta
import git
from pathlib import Path

# 配置项
REPO_PATH = "Rewrite"
REWRITE_DIR = "Advertising"
OUTPUT_FILE = "Ad.conf"
README_PATH = "README_Rewrite.md"

# 规则源列表
REWRITE_SOURCES = {
    "阻止常见的 HTTPDNS 服务器": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/%E6%8B%A6%E6%88%AAHTTPDNS.official.sgmodule",
    "广告平台拦截器": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%B9%BF%E5%91%8A%E5%B9%B3%E5%8F%B0%E6%8B%A6%E6%88%AA%E5%99%A8.sgmodule",
    "whatshubs开屏屏蔽": "https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/manual/rewrite/adultraplus.conf",
    "whatshubAdBlock":"https://raw.githubusercontent.com/deezertidal/QuantumultX-Rewrite/refs/heads/master/rewrite/AdBlock.conf",
    "chxm去广告": "https://raw.githubusercontent.com/chxm1023/Advertising/main/AppAd.conf",
    "墨鱼去开屏V2.0": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/StartUp.conf",
    "广告拦截精简版": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/QuantumultX/AdvertisingLite/AdvertisingLite.conf",
    "去广告重写": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/chongxie.txt",
    "整合广告拦截": "https://raw.githubusercontent.com/weiyesing/QuantumultX/GenMuLu/ChongXieGuiZe/QuGuangGao/To%20advertise.conf",
    "surge去广告":"https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/%E6%96%B0%E6%89%8B%E5%8F%8B%E5%A5%BD%E3%81%AE%E5%8E%BB%E5%B9%BF%E5%91%8A%E9%9B%86%E5%90%88.official.sgmodule",
    "YouTube去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/Youtube%20%E5%8E%BB%E5%B9%BF%E5%91%8A%20(%E4%B8%8D%E5%8E%BB%E8%B4%B4%E7%89%87).official.sgmodule",
    "YouTube双语翻译": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Beta/YouTube%E7%BF%BB%E8%AF%91.beta.sgmodule",
    "小红书去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%B0%8F%E7%BA%A2%E4%B9%A6%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "微博去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%BE%AE%E5%8D%9A%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "小黑盒去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%B0%8F%E9%BB%91%E7%9B%92%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "Google搜索重定向":"https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Google%E9%87%8D%E5%AE%9A%E5%90%91.sgmodule",
    "网易云音乐去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E7%BD%91%E6%98%93%E4%BA%91%E9%9F%B3%E4%B9%90%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "京东比价": "https://raw.githubusercontent.com/mw418/Loon/main/script/jd_price.js",
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

def normalize_rule(rule):
    """标准化规则，移除不同的reject后缀，只保留URL部分"""
    if '^' not in rule or 'url' not in rule:
        return rule
    parts = rule.split('url')
    url_pattern = parts[0].strip()
    return url_pattern

def get_best_reject_type(rules):
    """从多个相同URL pattern的规则中选择最佳的reject类型"""
    reject_priority = {
        'reject-dict': 4,
        'reject-200': 3,
        'reject-img': 2,
        'reject': 1
    }
    
    best_reject = 'reject'
    max_priority = 0
    
    for rule in rules:
        if 'url' not in rule:
            continue
        reject_type = rule.split('url')[1].strip()
        priority = reject_priority.get(reject_type, 0)
        if priority > max_priority:
            max_priority = priority
            best_reject = reject_type
            
    return best_reject

def merge_duplicate_rules(rules):
    """合并重复规则并记录日志"""
    rule_dict = {}
    for rule in rules:
        url_pattern = normalize_rule(rule)
        if url_pattern not in rule_dict:
            rule_dict[url_pattern] = set()
        rule_dict[url_pattern].add(rule)
    
    merged_rules = set()
    for url_pattern, rule_set in rule_dict.items():
        if len(rule_set) > 1:
            print(f"Found duplicate rules for pattern: {url_pattern}")
            print(f"Original rules: {rule_set}")
            best_reject = get_best_reject_type(rule_set)
            merged_rule = f"{url_pattern} url {best_reject}"
            print(f"Merged into: {merged_rule}")
            merged_rules.add(merged_rule)
        else:
            merged_rules.add(rule_set.pop())
    
    return merged_rules

def download_and_merge_rules():
    """下载并合并重写规则"""
    beijing_time = get_beijing_time()
    header = f"""#!name = 自建重写规则合集
#!desc = 自建重写规则合集     
# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in REWRITE_SOURCES.items()])}

"""

    # 用于存储所有规则
    all_rules = set()
    # 用于存储所有 hostname
    all_hostnames = set()
    # 用于存储其它脚本规则
    other_rules = []
    # 用于存储分类规则
    classified_rules = {}

    for name, url in REWRITE_SOURCES.items():
        try:
            print(f"Downloading rules from {name}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text

            current_tag = None
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if 'hostname' in line.lower():
                    if '=' in line:
                        hostnames = line.split('=')[1].strip()
                        hostnames = hostnames.replace('%APPEND%', '').strip()
                        all_hostnames.update(h.strip() for h in hostnames.split(',') if h.strip())
                    continue

                if line.startswith('[') and line.endswith(']'):
                    current_tag = line[1:-1].upper()
                    tag_with_brackets = f'[{current_tag}]'
                    if tag_with_brackets not in classified_rules:
                        classified_rules[tag_with_brackets] = set()
                    continue

                if current_tag:
                    if current_tag.upper() != 'MITM':
                        classified_rules[f'[{current_tag}]'].add(line)
                    continue

                if line.startswith('^'):
                    all_rules.add(line)
                elif line.endswith('.js'):
                    other_rules.append(line)

        except Exception as e:
            print(f"Error downloading {name}: {str(e)}")

    # 合并重复规则
    merged_rules = merge_duplicate_rules(all_rules)

    # 组合最终内容
    final_content = header

    # 输出分类规则
    for tag, rules in classified_rules.items():
        if rules and tag.upper() != '[MITM]':
            final_content += f"\n{tag}\n"
            final_content += '\n'.join(sorted(rules)) + '\n'

    # 输出合并后的所有 hostname
    if all_hostnames:
        final_content += "\n[MITM]\n"
        final_content += f"hostname = {', '.join(sorted(all_hostnames))}\n"

    # 输出合并后的规则
    if merged_rules:
        final_content += "\n[REWRITE]\n"
        final_content += '\n'.join(sorted(merged_rules)) + '\n'

    # 输出其它脚本规则
    if other_rules:
        final_content += "\n[SCRIPT]\n"
        final_content += '\n'.join(sorted(other_rules)) + '\n'

    # 写入合并后的文件
    output_path = os.path.join(REPO_PATH, REWRITE_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)

    rule_count = len(merged_rules)
    hostname_count = len(all_hostnames)
    script_count = len(other_rules)
    print(f"Successfully merged {rule_count} unique rules, {hostname_count} hostnames, and {script_count} scripts to {OUTPUT_FILE}")
    return rule_count, hostname_count, script_count

def update_readme(rule_count, hostname_count, script_count):
    """更新 README.md"""
    beijing_time = get_beijing_time()
    content = f"""#!name = 自建重写规则合集

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
