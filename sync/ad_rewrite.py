import os
import requests
import datetime
from datetime import timedelta
import git
from pathlib import Path

class RuleProcessor:
    def __init__(self):
        self.REPO_PATH = "ad"
        self.REWRITE_DIR = "rewrite"
        self.OUTPUT_FILE = "ad_rewrite.conf"
        self.README_PATH = "README-rewrite.md"
        self.RETRY_COUNT = 3
        self.TIMEOUT = 30
        
        # 确保目录存在
        self.setup_directory()
        
    def setup_directory(self):
        """创建必要的目录"""
        Path(os.path.join(self.REPO_PATH, self.REWRITE_DIR)).mkdir(parents=True, exist_ok=True)

    def get_beijing_time(self):
        """获取北京时间"""
        return datetime.datetime.utcnow() + timedelta(hours=8)

    def download_rules(self, name, url):
        """下载规则，带重试机制"""
        for attempt in range(self.RETRY_COUNT):
            try:
                print(f"Downloading rules from {name}... (Attempt {attempt + 1})")
                response = requests.get(url, timeout=self.TIMEOUT)
                response.raise_for_status()
                return response.text
            except Exception as e:
                if attempt == self.RETRY_COUNT - 1:
                    print(f"Failed to download {name} after {self.RETRY_COUNT} attempts: {str(e)}")
                    return None
                print(f"Retry after error: {str(e)}")
                time.sleep(2)
        return None

    def is_valid_rule(self, rule):
        """验证规则格式是否正确"""
        if not rule or rule.startswith('#'):
            return False
        return any(pattern in rule for pattern in ['url', 'reject', 'script', '^http'])

    def parse_rules(self, content):
        """解析规则内容"""
        rules = set()
        hostnames = set()
        comments = []

        if not content:
            return rules, hostnames, comments

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith('#'):
                comments.append(line)
            elif line.startswith('hostname'):
                try:
                    hosts = line.split('=')[1].strip().split(',')
                    hostnames.update(h.strip() for h in hosts if h.strip())
                except IndexError:
                    print(f"Warning: Invalid hostname line: {line}")
            elif self.is_valid_rule(line):
                rules.add(line)

        return rules, hostnames, comments

    def merge_rules(self, sources):
        """合并所有规则"""
        all_rules = set()
        all_hostnames = set()
        all_comments = []
        
        total_sources = len(sources)
        current = 0
        
        for name, url in sources.items():
            current += 1
            print(f"Processing {current}/{total_sources}: {name}")
            content = self.download_rules(name, url)
            if content:
                rules, hostnames, comments = self.parse_rules(content)
                all_rules.update(rules)
                all_hostnames.update(hostnames)
                all_comments.extend([f"\n# ======== {name} ========"] + comments)

        return all_rules, all_hostnames, all_comments

    def generate_output(self, rules, hostnames, comments):
        """生成输出内容"""
        header = f"""# 广告拦截重写规则合集
# 更新时间：{self.get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 规则数量：{len(rules)}
# Hostname数量：{len(hostnames)}

"""
        content = header
        content += "\n".join(comments)
        content += "\n\n# ======== 去重后的规则 ========\n"
        content += '\n'.join(sorted(rules))
        
        if hostnames:
            content += "\n\n# ======== Hostname ========\n"
            content += f"hostname = {','.join(sorted(hostnames))}\n"
        
        return content

    def save_rules(self, content):
        """保存规则到文件"""
        output_path = os.path.join(self.REPO_PATH, self.REWRITE_DIR, self.OUTPUT_FILE)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Successfully saved rules to {output_path}")
            return True
        except Exception as e:
            print(f"Error saving rules: {str(e)}")
            return False

def main():
    processor = RuleProcessor()
    rules, hostnames, comments = processor.merge_rules(REWRITE_SOURCES)
    content = processor.generate_output(rules, hostnames, comments)
    
    if processor.save_rules(content):
        print(f"Successfully processed {len(rules)} rules and {len(hostnames)} hostnames")
    else:
        print("Failed to save rules")

if __name__ == "__main__":
    main()
