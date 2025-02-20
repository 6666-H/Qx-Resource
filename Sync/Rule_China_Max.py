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

def clean_domain(domain):
    """清理域名，去除前导点和多余空格"""
    return domain.strip().lstrip('.')

def standardize_rule(line):
    """标准化规则格式"""
    if not line or line.startswith('#'):
        return None, None

    line = line.strip()

    # 处理不带前缀的域名
    if ',' not in line:
        return 'DOMAIN-SUFFIX', clean_domain(line)

    # 处理标准格式规则
    parts = line.split(',')
    rule_type = parts[0].upper()
    content = clean_domain(parts[1])

    # 规则类型转换
    type_map = {
        'HOST': 'DOMAIN',
        'HOST-SUFFIX': 'DOMAIN-SUFFIX',
        'HOST-KEYWORD': 'DOMAIN-KEYWORD',
        'HOST-WILDCARD': 'DOMAIN-WILDCARD'
    }
    rule_type = type_map.get(rule_type, rule_type)

    # 检查是否为 IPv6 地址段
    if rule_type == 'IP-CIDR' and ':' in content:
        rule_type = 'IP6-CIDR'
    
    # 对于IP类规则，保留规则类型但去除no-resolve选项
    if rule_type in ['IP-CIDR', 'IP6-CIDR', 'IP-ASN']:
        content = content.split(',')[0]  # 移除 no-resolve 等选项
        if rule_type == 'IP-CIDR' and '/' not in content:
            content = f"{content}/32"
        elif rule_type == 'IP6-CIDR' and '/' not in content:
            content = f"{content}/128"
        return rule_type, content

    return rule_type, content


def get_rule_priority(rule_type):
    """获取规则优先级"""
    priorities = {
        'DOMAIN': 1,
        'DOMAIN-SUFFIX': 2,
        'DOMAIN-WILDCARD': 3,
        'DOMAIN-KEYWORD': 4,
        'USER-AGENT': 5,
        'IP-CIDR': 6,
        'IP6-CIDR': 7,
        'IP-ASN': 8,
        'GEOIP': 9
    }
    return priorities.get(rule_type, 99)

def download_and_merge_rules():
    """下载并合并分流规则"""
    beijing_time = get_beijing_time()
    header = f"""# 国内分流规则合集
# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in FILTER_SOURCES.items()])}

"""
    
    # 存储规则的字典，用于去重和分类
    rules_dict = {
        'DOMAIN': set(),
        'DOMAIN-SUFFIX': set(),
        'DOMAIN-WILDCARD': set(),
        'DOMAIN-KEYWORD': set(),
        'USER-AGENT': set(),
        'IP-CIDR': set(),
        'IP6-CIDR': set(),
        'IP-ASN': set(),
        'GEOIP': set()
    }
    
    # 下载和处理规则
    for name, url in FILTER_SOURCES.items():
        try:
            print(f"Downloading rules from {name}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            for line in response.text.splitlines():
                rule_type, content = standardize_rule(line.strip())
                if content and rule_type in rules_dict:
                    rules_dict[rule_type].add(content)

        except Exception as e:
            print(f"Error downloading {name}: {str(e)}")

    # 写入合并后的文件
    output_path = os.path.join(REPO_PATH, FILTER_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        
        # 按照指定顺序写入规则
        rule_types = [
            'DOMAIN',
            'DOMAIN-SUFFIX',
            'DOMAIN-WILDCARD',
            'DOMAIN-KEYWORD',
            'USER-AGENT',
            'IP-CIDR',
            'IP6-CIDR',
            'IP-ASN',
            'GEOIP'
        ]
        
        for rule_type in rule_types:
            if rules_dict[rule_type]:
                f.write(f"\n# {rule_type}\n")
                for rule in sorted(rules_dict[rule_type]):
                    f.write(f"{rule_type},{rule}\n")
    
    total_rules = sum(len(rules) for rules in rules_dict.values())
    print(f"Successfully merged {total_rules} unique rules to {OUTPUT_FILE}")
    return total_rules

def update_readme(rule_count):
    """更新 README.md"""
    beijing_time = get_beijing_time()
    content = f"""# 国内分流规则合集

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 规则说明
本规则集合并自各个开源规则，统一转换为标准格式。
- 去除重复规则
- 统一规则格式
- 移除额外的选项（如 ChinaMax, no-resolve）
- 将不带前缀的域名默认设为 DOMAIN-SUFFIX
- 去除域名前的点(.)
当前规则数量：{rule_count}

## 规则来源
{chr(10).join([f'- {name}: {url}' for name, url in FILTER_SOURCES.items()])}

## 规则格式说明
- DOMAIN：完整域名匹配
- DOMAIN-SUFFIX：域名后缀匹配
- DOMAIN-WILDCARD：域名通配符匹配
- DOMAIN-KEYWORD：域名关键字匹配
- USER-AGENT：User-Agent匹配
- IP-CIDR：IPv4 地址段
- IP6-CIDR：IPv6 地址段
- IP-ASN：自治系统号码
- GEOIP：GeoIP数据库（国家/地区）匹配
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
