import os
import requests
import datetime
import git
from pathlib import Path

# 配置项
REPO_PATH = "ad"
REWRITE_DIR = "rewrite"
OUTPUT_FILE = "ad_rewrite.conf"
README_PATH = "README-rewrite.md"

# 规则源列表
REWRITE_SOURCES = {

    "whatshubs开屏屏蔽": "https://whatshub.top/rewrite/adultraplus.conf"
 
}

def setup_directory():
    """创建必要的目录"""
    Path(os.path.join(REPO_PATH, REWRITE_DIR)).mkdir(parents=True, exist_ok=True)

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
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text

            # 添加分隔符和源内容
            merged_content += f"\n# ======== {name} ========\n"
            merged_content += content + "\n"

        except Exception as e:
            print(f"Error downloading {name}: {str(e)}")

    # 写入合并后的文件
    output_path = os.path.join(REPO_PATH, REWRITE_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(merged_content)
    
    print(f"Successfully merged rules to {OUTPUT_FILE}")

def update_readme():
    """更新 README.md"""
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

def git_push():
    """提交更改到 Git"""
    try:
        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)
        repo.index.commit(f"Update rewrite rules: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
