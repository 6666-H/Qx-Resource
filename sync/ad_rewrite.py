import os
import requests
import datetime
from datetime import timedelta
import git
from pathlib import Path

# 配置项
REPO_PATH = "ad"
REWRITE_DIR = "rewrite"
OUTPUT_FILE = "ad_rewrite.conf"
README_PATH = "README-rewrite.md"

# 规则源列表
REWRITE_SOURCES = {
    "阻止常见的 HTTPDNS 服务器": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/%E6%8B%A6%E6%88%AAHTTPDNS.official.sgmodule",
    "广告平台拦截器": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%B9%BF%E5%91%8A%E5%B9%B3%E5%8F%B0%E6%8B%A6%E6%88%AA%E5%99%A8.sgmodule",
    "whatshubs开屏屏蔽": "https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/manual/rewrite/adultraplus.conf",
    # 省略其余规则...
}

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.datetime.utcnow()
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time

def setup_directory():
    """创建必要的目录"""
    Path(os.path.join(REPO_PATH, REWRITE_DIR)).mkdir(parents=True, exist_ok=True)

def download_and_merge_rules():
    """下载并合并重写规则"""
    beijing_time = get_beijing_time()
    header = f"""# 广告拦截重写规则合集
# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in REWRITE_SOURCES.items()])}

"""
    
    # 用于存储去重后的规则
    unique_rules = set()
    # 用于存储分类的规则
    classified_rules = {}
    
    # 用于存储 mitm 主机名
    mitm_hostnames = set()
    # 用于存储其它脚本规则
    other_rules = []

    for name, url in REWRITE_SOURCES.items():
        try:
            print(f"Downloading rules from {name}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text

            # 处理每一行
            current_tag = None
            for line in content.splitlines():
                line = line.strip()
                if not line:  # 跳过空行
                    continue

                # 检查标签 [tag]，并记录当前标签
                if line.startswith('[') and line.endswith(']'):
                    current_tag = line[1:-1]
                    if current_tag not in classified_rules:
                        classified_rules[current_tag] = []
                    continue

                if current_tag:  # 当前行属于某个标签
                    classified_rules[current_tag].append(line)
                    continue

                if line.startswith('hostname'):  # 提取 hostname
                    hosts = line.split('=')[1].strip().split(',')
                    mitm_hostnames.update([h.strip() for h in hosts if h.strip()])
                    continue

                if line.startswith('^'):  # 正常重写规则
                    unique_rules.add(line)

                # 处理 JavaScript 脚本
                if line.endswith('.js'):
                    other_rules.append(line)

        except Exception as e:
            print(f"Error downloading {name}: {str(e)}")

    # 组合最终内容
    final_content = header

    # 合并 mitm 的 hostname
    if mitm_hostnames:
        final_content += f"[mitm]\nhostname = {','.join(sorted(mitm_hostnames))}\n"

    # 分类规则输出
    for tag, rules in classified_rules.items():
        final_content += f"\n[{tag}]\n"
        final_content += '\n'.join(sorted(rules))

    # 去重后的规则
    final_content += "\n[去重后的规则]\n"
    final_content += '\n'.join(sorted(unique_rules))

    # 其它脚本规则
    if other_rules:
        final_content += "\n[其它脚本]\n"
        final_content += '\n'.join(sorted(other_rules))

    # 写入合并后的文件
    output_path = os.path.join(REPO_PATH, REWRITE_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)

    rule_count = len(unique_rules)
    hostname_count = len(mitm_hostnames)
    script_count = len(other_rules)
    print(f"Successfully merged {rule_count} unique rules, {hostname_count} mitm hostnames, and {script_count} scripts to {OUTPUT_FILE}")
    return rule_count, hostname_count, script_count

def update_readme(rule_count, hostname_count, script_count):
    """更新 README.md"""
    beijing_time = get_beijing_time()
    content = f"""# 广告拦截重写规则合集

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 规则说明
本重写规则集合并自各个开源规则，去除重复规则。
- 当前规则数量：{rule_count}
- 当前 mitm 主机名数量：{hostname_count}
- 当前 脚本 数量：{script_count}

## 规则来源
{chr(10).join([f'- {name}: {url}' for name, url in REWRITE_SOURCES.items()])}

## 使用方法
规则文件地址: https://raw.githubusercontent.com/[你的用户名]/[仓库名]/main/rewrite/ad_rewrite.conf
"""
    
    with open(os.path.join(REPO_PATH, README_PATH), 'w', encoding='utf-8') as f:
        f.write(content)

def git_push():
    """提交更改到 Git"""
    try:
        repo = git.Repo(REPO_PATH)
        repo.git.add(all=True)
        beijing_time = get_beijing_time()
        repo.index.commit(f"Update rewrite rules: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
        origin = repo.remote(name='origin')
        origin.push()
        print("Successfully pushed to repository")
    except Exception as e:
        print(f"Error pushing to repository: {str(e)}")

def main():
    setup_directory()
    rule_count, hostname_count, script_count = download_and_merge_rules()
    update_readme(rule_count, hostname_count, script_count)
    git_push()

if __name__ == "__main__":
    main()
