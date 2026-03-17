#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

# 读取文件
with open('C:/Users/Administrator/AppData/Local/Temp/index_old.asp', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# 定义替换规则 (旧字符串 -> 新字符串)
replacements = [
    ('钟点\ufffd?', '钟点工'),  # 钟点工
    ('服\ufffd?', '服务'),      # 服务
    ('\ufffd?', ''),           # 单独的乱码字符删除
    ('新闻动\ufffd?', '新闻动态'),  # 新闻动态
    ('解决方\ufffd?', '解决方案'),  # 解决方案
    ('欢迎访问四川嘉美净清洁服务有限公司\ufffd?', '欢迎访问四川嘉美净清洁服务有限公司！'),
    ('服务热线\ufffd?', '服务热线：'),
    ('选择我们\ufffd?大理\ufffd?', '选择我们的理由'),
    ('我们的优\ufffd?', '我们的优势'),
    ('专业保洁人\ufffd?', '专业保洁人员'),
    ('快速服\ufffd?', '快速服务'),
    ('客户需\ufffd?', '客户需求'),
    ('各种需\ufffd?', '各种需求'),
    ('立即预约服务 \ufffd?', '立即预约服务 →'),
    ('按小时计费\ufffd?', '按小时计费。'),
    ('灵活钟点工清洁服务，按小时计费\ufffd?', '灵活钟点工清洁服务，按小时计费。'),
]

# 执行替换
for old, new in replacements:
    content = content.replace(old, new)

# 保存文件
with open('C:/Users/Administrator/AppData/Local/Temp/index_fixed.asp', 'w', encoding='utf-8') as f:
    f.write(content)

print("OK: File fixed")
print(f"Size: {len(content)} bytes")
