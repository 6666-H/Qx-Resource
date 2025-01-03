import os
import requests
import datetime
import git
from pathlib import Path

# 配置项
REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
REWRITE_DIR = "rewrite"
OUTPUT_FILE = "ad_rewrite.conf"
README_PATH = "README-rewrite.md"

# Headers 配置
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# 规则源列表
REWRITE_SOURCES = {
    "whatshubs开屏屏蔽": "https://whatshub.top/rewrite/adultraplus.conf"
}

def setup_directory():
    """创建必要的目录"""
    try:
        Path(os.path.join(REPO_PATH, REWRITE_DIR)).mkdir(parents=True, exist_ok=True)
        print(f"Successfully created directory: {os.path.join(REPO_PATH, REWRITE_DIR)}")
    except Exception as e:
        print(f"Error creating directory: {str(e)}")

def download_and_merge_rules():
    """下载并合并重写规则"""
    merged_content = f"""# 广告拦截重写规则合集
# 更新时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in REWRITE_SOURCES.items()])}

"""

    for name, url in REWRITE_SOURCES.items():
        try:
            print(f"Downloading rules from {name}...")
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
            response.raise_for_status()
            content = response.text

            # 添加分隔符和源内容
            merged_content += f"\n# ======== {name} ========\n"
            merged_content += content + "\n"
            print(f"Successfully downloaded rules from {name}")

        except requests.exceptions.RequestException as e:
            print(f"Error downloading {name}: {str(e)}")
            continue

    try:
        # 写入合并后的文件
        output_path = os.path.join(REPO_PATH, REWRITE_DIR, OUTPUT_FILE)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(merged_content)
        print(f"Successfully merged rules to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error writing merged rules: {str(e)}")

def update_readme():
    """更新 README.md"""
    try:
        content = f"""# 广告拦截重写规则合集

## 更新时间
{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 规则说明
本重写规则集合并自各个开源规则，保持原始格式不变。

## 规则来源
{chr(10).join([f'- {name}: {url}' for name, url in REWRITE_SOURCES.items()])}
"""
        
        with open(os.path.join(REPO_PATH, README_PATH), 'w', encoding='utf-8') as f:
            f.write(content)
        print("Successfully updated README")
    except Exception as e:
        print(f"Error updating README: {str(e)}")

def git_push():
    """提交更改到 Git"""
    try:
        repo = git.Repo(REPO_PATH)
        # 设置 Git 用户信息
        repo.config_writer().set_value("user", "name", "GitHub Actions").release()
        repo.config_writer().set_value("user", "email", "actions@github.com").release()
        
        if repo.is_dirty(untracked_files=True):
            repo.git.add(all=True)
            commit_message = f"Update rewrite rules: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            repo.index.commit(commit_message)
            origin = repo.remote(name='origin')
            origin.push()
            print("Successfully pushed to repository")
        else:
            print("No changes to commit")
    except Exception as e:
        print(f"Error pushing to repository: {str(e)}")

def main():
    print("Starting script execution...")
    print(f"Working directory: {os.getcwd()}")
    print(f"Repository path: {REPO_PATH}")
    
    try:
        setup_directory()
        download_and_merge_rules()
        update_readme()
        git_push()
        print("Script execution completed successfully")
    except Exception as e:
        print(f"Error during script execution: {str(e)}")
    finally:
        print("Script execution finished")

if __name__ == "__main__":
    main()
