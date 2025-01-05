import os
import requests
import datetime
from datetime import timedelta
import git
from pathlib import Path

# 配置项
REPO_PATH = "ad"
FILTER_DIR = "filter"
OUTPUT_FILE = "ad_filter.list"
README_PATH = "README-rule.md"

# 分流规则源列表
FILTER_SOURCES = {
    "AD_ALL": "https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/manual/rule/Ad_All.list",
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

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.datetime.utcnow()
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time

def setup_directory():
    """创建必要的目录"""
    Path(os.path.join(REPO_PATH, FILTER_DIR)).mkdir(parents=True, exist_ok=True)

def download_and_merge_rules():
    """下载并合并分流规则"""
    beijing_time = get_beijing_time()
    header = f"""# 广告拦截分流规则合集
# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in FILTER_SOURCES.items()])}

"""
    
    # 用于存储去重后的规则
    unique_rules = set()
    # 用于存储所有注释
    comments = []

    # 规则格式转换映射
    replacements = {
        'HOST-SUFFIX,': 'DOMAIN-SUFFIX,',
        'HOST,': 'DOMAIN,',
        'HOST-KEYWORD,': 'DOMAIN-KEYWORD,',
        'IP-CIDR,': 'IP-CIDR,',
        'IP6-CIDR,': 'IP6-CIDR,',
        'IP6-CIDR,': 'IP-CIDR6,' 
    }

    for name, url in FILTER_SOURCES.items():
        try:
            print(f"Downloading rules from {name}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text

            comments.append(f"\n# ======== {name} ========")
            
            # 处理每一行
            for line in content.splitlines():
                line = line.strip()
                # 跳过空行
                if not line:
                    continue
                
                # 保存重要注释行，跳过域名标记注释
                if line.startswith('#'):
                    if not line.startswith('# [') and not line.endswith(']'):
                        comments.append(line)
                    continue
                
                # 规则格式转换
                for old, new in replacements.items():
                    line = line.replace(old, new)
                
                # 添加到去重集合
                if any(line.startswith(prefix) for prefix in ['DOMAIN', 'IP-CIDR', 'IP6-CIDR', 'USER-AGENT']):
                    unique_rules.add(line)

        except Exception as e:
            print(f"Error downloading {name}: {str(e)}")

    # 组合最终内容
    final_content = header
    final_content += "\n".join(comments)
    final_content += "\n\n# ======== 去重后的规则 ========\n"
    final_content += '\n'.join(sorted(unique_rules))

    # 写入合并后的文件
    output_path = os.path.join(REPO_PATH, FILTER_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"Successfully merged {len(unique_rules)} unique rules to {OUTPUT_FILE}")
    return len(unique_rules)

def update_readme(rule_count):
    """更新 README.md"""
    beijing_time = get_beijing_time()
    content = f"""# 广告拦截分流规则合集

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 规则说明
本规则集合并自各个开源规则，将 HOST 类规则统一转换为 DOMAIN 格式。
当前规则数量：{rule_count}

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
        beijing_time = get_beijing_time()
        repo.index.commit(f"Update rules: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
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
