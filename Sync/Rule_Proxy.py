import os
import requests
import datetime
import time
import argparse
import git
from pathlib import Path
from datetime import timedelta

# 配置项
REPO_PATH = "Rule"
FILTER_DIR = "Proxy"
OUTPUT_FILE = "Proxy.list"

# 分流规则源列表（仅保留被墙服务）
FILTER_SOURCES = {
    "Google":     "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Surge/Google/Google.list",
    "Telegram":   "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Surge/Telegram/Telegram.list",
    "GitHub":     "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Surge/GitHub/GitHub.list",
    "Twitter":    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Surge/Twitter/Twitter.list",
    "Facebook":   "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Surge/Facebook/Facebook.list",
    "Instagram":  "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Surge/Instagram/Instagram.list",
    "Reddit":     "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Surge/Reddit/Reddit.list",
    "Discord":    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Surge/Discord/Discord.list",
    "YouTube":    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Surge/YouTube/YouTube.list"
}

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.datetime.utcnow()
    return utc_now + timedelta(hours=8)

def setup_directory():
    """创建必要的目录"""
    Path(os.path.join(REPO_PATH, FILTER_DIR)).mkdir(parents=True, exist_ok=True)

def fetch_with_retry(url, retries=3, delay=5):
    """带重试机制的请求下载"""
    headers = {
        "User-Agent": "Mozilla/5.0 (SurgeRuleBot/1.0)"
    }
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"[Retry {i+1}/{retries}] Failed to fetch {url}: {e}")
            time.sleep(delay)
    raise Exception(f"❌ Failed to download {url} after {retries} attempts.")

def download_and_merge_rules():
    """下载并合并所有规则"""
    beijing_time = get_beijing_time()
    all_rules = set()

    for name, url in FILTER_SOURCES.items():
        try:
            print(f"🔄 Downloading {name}...")
            content = fetch_with_retry(url)
            lines = [line.strip() for line in content.splitlines()
                     if line.strip() and not line.strip().startswith('#')]
            all_rules.update(lines)
        except Exception as e:
            print(f"⚠️ Error downloading {name}: {e}")

    final_rules = sorted(all_rules)

    header = f"""# 被墙服务分流规则合集
# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 来源：
# {'\n# '.join([f'{name}: {url}' for name, url in FILTER_SOURCES.items()])}

# 规则总数: {len(final_rules)}

"""

    output_path = os.path.join(REPO_PATH, FILTER_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8-sig') as f:  # BOM for UTF-8
        f.write(header + "\n".join(final_rules))

    print(f"✅ Successfully merged {len(final_rules)} rules to {OUTPUT_FILE}")
    return len(final_rules)

def git_push():
    """提交更改到 Git 仓库"""
    try:
        if not os.path.exists(os.path.join(REPO_PATH, '.git')):
            print("⚠️ Git repo not found, skipping push.")
            return
        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)
        commit_msg = f"Update rules: {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')} (北京时间)"
        repo.index.commit(commit_msg)
        repo.remote(name='origin').push()
        print("🚀 Successfully pushed to repository")
    except Exception as e:
        print(f"❌ Git push failed: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-push', action='store_true', help='Only download and merge rules, do not push to git')
    args = parser.parse_args()

    setup_directory()
    download_and_merge_rules()
    if not args.no_push:
        git_push()

if __name__ == "__main__":
    main()
