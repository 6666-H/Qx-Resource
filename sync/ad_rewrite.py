import os
import requests
import datetime
import git
from pathlib import Path

# 配置项
REPO_PATH = "ad"
REWRITE_DIR = "rewrite"
OUTPUT_FILE = "ad_rewrite.conf"
README_PATH = "README.md"

# 规则源列表
REWRITE_SOURCES = {
    "whatshubs开屏屏蔽": "https://whatshub.top/rewrite/adultraplus.conf",
    "whatshub微信屏蔽": " https://whatshub.top/rewrite/wechatad.conf",
    "whatshub油管优化": "https://whatshub.top/rewrite/youtube.conf",
    "surge去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/%E6%96%B0%E6%89%8B%E5%8F%8B%E5%A5%BD%E3%81%AE%E5%8E%BB%E5%B9%BF%E5%91%8A%E9%9B%86%E5%90%88.official.sgmodule",
    "chxm去广告": "https://raw.githubusercontent.com/chxm1023/Advertising/main/AppAd.conf",
    "可莉微信屏蔽": "https://kelee.one/Tool/Loon/Plugin/WexinMiniPrograms_Remove_ads.plugin",
    "墨鱼微信广告": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/Applet.conf",
    "墨鱼去开屏V2.0": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/StartUp.conf",
    "广告拦截精简版": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/QuantumultX/AdvertisingLite/AdvertisingLite.conf",
    "去广告重写": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/chongxie.txt",
    "整合广告拦截": "https://raw.githubusercontent.com/DivineEngine/Profiles/master/Quantumult/Rewrite/Block/Advertising.conf"
}

def setup_directory():
    """创建必要的目录"""
    Path(os.path.join(REPO_PATH, REWRITE_DIR)).mkdir(parents=True, exist_ok=True)

def download_and_merge_rules():
    """下载并合并重写规则"""
    merged_content = f"""# 合并广告拦截重写规则
# 更新时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in REWRITE_SOURCES.items()])}

"""
    hostname_set = set()

    for name, url in REWRITE_SOURCES.items():
        try:
            print(f"Downloading rewrite rules from {name}...")
            response = requests.get(url)
            response.raise_for_status()
            content = response.text

            # 添加分隔符
            merged_content += f"\n# ======== {name} ========\n"
            
            # 处理内容
            lines = content.split('\n')
            for line in lines:
                # 跳过空行和注释行
                if not line.strip() or line.strip().startswith('#'):
                    continue
                
                # 提取 hostname
                if 'hostname' in line.lower():
                    hostnames = line.split('=')[-1].strip().split(',')
                    hostname_set.update([h.strip() for h in hostnames if h.strip()])
                    continue
                
                # 添加规则行
                merged_content += line + '\n'

        except Exception as e:
            print(f"Error downloading {name}: {str(e)}")

    # 添加合并后的 hostname
    if hostname_set:
        merged_content += "\n# 合并后的 Hostname\n"
        merged_content += "hostname = " + ", ".join(sorted(hostname_set))

    # 写入合并后的文件
    output_path = os.path.join(REPO_PATH, REWRITE_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(merged_content)
    
    print(f"Successfully merged rewrite rules to {OUTPUT_FILE}")

def update_readme():
    """更新 README.md"""
    content = f"""# QuantumultX 广告拦截重写规则合集

最后更新时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 重写规则源

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
