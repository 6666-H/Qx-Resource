import os
import re
import requests
import datetime
from datetime import timedelta
import git
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    "whatshub微信屏蔽": "https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/manual/rewrite/wechatad.conf",
    "whatshubAdBlock":"https://raw.githubusercontent.com/deezertidal/QuantumultX-Rewrite/refs/heads/master/rewrite/AdBlock.conf",
    "surge去广告":"https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/%E6%96%B0%E6%89%8B%E5%8F%8B%E5%A5%BD%E3%81%AE%E5%8E%BB%E5%B9%BF%E5%91%8A%E9%9B%86%E5%90%88.official.sgmodule",
    "chxm去广告": "https://raw.githubusercontent.com/chxm1023/Advertising/main/AppAd.conf",
    "墨鱼微信广告": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/Applet.conf",
    "墨鱼去开屏V2.0": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/StartUp.conf",
    "广告拦截精简版": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/QuantumultX/AdvertisingLite/AdvertisingLite.conf",
    "去广告重写": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/chongxie.txt",
    "整合广告拦截": "https://raw.githubusercontent.com/weiyesing/QuantumultX/GenMuLu/ChongXieGuiZe/QuGuangGao/To%20advertise.conf",
    "YouTube去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/Youtube%20%E5%8E%BB%E5%B9%BF%E5%91%8A%20(%E4%B8%8D%E5%8E%BB%E8%B4%B4%E7%89%87).official.sgmodule",
    "YouTube双语翻译": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Beta/YouTube%E7%BF%BB%E8%AF%91.beta.sgmodule",
    "小红书去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%B0%8F%E7%BA%A2%E4%B9%A6%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "微博去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%BE%AE%E5%8D%9A%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "小黑盒去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%B0%8F%E9%BB%91%E7%9B%92%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "微信小程序去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%BE%AE%E4%BF%A1%E5%B0%8F%E7%A8%8B%E5%BA%8F%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "百度网页去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E7%99%BE%E5%BA%A6%E6%90%9C%E7%B4%A2%E7%BD%91%E9%A1%B5%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "网易云音乐去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E7%BD%91%E6%98%93%E4%BA%91%E9%9F%B3%E4%B9%90%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "拼多多去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E6%8B%BC%E5%A4%9A%E5%A4%9A%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "Google搜索重定向": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Google%E9%87%8D%E5%AE%9A%E5%90%91.sgmodule",
    "京东比价": "https://raw.githubusercontent.com/mw418/Loon/main/script/jd_price.js",
    "汤头条解锁": "https://raw.githubusercontent.com/Yu9191/Rewrite/main/lsp/Tangtoutiao.js",
    "1998解锁": "https://raw.githubusercontent.com/Yu9191/Rewrite/main/1998.js"
}

def create_session():
    """创建带重试机制的会话"""
    session = requests.Session()
    retries = requests.adapters.Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504]
    )
    session.mount('http://', requests.adapters.HTTPAdapter(max_retries=retries))
    session.mount('https://', requests.adapters.HTTPAdapter(max_retries=retries))
    return session

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.datetime.utcnow()
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time

def setup_directory():
    """创建必要的目录"""
    Path(os.path.join(REPO_PATH, REWRITE_DIR)).mkdir(parents=True, exist_ok=True)

def validate_rewrite_rule(rule):
    """验证重写规则的格式"""
    try:
        if ' url ' not in rule:
            return False
            
        pattern, action = rule.split(' url ', 1)
        
        # 检查基本格式
        if not pattern.startswith('^'):
            return False
            
        # 检查动作类型
        valid_actions = ['reject', 'reject-200', 'reject-img', 'reject-dict', 'reject-array']
        if action not in valid_actions and not action.startswith('script'):
            return False
            
        return True
    except:
        return False

def test_regex_pattern(pattern):
    """测试正则表达式是否有效"""
    try:
        re.compile(pattern)
        return True
    except re.error:
        return False

def process_rewrite_rule(line):
    """处理重写规则，确保正则表达式正确"""
    try:
        if not line.strip():
            return None
            
        if ' url ' not in line:
            return None
            
        pattern, action = line.split(' url ', 1)
        
        # 修复常见的正则表达式问题
        if pattern.startswith('^'):
            pattern = pattern.replace(r'[\w-.]+', r'[\w\-\.]+')
            pattern = pattern.replace('.mp4', r'\.mp4')
            pattern = pattern.replace('?', r'\?')
            
        # 验证正则表达式
        test_pattern = pattern[1:] if pattern.startswith('^') else pattern
        if not test_regex_pattern(test_pattern):
            logger.warning(f"Invalid regex pattern: {pattern}")
            return None
            
        return f"{pattern} url {action}"
    except Exception as e:
        logger.error(f"Error processing rule: {line}, Error: {str(e)}")
        return None

def filter_invalid_rules(rules):
    """过滤无效的重写规则"""
    valid_rules = set()
    for rule in rules:
        processed_rule = process_rewrite_rule(rule)
        if processed_rule:
            valid_rules.add(processed_rule)
    return valid_rules

def download_and_merge_rules():
    """下载并合并重写规则"""
    beijing_time = get_beijing_time()
    header = f"""# 广告拦截重写规则合集
# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in REWRITE_SOURCES.items()])}

"""
    
    unique_rules = set()
    classified_rules = {}
    all_hostnames = set()
    other_rules = []
    session = create_session()

    for name, url in REWRITE_SOURCES.items():
        try:
            logger.info(f"Downloading rules from {name}...")
            response = session.get(url, timeout=30)
            response.raise_for_status()
            content = response.text
            
            current_tag = None
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if 'hostname' in line.lower():
                    if '=' in line:
                        hostnames = line.split('=')[1].strip()
                        hostnames = hostnames.replace('%APPEND%', '').strip()
                        all_hostnames.update(h.strip() for h in hostnames.split(',') if h.strip())
                    continue
                
                if line.startswith('[') and line.endswith(']'):
                    current_tag = line[1:-1].upper()
                    tag_with_brackets = f'[{current_tag}]'
                    if tag_with_brackets not in classified_rules:
                        classified_rules[tag_with_brackets] = []
                    continue

                if current_tag:
                    if current_tag.upper() != 'MITM':
                        classified_rules[f'[{current_tag}]'].append(line)
                    continue

                if line.startswith('^'):
                    processed_rule = process_rewrite_rule(line)
                    if processed_rule:
                        unique_rules.add(processed_rule)
                
                elif line.endswith('.js'):
                    other_rules.append(line)

        except Exception as e:
            logger.error(f"Error downloading {name}: {str(e)}")

    # Filter invalid rules
    unique_rules = filter_invalid_rules(unique_rules)

    # 组合最终内容
    final_content = header
    
    for tag, rules in classified_rules.items():
        if rules and tag.upper() != '[MITM]':
            final_content += f"\n{tag}\n"
            final_content += '\n'.join(sorted(rules)) + '\n'
    
    if all_hostnames:
        final_content += "\n[MITM]\n"
        final_content += f"hostname = {', '.join(sorted(all_hostnames))}\n"

    if unique_rules:
        final_content += "\n[REWRITE]\n"
        final_content += '\n'.join(sorted(unique_rules)) + '\n'
    
    if other_rules:
        final_content += "\n[SCRIPT]\n"
        final_content += '\n'.join(sorted(other_rules)) + '\n'

    output_path = os.path.join(REPO_PATH, REWRITE_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    rule_count = len(unique_rules)
    hostname_count = len(all_hostnames)
    script_count = len(other_rules)
    logger.info(f"Successfully merged {rule_count} unique rules, {hostname_count} hostnames, and {script_count} scripts")
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
- 当前 hostname 数量：{hostname_count}
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
        logger.info("Successfully pushed to repository")
    except Exception as e:
        logger.error(f"Error pushing to repository: {str(e)}")

def main():
    """主函数"""
    try:
        setup_directory()
        rule_count, hostname_count, script_count = download_and_merge_rules()
        update_readme(rule_count, hostname_count, script_count)
        git_push()
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")

if __name__ == "__main__":
    main()
