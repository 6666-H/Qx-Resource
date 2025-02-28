# 国内分流规则合集

## 更新时间
2025-02-28 10:55:35 (北京时间)

## 规则说明
本规则集合并自各个开源规则，统一转换为标准格式。
- 去除重复规则
- 统一规则格式
- 移除额外的选项（如 ChinaMax, no-resolve）
- 将不带前缀的域名默认设为 DOMAIN-SUFFIX
- 去除域名前的点(.)
当前规则数量：117714

## 规则来源
- ChinaMax: https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/ChinaMax/ChinaMax.list
- ChinaMax_2: https://raw.githubusercontent.com/deezertidal/QuantumultX-Rewrite/refs/heads/master/rule/ChinaMax.list
- Direct_Rule: https://raw.githubusercontent.com/Code-Dramatist/Rule_Actions/main/Direct_Rule/Direct_Rule.rule
- GEOIP: https://raw.githubusercontent.com/6666-H/QuantumultX-Resource/refs/heads/main/Manual/Rule/Direct.list

## 规则格式说明
- DOMAIN：完整域名匹配
- DOMAIN-SUFFIX：域名后缀匹配
- DOMAIN-WILDCARD：域名通配符匹配
- DOMAIN-KEYWORD：域名关键字匹配
- USER-AGENT：User-Agent匹配
- IP-CIDR：IPv4 地址段
- IP6-CIDR：IPv6 地址段
- IP-ASN：自治系统号码
- GEOIP：GeoIP数据库（国家/地区）匹配
