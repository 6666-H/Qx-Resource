import os
import re
import requests
import datetime
from datetime import timedelta
from pathlib import Path
import time
import logging

# 设置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 规则源列表
REWRITE_SOURCES = {
    "阻止常见的 HTTPDNS 服务器": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/Official/%E6%8B%A6%E6%88%AAHTTPDNS.official.sgmodule",
    "广告平台拦截器": "https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/%E5%B9%BF%E5%91%8A%E5%B9%B3%E5%8F%B0%E6%8B%A6%E6%88%AA%E5%99%A8.sgmodule",
    # 其他规则来源省略，可按需添加...
}

class RuleProcessor:
    def __init__(self):
        self.REPO_PATH = "ad"
        self.REWRITE_DIR = "rewrite"
        self.OUTPUT_FILE = "ad_rewrite.conf"
        self.RETRY_COUNT = 3
        self.TIMEOUT = 30

        self.setup_directory()

    def setup_directory(self):
        """创建必要的目录结构"""
        Path(os.path.join(self.REPO_PATH, self.REWRITE_DIR)).mkdir(parents=True, exist_ok=True)

    def get_beijing_time(self):
        """获取北京时间"""
        return datetime.datetime.utcnow() + timedelta(hours=8)

    def download_rules(self, name, url):
        """下载规则"""
        for attempt in range(self.RETRY_COUNT):
            try:
                logger.info(f"Downloading rules from {name}... (Attempt {attempt + 1})")
                response = requests.get(url, timeout=self.TIMEOUT)
                response.raise_for_status()
                return response.text
            except Exception as e:
                if attempt == self.RETRY_COUNT - 1:
                    logger.error(f"Failed to download {name}: {str(e)}")
                    return None
                time.sleep(2)

    def parse_rules(self, content):
        """解析规则内容"""
        rules = set()
        hostnames = set()
        scripts = {}
        current_section = None

        if not content:
            return rules, hostnames, scripts

        lines = content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith('#'):
                i += 1
                continue

            # 处理段落
            if line.startswith('['):
                current_section = line.strip('[]').upper()
                i += 1
                continue

            # 处理脚本部分
            if current_section == 'SCRIPT':
                script_info = self.parse_script_section(lines[i:])
                if script_info:
                    name, pattern, script = script_info
                    scripts[name] = {'pattern': pattern, 'script': script}
                    i += 3
                else:
                    i += 1
                continue

            # 转换和验证规则
            converted_rule = self.convert_surge_to_quanx(line)
            if converted_rule and self.is_valid_rule(converted_rule):
                rules.add(converted_rule)

                # 提取 hostname
                url_pattern = re.search(r'https?://([^/]+)', converted_rule)
                if url_pattern:
                    domain = url_pattern.group(1).split(':')[0]
                    if '.' in domain:
                        hostnames.add(domain)

            i += 1

        return rules, hostnames, scripts

    def parse_script_section(self, lines):
        """解析脚本部分"""
        try:
            if len(lines) < 3:
                return None
            name_line, pattern_line, script_line = lines[:3]

            # 脚本名称
            if not name_line.startswith('#'):
                return None
            name = name_line[1:].strip()

            # 匹配模式
            pattern_match = re.search(r'^(http[^\s]+)', pattern_line)
            if not pattern_match:
                return None
            pattern = pattern_match.group(1)

            # 脚本路径
            script_match = re.search(r'script-path\s*=\s*([^\s,]+)', script_line)
            if not script_match:
                return None
            script = script_match.group(1)

            return name, pattern, script
        except Exception as e:
            logger.error(f"Error parsing script section: {str(e)}")
            return None

    def convert_surge_to_quanx(self, line):
        """转换规则为 QuantumultX 格式"""
        if not line or line.startswith('#'):
            return line
        try:
            line = line.replace('\t', ' ').strip()
            if ' url ' in line:
                return line
            if 'type=http-response' in line or 'type=http-request' in line:
                pattern = re.search(r'pattern=([^,]+).*script-path=([^,\s]+)', line)
                if pattern:
                    url, script = pattern.groups()
                    requires_body = 'requires-body=true' in line
                    script_type = 'response' if 'http-response' in line else 'request'
                    body_type = '-body' if requires_body else ''
                    return f'{url.strip()} url script-{script_type}{body_type} {script.strip()}'
            if 'URL-REGEX' in line:
                pattern = re.search(r'URL-REGEX,([^,]+)', line)
                if pattern:
                    url = pattern.group(1).strip()
                    if not url.startswith('^'):
                        url = '^' + url
                    return f'{url} url reject-200'
            if '302' in line or '307' in line:
                match = re.search(r'([^\s]+)\s+30[27]\s+([^\s]+)', line)
                if match:
                    source, destination = match.groups()
                    if not source.startswith('^'):
                        source = '^' + source
                    return f'{source} url 302 {destination}'
            return None
        except Exception as e:
            logger.error(f"Error converting rule: {line}")
            return None

    def is_valid_rule(self, rule):
        """验证规则有效性"""
        if not rule or rule.startswith('#'):
            return False
        try:
            if ' url ' not in rule:
                return False
            parts = rule.split(' url ')
            if len(parts) != 2:
                return False
            valid_actions = [
                'reject', 'reject-200', 'reject-img', 'reject-dict', 'reject-array',
                'script-response-body', 'script-request-body', '302', '307'
            ]
            return any(act in parts[1] for act in valid_actions)
        except:
            return False

    def generate_output(self, rules, hostnames, scripts):
        """生成 QuantumultX 格式输出"""
        current_time = self.get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')
        output = f"""# AD Rewrite Rules
# Update: {current_time}
# Total rules: {len(rules)}
# Maintainer: Centralmatrix3
"""
        if scripts:
            output += "\n[rewrite_local]\n"
            for name, script_info in scripts.items():
                output += f"# {name}\n"
                output += f"{script_info['pattern']} url script-response-body {script_info['script']}\n"
        if rules:
            if not scripts:
                output += "\n[rewrite_local]\n"
            for rule in sorted(rules):
                output += f"{rule}\n"
        if hostnames:
            output += "\n[mitm]\n"
            output += f"hostname = {', '.join(sorted(hostnames))}\n"
        return output

    def run(self):
        """主运行逻辑"""
        all_rules = set()
        all_hostnames = set()
        all_scripts = {}

        for name, url in REWRITE_SOURCES.items():
            content = self.download_rules(name, url)
            if content:
                rules, hostnames, scripts = self.parse_rules(content)
                all_rules.update(rules)
                all_hostnames.update(hostnames)
                all_scripts.update(scripts)

        output = self.generate_output(all_rules, all_hostnames, all_scripts)
        output_path = os.path.join(self.REPO_PATH, self.REWRITE_DIR, self.OUTPUT_FILE)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)

        logger.info(f"Generated rules file: {output_path}")
        logger.info(f"Total rules: {len(all_rules)}")
        logger.info(f"Total hostnames: {len(all_hostnames)}")
        logger.info(f"Total scripts: {len(all_scripts)}")


if __name__ == "__main__":
    processor = RuleProcessor()
    processor.run()
