import os
import requests
import datetime
from pathlib import Path
import urllib3
import time
import traceback

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置项
REWRITE_DIR = "rewrite"
RULES_DIR = "rules"
OUTPUT_FILE = "ad_rewrite.conf"
README_PATH = "README-rewrite.md"

# 网站规则源
WEBSITE_RULES = {
    "adultraplus": "https://whatshub.top/rewrite/adultraplus.conf",
    "wechatad": "https://whatshub.top/rewrite/wechatad.conf",
    "youtube": "https://whatshub.top/rewrite/youtube.conf",
    "可莉微信屏蔽": "https://kelee.one/Tool/Loon/Plugin/WexinMiniPrograms_Remove_ads.plugin",
}

# GitHub 规则源
GITHUB_SOURCES = {
    "surge去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/%E6%96%B0%E6%89%8B%E5%8F%8B%E5%A5%BD%E3%81%AE%E5%8E%BB%E5%B9%BF%E5%91%8A%E9%9B%86%E5%90%88.official.sgmodule",
    "chxm去广告": "https://raw.githubusercontent.com/chxm1023/Advertising/main/AppAd.conf",
    "墨鱼微信广告": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/Applet.conf",
    "墨鱼去开屏V2.0": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/StartUp.conf",
    "广告拦截精简版": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/QuantumultX/AdvertisingLite/AdvertisingLite.conf",
    "去广告重写": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/chongxie.txt",
    "整合广告拦截": "https://raw.githubusercontent.com/DivineEngine/Profiles/master/Quantumult/Rewrite/Block/Advertising.conf"
}

def setup_directory():
    """创建必要的目录"""
    Path(REWRITE_DIR).mkdir(parents=True, exist_ok=True)
    Path(RULES_DIR).mkdir(parents=True, exist_ok=True)

def download_rule(url, headers=None):
    """下载规则"""
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    for _ in range(3):  # 重试3次
        try:
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error downloading {url}: {str(e)}")
            time.sleep(2)
    return None

def download_website_rules():
    """下载网站规则"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Referer': 'https://whatshub.top/',
    }

    for name, url in WEBSITE_RULES.items():
        try:
            print(f"Downloading {name} from {url}")
            content = download_rule(url, headers)
            
            if content:
                rule_path = os.path.join(RULES_DIR, f"{name}.conf")
                with open(rule_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Successfully saved {name}")
            else:
                print(f"Failed to download {name}")
                
        except Exception as e:
            print(f"Error processing {name}: {str(e)}")

def download_github_rules():
    """下载 GitHub 规则"""
    for name, url in GITHUB_SOURCES.items():
        try:
            print(f"Downloading {name} from {url}")
            content = download_rule(url)
            
            if content:
                rule_path = os.path.join(RULES_DIR, f"{name}.conf")
                with open(rule_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Successfully saved {name}")
            else:
                print(f"Failed to download {name}")
                
        except Exception as e:
            print(f"Error processing {name}: {str(e)}")

def merge_all_rules():
    """合并所有规则"""
    merged_content = f"""# 广告拦截重写规则合集
# 更新时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 合并自以下源：
"""

    # 添加所有规则源信息
    for name, url in {**WEBSITE_RULES, **GITHUB_SOURCES}.items():
        merged_content += f"# {name}: {url}\n"

    # 合并所有规则文件
    for filename in os.listdir(RULES_DIR):
        if filename.endswith('.conf'):
            name = filename[:-5]
            try:
                with open(os.path.join(RULES_DIR, filename), 'r', encoding='utf-8') as f:
                    content = f.read()
                    merged_content += f"\n# ======== {name} ========\n"
                    merged_content += content + "\n"
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

    # 保存合并后的文件
    output_path = os.path.join(REWRITE_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(merged_content)
    
    print(f"Successfully merged all rules to {OUTPUT_FILE}")

def update_readme():
    """更新 README.md"""
    content = f"""# 广告拦截重写规则合集

## 更新时间
{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 规则说明
本重写规则集合并自各个开源规则，保持原始格式不变。

## 规则来源
### 网站规则
{chr(10).join([f'- {name}: {url}' for name, url in WEBSITE_RULES.items()])}

### GitHub规则
{chr(10).join([f'- {name}: {url}' for name, url in GITHUB_SOURCES.items()])}
"""
    
    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    setup_directory()
    download_website_rules()
    download_github_rules()
    merge_all_rules()
    update_readme()

if __name__ == "__main__":
    main()
