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
    # ... 其他源保持不变 ...
}

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.datetime.utcnow()
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time

def setup_directory():
    """创建必要的目录"""
    Path(os.path.join(REPO_PATH, REWRITE_DIR)).mkdir(parents=True, exist_ok=True)

def extract_domain_from_rule(rule):
    """从规则中提取域名"""
    try:
        # 匹配域名的正则表达式
        domain_pattern = r'https?:\/\/([^\/]+)'
        match = re.search(domain_pattern, rule)
        if match:
            return match.group(1)
        return None
    except:
        return None

def get_rule_priority(rule):
    """获取规则的优先级"""
    priorities = {
        'script-response-body': 5,
        'response-body': 4,
        'reject-200': 3,
        'reject-dict': 2,
        'reject': 1,
        '302': 1
    }
    
    for key, priority in priorities.items():
        if key in rule:
            return priority
    return 0

def should_replace_rule(old_rule, new_rule):
    """决定是否用新规则替换旧规则"""
    old_priority = get_rule_priority(old_rule)
    new_priority = get_rule_priority(new_rule)
    
    # 如果新规则优先级更高，则替换
    if new_priority > old_priority:
        return True
        
    # 如果优先级相同，选择更短的规则
    if new_priority == old_priority:
        return len(new_rule) < len(old_rule)
        
    return False

def dedup_rules(rules):
    """去重规则"""
    domain_rules = {}  # 用于存储每个域名对应的规则
    unique_rules = []  # 存储无法提取域名的规则
    
    for rule in rules:
        # 跳过空规则或注释
        if not rule or rule.startswith('#'):
            continue
            
        domain = extract_domain_from_rule(rule)
        if domain:
            if domain not in domain_rules:
                domain_rules[domain] = rule
            else:
                # 如果域名已存在，根据规则优先级决定是否替换
                if should_replace_rule(domain_rules[domain], rule):
                    domain_rules[domain] = rule
        else:
            # 对于无法提取域名的规则，直接保留
            unique_rules.append(rule)
    
    # 合并所有规则
    return sorted(list(domain_rules.values()) + unique_rules)

def download_and_merge_rules():
    """下载并合并重写规则"""
    beijing_time = get_beijing_time()
    header = f"""# 广告拦截重写规则合集
# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in REWRITE_SOURCES.items()])}

"""
    
    # 用于存储规则
    all_rules = set()
    all_hostnames = set()
    script_rules = []
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
                
                # 处理 hostname
                if 'hostname' in line.lower():
                    if '=' in line:
                        hostnames = line.split('=')[1].strip()
                        hostnames = hostnames.replace('%APPEND%', '').strip()
                        all_hostnames.update(h.strip() for h in hostnames.split(',') if h.strip())
                    continue
                
                # 处理标签
                if line.startswith('[') and line.endswith(']'):
                    current_tag = line[1:-1].upper()
                    tag_with_brackets = f'[{current_tag}]'
                    if tag_with_brackets not in classified_rules:
                        classified_rules[tag_with_brackets] = set()
                    continue

                # 处理规则
                if current_tag:
                    if current_tag.upper() != 'MITM':
                        classified_rules[f'[{current_tag}]'].add(line)
                elif '^' in line:
                    all_rules.add(line)
                elif line.endswith('.js'):
                    script_rules.append(line)

        except Exception as e:
            print(f"Error downloading {name}: {str(e)}")

    # 组合最终内容
    final_content = header
    
    # 输出分类规则
    for tag, rules in classified_rules.items():
        if rules and tag.upper() != '[MITM]':
            final_content += f"\n{tag}\n"
            deduped_rules = dedup_rules(rules)
            final_content += '\n'.join(sorted(deduped_rules)) + '\n'
    
    # 输出常规重写规则
    if all_rules:
        final_content += "\n[REWRITE]\n"
        deduped_rules = dedup_rules(all_rules)
        final_content += '\n'.join(sorted(deduped_rules)) + '\n'
    
    # 输出脚本规则
    if script_rules:
        final_content += "\n[SCRIPT]\n"
        deduped_scripts = dedup_rules(script_rules)
        final_content += '\n'.join(sorted(deduped_scripts)) + '\n'
    
    # 输出 hostname
    if all_hostnames:
        final_content += "\n[MITM]\n"
        final_content += f"hostname = {', '.join(sorted(all_hostnames))}\n"

    # 写入文件
    output_path = os.path.join(REPO_PATH, REWRITE_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    rule_count = len(all_rules)
    hostname_count = len(all_hostnames)
    script_count = len(script_rules)
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
