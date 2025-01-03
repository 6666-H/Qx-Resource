import os
import requests
import datetime
import git
from pathlib import Path

# 配置项
REPO_PATH = "ad"
FILTER_DIR = "filter"
OUTPUT_FILE = "ad_filter.list"
README_PATH = "README.md"

# 分流规则源列表
FILTER_SOURCES = {
    "AntiAD": "https://whatshub.top/rule/AntiAD.list",
    "Ads_ml": "https://github.com/thNylHx/Tools/raw/main/Ruleset/Surge/Block/Ads_ml.list",
    "Reject_Rule": "https://raw.githubusercontent.com/Code-Dramatist/Rule_Actions/main/Reject_Rule/Reject_Rule.rule",
    "AdBlock": "https://raw.githubusercontent.com/zqzess/rule_for_quantumultX/refs/heads/master/QuantumultX/rules/AdBlock.list",
    "AdvertisingLite": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/QuantumultX/AdvertisingLite/AdvertisingLite.list",
    "Reject": "https://raw.githubusercontent.com/Irrucky/Tool/main/Surge/rules/Reject.list",
    "SKK_Reject": "https://ruleset.skk.moe/List/non_ip/reject.conf",
    "Dler_AdBlock": "https://raw.githubusercontent.com/dler-io/Rules/refs/heads/main/Surge/Surge%203/Provider/AdBlock.list",
    "SKK_IP_Reject": "https://ruleset.skk.moe/List/ip/reject.conf",
    "NobyDa_AdRule": "https://raw.githubusercontent.com/NobyDa/Script/master/QuantumultX/AdRule.list",
    "Adrules": "https://adrules.top/adrules.list"
}

def setup_directory():
    """创建必要的目录"""
    Path(os.path.join(REPO_PATH, FILTER_DIR)).mkdir(parents=True, exist_ok=True)

def clean_rule_line(line):
    """清理和标准化规则行"""
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    
    # 转换规则格式
    replacements = {
        'HOST-SUFFIX,': 'DOMAIN-SUFFIX,',
        'HOST,': 'DOMAIN,',
        'HOST-KEYWORD,': 'DOMAIN-KEYWORD,',
        'IP-CIDR,': 'IP-CIDR,',
        'IP6-CIDR,': 'IP6-CIDR,'
    }
    
    # 检查并转换规则格式
    for old, new in replacements.items():
        if line.startswith(old):
            line = line.replace(old, new)
            break
    
    # 处理不带类型前缀的域名（假设它们是 DOMAIN 类型）
    if not any(line.startswith(prefix) for prefix in ['DOMAIN', 'IP-CIDR', 'IP6-CIDR']):
        if ',' in line:
            domain = line.split(',')[0]
            line = f"DOMAIN,{domain},reject"
        else:
            line = f"DOMAIN,{line},reject"
    
    # 确保规则以 reject 结尾
    if not line.lower().endswith(',reject'):
        line = f"{line},reject"
    
    return line

def download_and_merge_rules():
    """下载并合并分流规则"""
    merged_content = f"""# 广告拦截分流规则合集
# 更新时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in FILTER_SOURCES.items()])}

"""
    # 用于去重的集合
    unique_rules = set()

    for name, url in FILTER_SOURCES.items():
        try:
            print(f"Downloading rules from {name}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text

            # 添加分隔符
            merged_content += f"\n# ======== {name} ========\n"
            
            # 处理内容
            lines = content.split('\n')
            for line in lines:
                cleaned_line = clean_rule_line(line)
                if cleaned_line and cleaned_line not in unique_rules:
                    unique_rules.add(cleaned_line)
                    merged_content += cleaned_line + '\n'

        except Exception as e:
            print(f"Error downloading {name}: {str(e)}")

    # 写入合并后的文件
    output_path = os.path.join(REPO_PATH, FILTER_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(merged_content)
    
    print(f"Successfully merged {len(unique_rules)} unique rules to {OUTPUT_FILE}")

def update_readme():
    """更新 README.md"""
    content = f"""# 广告拦截分流规则合集

## 更新时间
{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 规则说明
本规则集合并自各个开源规则，主要用于广告拦截。
已将规则统一为 Surge 格式，可兼容 Surge、Quantumult X、Clash 等。

## 规则来源
{chr(10).join([f'- {name}: {url}' for name, url in FILTER_SOURCES.items()])}

## 使用方法
规则文件地址: https://raw.githubusercontent.com/[你的用户名]/[仓库名]/main/filter/ad_filter.list

## 规则统计
合并规则条数: {sum(1 for line in open(os.path.join(REPO_PATH, FILTER_DIR, OUTPUT_FILE)) if line.strip() and not line.startswith('#'))}
"""
    
    with open(os.path.join(REPO_PATH, README_PATH), 'w', encoding='utf-8') as f:
        f.write(content)

def git_push():
    """提交更改到 Git"""
    try:
        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)
        repo.index.commit(f"Update rules: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        origin = repo.remote(name='origin')
        origin.push()
        print("Successfully pushed to repository")
    except Exception as e:
        print(f"Error pushing to repository: {str(e)}")

def main():
    setup_directory()
    download_and_merge_rules()
    update_readme()
    git_push()

if __name__ == "__main__":
    main()
