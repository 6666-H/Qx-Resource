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
    # 用于存储所有注释和其他配置
    comments = []
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

            comments.append(f"\n# ======== {name} ========")

            # 处理每一行
            current_tag = None
            for line in content.splitlines():
                line = line.strip()
                if not line:  # 跳过空行
                    continue

                if line.startswith('#'):  # 保存注释行
                    comments.append(line)
                    continue

                # 检查标签 [tag]，并记录当前标签
                if line.startswith('[') and line.endswith(']'):
                    current_tag = line[1:-1].upper()  # 转成大写
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
    final_content += "\n".join(comments)

    # 合并 mitm 的 hostname
    if mitm_hostnames:
        final_content += "\n\n# ======== [MITM] ========\n"
        final_content += f"hostname = {','.join(sorted(mitm_hostnames))}\n"

    # 分类规则输出
    for tag, rules in classified_rules.items():
        final_content += f"\n\n# ======== [{tag}] ========\n"
        final_content += '\n'.join(sorted(rules))

    # 去重后的规则
    final_content += "\n\n# ======== [去重后的规则] ========\n"
    final_content += '\n'.join(sorted(unique_rules))

    # 其它脚本规则
    if other_rules:
        final_content += "\n\n# ======== [其它脚本] ========\n"
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
