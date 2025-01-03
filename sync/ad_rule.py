import os
import requests
import datetime
import git
from pathlib import Path

# 配置项
REPO_PATH = "ad"
FILTER_DIR = "filter"
OUTPUT_FILE = "ad_filter.list"
README_PATH = "README-rule.md"

# 分流规则源列表
FILTER_SOURCES = {
    "AntiAD": "https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/manual/rule/AntiAD.list",
	"Adrules": "https://adrules.top/adrules.list"
    "Ads_ml": "https://github.com/thNylHx/Tools/raw/main/Ruleset/Surge/Block/Ads_ml.list",
    "Reject_Rule": "https://raw.githubusercontent.com/Code-Dramatist/Rule_Actions/main/Reject_Rule/Reject_Rule.rule",
    "AdBlock": "https://raw.githubusercontent.com/zqzess/rule_for_quantumultX/refs/heads/master/QuantumultX/rules/AdBlock.list",
    "AdvertisingLite": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/QuantumultX/AdvertisingLite/AdvertisingLite.list",
    "Reject": "https://raw.githubusercontent.com/Irrucky/Tool/main/Surge/rules/Reject.list",
    "SKK_Reject": "https://ruleset.skk.moe/List/non_ip/reject.conf",
    "Dler_AdBlock": "https://raw.githubusercontent.com/dler-io/Rules/refs/heads/main/Surge/Surge%203/Provider/AdBlock.list",
    "SKK_IP_Reject": "https://ruleset.skk.moe/List/ip/reject.conf",
    "NobyDa_AdRule": "https://raw.githubusercontent.com/NobyDa/Script/master/QuantumultX/AdRule.list"
}

def setup_directory():
    """创建必要的目录"""
    Path(os.path.join(REPO_PATH, FILTER_DIR)).mkdir(parents=True, exist_ok=True)

def download_and_merge_rules():
    """下载并合并分流规则"""
    merged_content = f"""# 广告拦截分流规则合集
# 更新时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in FILTER_SOURCES.items()])}

"""

    for name, url in FILTER_SOURCES.items():
        try:
            print(f"Downloading rules from {name}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text

            # 添加分隔符和源内容
            merged_content += f"\n# ======== {name} ========\n"
            merged_content += content + "\n"

        except Exception as e:
            print(f"Error downloading {name}: {str(e)}")

    # 规则格式转换
    replacements = {
        'HOST-SUFFIX,': 'DOMAIN-SUFFIX,',
        'HOST,': 'DOMAIN,',
        'HOST-KEYWORD,': 'DOMAIN-KEYWORD,',
        'IP-CIDR,': 'IP-CIDR,',
        'IP6-CIDR,': 'IP6-CIDR,'
    }
    
    # 进行全局替换
    for old, new in replacements.items():
        merged_content = merged_content.replace(old, new)

    # 写入合并后的文件
    output_path = os.path.join(REPO_PATH, FILTER_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(merged_content)
    
    print(f"Successfully merged rules to {OUTPUT_FILE}")

def update_readme():
    """更新 README.md"""
    content = f"""# 广告拦截分流规则合集

## 更新时间
{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 规则说明
本规则集合并自各个开源规则，将 HOST 类规则统一转换为 DOMAIN 格式。

## 规则来源
{chr(10).join([f'- {name}: {url}' for name, url in FILTER_SOURCES.items()])}

## 使用方法
规则文件地址: https://raw.githubusercontent.com/[你的用户名]/[仓库名]/main/filter/ad_filter.list
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
