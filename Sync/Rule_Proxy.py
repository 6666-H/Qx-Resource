import os
import requests
import datetime
from datetime import timedelta
import git
from pathlib import Path

# 配置项
REPO_PATH = "Rule"
FILTER_DIR = "Proxy"
OUTPUT_FILE = "Proxy.list"
README_PATH = "README_Ad.md"

FILTER_SOURCES = {
    "ADLite":"https://raw.githubusercontent.com/deezertidal/shadowrocket-rules/refs/heads/main/rule/ADLite.list",
    "AdvertisingLite": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/QuantumultX/AdvertisingLite/AdvertisingLite.list"
}

def get_beijing_time():
    return datetime.datetime.utcnow() + timedelta(hours=8)

def setup_directory():
    Path(os.path.join(REPO_PATH, FILTER_DIR)).mkdir(parents=True, exist_ok=True)

def get_white_list():
    try:
        response = requests.get(WHITE_LIST_URL, timeout=30)
        response.raise_for_status()
        return set(line.strip() for line in response.text.splitlines() if line.strip() and not line.startswith('#'))
    except Exception as e:
        print(f"Error downloading white list: {str(e)}")
        return set()

def download_and_merge_rules():
    beijing_time = get_beijing_time()
    white_list = get_white_list()
    rules = set()
    comments = []

    for name, url in FILTER_SOURCES.items():
        try:
            print(f"Downloading rules from {name}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text
            comments.append(f"\n# ======== {name} ========")
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith('#') and line not in white_list:
                    rules.add(line)
        except Exception as e:
            print(f"Error downloading {name}: {str(e)}")

    header = f"""# 广告拦截分流规则合集
# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in FILTER_SOURCES.items()])}

# 规则总数: {len(rules)}
"""

    output_path = os.path.join(REPO_PATH, FILTER_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header + '\n'.join(comments) + '\n\n# ======== 合并后的规则 ========\n')
        f.write('\n'.join(sorted(rules)))

    print(f"Successfully merged {len(rules)} unique rules to {OUTPUT_FILE}")
    return len(rules)

def update_readme(rule_count):
    beijing_time = get_beijing_time()
    content = f"""# 广告拦截分流规则合集

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 当前规则数量：{rule_count}

## 规则来源
{chr(10).join([f'- {name}: {url}' for name, url in FILTER_SOURCES.items()])}

## 规则地址
https://raw.githubusercontent.com/[你的用户名]/[仓库名]/main/Rule/Advertising/Ad.list
"""
    with open(os.path.join(REPO_PATH, README_PATH), 'w', encoding='utf-8') as f:
        f.write(content)

def git_push():
    try:
        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)
        repo.index.commit(f"Update rules: {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
        repo.remote(name='origin').push()
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
