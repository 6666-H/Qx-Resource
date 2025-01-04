import os
import requests
import datetime
from datetime import timedelta
import git
from pathlib import Path
import re

# 配置项
REPO_PATH = "ad"
REWRITE_DIR = "rewrite"
OUTPUT_FILE = "ad_rewrite.conf"
README_PATH = "README-rewrite.md"

# 规则源列表
REWRITE_SOURCES = {
    "whatshubs开屏屏蔽": "https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/manual/rewrite/adultraplus.conf",
    "whatshub微信屏蔽": "https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/manual/rewrite/wechatad.conf",
    "whatshubAdBlock": "https://raw.githubusercontent.com/deezertidal/QuantumultX-Rewrite/refs/heads/master/rewrite/AdBlock.conf",
    "surge去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/%E6%96%B0%E6%89%8B%E5%8F%8B%E5%A5%BD%E3%81%AE%E5%8E%BB%E5%B9%BF%E5%91%8A%E9%9B%86%E5%90%88.official.sgmodule",
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
    "微博去广告": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%BE%AE%E5%8D%9A%E5%8E%BB%E5%B9%BF%E5%91%8A.sgmodule",
    "Google搜索重定向": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Google%E9%87%8D%E5%AE%9A%E5%90%91.sgmodule",
    "京东比价": "https://raw.githubusercontent.com/mw418/Loon/main/script/jd_price.js",
    "汤头条解锁": "https://raw.githubusercontent.com/Yu9191/Rewrite/main/lsp/Tangtoutiao.js",
    "1998解锁": "https://raw.githubusercontent.com/Yu9191/Rewrite/main/1998.js"
}

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.datetime.utcnow()
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time

def setup_directory():
    """创建必要的目录"""
    Path(os.path.join(REPO_PATH, REWRITE_DIR)).mkdir(parents=True, exist_ok=True)

def convert_surge_to_qx(line):
    """将Surge规则转换为QuantumultX格式"""
    # Surge脚本转换
    if line.startswith('http-response') or line.startswith('http-request'):
        # 提取URL模式和脚本路径
        pattern = r'(http-(?:response|request))\s+([^\s]+)\s+requires-body=(\d+),\s*script-path=(.+)'
        match = re.match(pattern, line)
        if match:
            req_type, url_pattern, requires_body, script_path = match.groups()
            script_type = 'response' if req_type == 'http-response' else 'request'
            return f'url script-{script_type}-body {url_pattern} {script_path}'
    
    # Surge URL重写转换
    if '=>' in line:
        parts = line.split('=>')
        if len(parts) == 2:
            return f'url {parts[0].strip()} {parts[1].strip()}'
    
    # Surge reject转换
    if any(x in line for x in ['REJECT', 'REJECT-TINYGIF', 'REJECT-IMG', 'REJECT-DICT', 'REJECT-ARRAY']):
        pattern = r'([^\s]+)\s+(REJECT(?:-TINYGIF|-IMG|-DICT|-ARRAY)?)'
        match = re.match(pattern, line)
        if match:
            url, reject_type = match.groups()
            reject_map = {
                'REJECT': 'reject',
                'REJECT-TINYGIF': 'reject-img',
                'REJECT-IMG': 'reject-img',
                'REJECT-DICT': 'reject-dict',
                'REJECT-ARRAY': 'reject-array'
            }
            return f'url {reject_map.get(reject_type, "reject")} {url}'
    
    return line

def parse_rule_line(line):
    """解析重写规则行"""
    # 预处理：移除注释
    if '#' in line:
        line = line.split('#')[0].strip()
    
    # 如果是空行，直接返回False
    if not line:
        return False
        
    # QX 基本重写格式
    qx_patterns = [
        r'^url\s+(?:reject|reject-200|reject-img|reject-dict|reject-array)\s+',
        r'^url\s+script-(?:response|request)-(?:body|header)\s+',
        r'^url\s+(?:request|response)-(?:body|header)\s+',
        r'^(?:host|host-suffix|host-keyword)',
        r'^\^https?://'
    ]
    
    # Surge 格式 (需转换)
    surge_patterns = [
        r'^http-(?:response|request)\s+',
        r'.+\s*=>\s*.+',
        r'.+\s+(?:REJECT|REJECT-TINYGIF|REJECT-IMG|REJECT-DICT|REJECT-ARRAY)'
    ]
    
    # 检查是否匹配任何QX格式
    for pattern in qx_patterns:
        if re.match(pattern, line):
            return True
            
    # 检查是否匹配任何Surge格式
    for pattern in surge_patterns:
        if re.match(pattern, line):
            return True
            
    return False

def is_script_section(line):
    """检查是否为脚本相关内容"""
    script_indicators = [
        '[Script]',
        'script-path=',
        'requires-body=',
        'type=http-response',
        'type=http-request',
        'url script-',
        '.js'
    ]
    return any(indicator in line for indicator in script_indicators)

def extract_hostnames(line):
    """提取 hostname"""
    if 'hostname' in line.lower():
        line = line.replace('%APPEND%', '').replace('%INSERT%', '').replace('hostname =', '').replace('hostname=', '')
        hosts = re.split(r'[,\s]+', line)
        return [h.strip() for h in hosts if h.strip() and '*' not in h]  # 排除通配符
    return []

def process_js_content(content, name):
    """处理JavaScript内容，确保格式正确"""
    # 添加基本注释信息
    header = f"""/*
* 名称: {name}
* 更新: {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}
*/

"""
    # 如果内容没有基本结构，添加封装
    if 'function' not in content and 'let' not in content and 'var' not in content:
        content = f"""
let body = $response.body;
try {{
    {content}
}} catch (err) {{
    console.log('Error: ' + err);
}}
$done({{body}});
"""
    return header + content

def download_and_merge_rules():
    """下载并合并重写规则"""
    beijing_time = get_beijing_time()
    header = f"""# QuantumultX 重写规则合集
# 更新时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 规则数量：{len(REWRITE_SOURCES)}
# 合并自以下源：
# {chr(10).join([f'# {name}: {url}' for name, url in REWRITE_SOURCES.items()])}

"""
    
    # 存储容器
    unique_rules = set()  # 普通重写规则
    scripts = []  # 脚本规则
    hostnames = set()  # hostname
    comments = []  # 注释
    js_files = {}  # JavaScript文件
    module_info = []  # 模块信息

    for name, url in REWRITE_SOURCES.items():
        try:
            print(f"Downloading rules from {name}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text

            # 处理JavaScript文件
            if url.endswith('.js') or 'script-path' in content:
                js_name = f"{name.replace(' ', '_')}.js"
                js_content = process_js_content(content, name)
                js_files[js_name] = js_content
                continue

            # 处理文件内容
            lines = content.splitlines()
            in_script_section = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 处理注释和模块信息
                if line.startswith('#'):
                    if line.startswith('#!'):
                        module_info.append(line)
                    else:
                        comments.append(line)
                    continue

                # 处理 hostname
                if 'hostname' in line.lower():
                    hostnames.update(extract_hostnames(line))
                    continue

                # 处理脚本部分
                if is_script_section(line):
                    in_script_section = True
                    # 转换Surge格式为QX格式
                    converted_line = convert_surge_to_qx(line)
                    if converted_line != line:
                        scripts.append(f"# 转换自Surge: {line}")
                    scripts.append(converted_line)
                    continue

                # 处理普通重写规则
                if parse_rule_line(line):
                    converted_line = convert_surge_to_qx(line)
                    unique_rules.add(converted_line)

        except Exception as e:
            print(f"Error downloading {name}: {str(e)}")

    # 保存 JavaScript 文件
    for name, content in js_files.items():
        js_path = os.path.join(REPO_PATH, REWRITE_DIR, name)
        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Saved JavaScript file: {name}")

    # 组合最终内容
    final_content = header

    if module_info:
        final_content += "\n[rewrite_local]\n# ======== 模块信息 ========\n"
        final_content += '\n'.join(module_info)

    if scripts:
        final_content += "\n\n# ======== 脚本规则 ========\n"
        final_content += '\n'.join(scripts)

    final_content += "\n\n# ======== 重写规则 ========\n"
    final_content += '\n'.join(sorted(unique_rules))

    if hostnames:
        final_content += "\n\n[mitm]\n# ======== MitM主机名 ========\n"
        final_content += f"hostname = {','.join(sorted(hostnames))}"

    # 写入合并后的文件
    output_path = os.path.join(REPO_PATH, REWRITE_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)

    return len(unique_rules), len(scripts), len(js_files), len(hostnames)

def update_readme(rule_count, script_count, js_count, hostname_count):
    """更新 README.md"""
    beijing_time = get_beijing_time()
    content = f"""# QuantumultX 重写规则合集

## 更新时间
{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

## 规则说明
本重写规则集合并自各个开源规则，适用于 QuantumultX。
自动处理规则去重、格式转换、脚本处理等。

## 规则统计
- 重写规则数量：{rule_count}
- 脚本规则数量：{script_count}
- JavaScript文件数量：{js_count}
- MitM主机名数量：{hostname_count}

## 规则来源
{chr(10).join([f'- {name}: {url}' for name, url in REWRITE_SOURCES.items()])}

## 使用说明
1. 重写规则地址：
https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/ad/rewrite/ad_rewrite.conf

2. 使用方法：
- 打开 QuantumultX
- 进入配置文件编辑
- 在 [rewrite_remote] 部分添加规则地址
- 在 [mitm] 部分添加所需主机名
- 开启 MITM 功能并信任证书

## 注意事项
1. 首次使用需要安装并信任 MITM 证书
2. 部分规则可能需要开启 MITM 才能生效
3. 规则更新时间：每日自动更新
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
    try:
        print("Setting up directories...")
        setup_directory()
        
        print("Downloading and merging rules...")
        rule_count, script_count, js_count, hostname_count = download_and_merge_rules()
        print(f"Rules processed: {rule_count} rules, {script_count} scripts, {js_count} JS files, {hostname_count} hostnames")
        
        print("Updating README...")
        update_readme(rule_count, script_count, js_count, hostname_count)
        
        print("Pushing to Git repository...")
        git_push()
        
        print("All tasks completed successfully!")
    except Exception as e:
        print(f"Error in main process: {str(e)}")

if __name__ == "__main__":
    main()

