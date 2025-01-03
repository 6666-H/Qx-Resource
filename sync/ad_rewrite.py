import os
import requests
import datetime
from pathlib import Path

# 配置项
REPO_PATH = "ad"
REWRITE_DIR = "rewrite"
OUTPUT_FILE = "ad_rewrite.conf"
README_PATH = "README-rewrite.md"

# 规则源列表
REWRITE_SOURCES = {
    "whatshubs开屏屏蔽": "https://whatshub.top/rewrite/adultraplus.conf",
    "whatshub微信屏蔽": "https://whatshub.top/rewrite/wechatad.conf",
    "surge去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/%E6%96%B0%E6%89%8B%E5%8F%8B%E5%A5%BD%E3%81%AE%E5%8E%BB%E5%B9%BF%E5%91%8A%E9%9B%86%E5%90%88.official.sgmodule",
    "chxm去广告": "https://raw.githubusercontent.com/chxm1023/Advertising/main/AppAd.conf",
    "可莉微信屏蔽": "https://kelee.one/Tool/Loon/Plugin/WexinMiniPrograms_Remove_ads.plugin",
    "墨鱼微信广告": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/Applet.conf",
    "墨鱼去开屏V2.0": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/StartUp.conf",
    "广告拦截精简版": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/QuantumultX/AdvertisingLite/AdvertisingLite.conf",
    "去广告重写": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/chongxie.txt",
    "整合广告拦截": "https://raw.githubusercontent.com/DivineEngine/Profiles/master/Quantumult/Rewrite/Block/Advertising.conf",
    "whatshub油管优化": "https://whatshub.top/rewrite/youtube.conf"
}

def setup_directory():
    """创建必要的目录"""
    Path(REWRITE_DIR).mkdir(exist_ok=True)

def download_and_merge_rules():
    """下载并合并重写规则"""
    merged_content = f"""# 广告拦截重写规则合集
# 更新时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in REWRITE_SOURCES.items()])}

"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for name, url in REWRITE_SOURCES.items():
        try:
            print(f"Downloading rules from {name}...")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            content = response.text

            merged_content += f"\n# ======== {name} ========\n"
            merged_content += content + "\n"

        except Exception as e:
            print(f"Error downloading {name}: {str(e)}")

    output_path = Path(REWRITE_DIR) / OUTPUT_FILE
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
    
    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

def git_commit():
    """提交更改"""
    os.system('git config --local user.email "action@github.com"')
    os.system('git config --local user.name "GitHub Action"')
    os.system('git add .')
    os.system('git commit -m "Update rewrite rules: {}"'.format(
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
    os.system('git push')

def main():
    setup_directory()
    download_and_merge_rules()
    update_readme()
    git_commit()

if __name__ == "__main__":
    main()
