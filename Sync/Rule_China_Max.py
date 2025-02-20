import os
import requests
import datetime
from datetime import timedelta
import git
from pathlib import Path

# 配置项
REPO_PATH = "Rule"
FILTER_DIR = "Direct"
OUTPUT_FILE = "China_Max.list"
README_PATH = "README.md"

FILTER_SOURCES = {
    "ChinaMax": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/ChinaMax/ChinaMax.list",
    "ChinaMax_2": "https://raw.githubusercontent.com/deezertidal/QuantumultX-Rewrite/refs/heads/master/rule/ChinaMax.list",
    "Direct_Rule": "https://raw.githubusercontent.com/Code-Dramatist/Rule_Actions/main/Direct_Rule/Direct_Rule.rule",
    "GEOIP": "https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/Manual/Rule/Direct.list"
}

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.datetime.utcnow()
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time

def setup_directory():
    """创建必要的目录"""
    Path(os.path.join(REPO_PATH, FILTER_DIR)).mkdir(parents=True, exist_ok=True)

def standardize_rule(line):
    """标准化规则格式"""
    if not line or line.startswith('#'):
        return None, None, None

    # 规则格式转换映射
    replacements = {
        'HOST-SUFFIX,': 'DOMAIN-SUFFIX,',
        'HOST,': 'DOMAIN,',
        'HOST-KEYWORD,': 'DOMAIN-KEYWORD,',
        'IP-CIDR,': 'IP-CIDR,',
        'IP6-CIDR,': 'IP6-CIDR,',
        'GEOIP,': 'GEOIP,'
    }
    
    line = line.strip()
    for old, new in replacements.items():
        line = line.replace(old, new)
    
    parts = line.split(',')
    if len(parts) < 2:
        return None, None, None

    rule_type = parts[0]
    content = parts[1]
    options = parts[2] if len(parts) > 2 else None

    return rule_type, content, options

def download_and_merge_rules():
    """下载并合并分流规则"""
    beijing_time = get_beijing_time()
    header = f"""# 国内分流规则合集
# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in FILTER_SOURCES.items()])}

"""
    
    # 存储规则的集合
    rules_set = set()
    
    # 下载和处理规则
    for name, url in FILTER_SOURCES.items():
        try:
            print(f"Downloading rules from {name}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            for line in response.text.splitlines():
                rule_type, content, options = standardize_rule(line.strip())
                if content:
                    rule = f"{rule_type},{content}"
                    if options:
                        rule += f",{options}"
                    rules_set.add(rule)

        except Exception as e:
            print(f"Error downloading {name}: {str(e)}")

    # 写入合并后的文件
    output_path = os.path.join(REPO_PATH, FILTER_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        for rule in sorted(rules_set):
            f.write(f"{rule}\n")
    
    return len(rules_set)

def update_readme(rule_count):
    """更新 README.md"""
    beijing_time = get_beijing_time()
    content = f"""# 国内分流规则合集

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 规则说明
本规则集合并自各个开源规则，统一转换为标准格式。
当前规则数量：{rule_count}

## 规则来源
{chr(10).join([f'- {name}: {url}' for name, url in FILTER_SOURCES.items()])}
"""
    
    with open(os.path.join(REPO_PATH, README_PATH), 'w', encoding='utf-8') as f:
        f.write(content)

def git_push():
    """提交更改到 Git"""
    try:
        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)
        beijing_time = get_beijing_time()
        repo.index.commit(f"更新规则: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
        origin = repo.remote(name='origin')
        origin.push()
        print("Successfully pushed to repository")
    except Exception as e:
        print(f"Error pushing to repository: {str(e)}")

def main():
    setup_directory()
    rule_count = download_and_merge_rules()
    update_readme(rule_count)
    git_push()

if __name__ == "__main__":
    main()
