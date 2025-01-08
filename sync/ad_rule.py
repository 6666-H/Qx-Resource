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
WHITE_LIST_URL = "https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/ad/filter/white_list.text"

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

def clean_rule(line, replacements):
    """清理规则格式，去掉后缀"""
    # 跳过空行和注释
    if not line or line.startswith('#'):
        return None
        
    # 处理规则格式转换
    for old, new in replacements.items():
        line = line.replace(old, new)
    
    # 分割规则
    parts = line.split(',')
    if len(parts) >= 2:
        # 只保留规则类型和域名/IP部分
        return f"{parts[0]},{parts[1]}"
    return None

def get_white_list(replacements):
    """获取白名单规则"""
    try:
        response = requests.get(WHITE_LIST_URL, timeout=30)
        response.raise_for_status()
        white_list = set()
        for line in response.text.splitlines():
            cleaned_rule = clean_rule(line.strip(), replacements)
            if cleaned_rule:
                white_list.add(cleaned_rule)
        return white_list
    except Exception as e:
        print(f"Error downloading white list: {str(e)}")
        return set()

def download_and_merge_rules():
    """下载并合并分流规则"""
    beijing_time = get_beijing_time()
    header = f"""# 广告拦截分流规则合集
# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in FILTER_SOURCES.items()])}

"""
    
    unique_rules = set()
    comments = []

    # 规则格式转换映射
    replacements = {
        'HOST-SUFFIX,': 'DOMAIN-SUFFIX,',
        'HOST,': 'DOMAIN,',
        'HOST-KEYWORD,': 'DOMAIN-KEYWORD,',
        'IP-CIDR,': 'IP-CIDR,',
        'IP6-CIDR,': 'IP-CIDR6,',
        'IP6-CIDR,': 'IP-CIDR6,'
    }

    # 获取白名单
    white_list = get_white_list(replacements)
    print(f"Loaded {len(white_list)} white list rules")

    # 按规则类型分组
    rule_groups = {
        'DOMAIN-SUFFIX': [],
        'DOMAIN': [],
        'DOMAIN-KEYWORD': [],
        'IP-CIDR': [],
        'IP-CIDR6': [],
        'USER-AGENT': []
    }

    for name, url in FILTER_SOURCES.items():
        try:
            print(f"Downloading rules from {name}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text

            comments.append(f"\n# ======== {name} ========")
            
            for line in content.splitlines():
                # 清理规则格式（去掉后缀）
                cleaned_rule = clean_rule(line.strip(), replacements)
                if cleaned_rule and cleaned_rule not in white_list:
                    # 验证和分类规则
                    for prefix in rule_groups.keys():
                        if cleaned_rule.startswith(prefix):
                            unique_rules.add(cleaned_rule)
                            break

        except Exception as e:
            print(f"Error downloading {name}: {str(e)}")

    # 对规则进行分组
    for rule in unique_rules:
        for prefix in rule_groups.keys():
            if rule.startswith(prefix):
                rule_groups[prefix].append(rule)
                break

    # 组合最终内容
    final_content = header
    final_content += "\n".join(comments)
    final_content += "\n\n# ======== 去重后的规则 ========\n"
    
    # 按组添加规则
    for group_name, rules in rule_groups.items():
        if rules:
            final_content += f"\n# {group_name}\n"
            final_content += '\n'.join(sorted(rules))

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
