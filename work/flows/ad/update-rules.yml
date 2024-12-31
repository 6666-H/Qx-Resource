name: Update Rules

on:
  schedule:
    - cron: '0 */6 * * *'  # 每6小时执行一次
  workflow_dispatch:        # 允许手动触发

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.x'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests
          
      - name: Update Rules
        run: |
          python update-rules.py
          
      - name: Commit Changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add .
          git commit -m "Update rules" || exit 0
          git push
