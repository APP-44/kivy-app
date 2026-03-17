#!/usr/bin/env python3
"""
通过API部署员工页面到虚拟主机
"""

import requests
import base64
import urllib.parse

# API配置
API_URL = 'https://scjmj.cn/api_sync.php'
API_KEY = 'jiameijing2024'

def deploy_file(filename, content):
    """通过API部署文件"""

    # 将内容转为base64
    content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')

    # 准备参数
    params = {
        'key': API_KEY,
        'action': 'deploy_file',
        'filename': filename,
        'content': content_b64,
    }

    try:
        print(f"正在部署 {filename}...")

        # 构建URL
        query_string = urllib.parse.urlencode(params, encoding='utf-8')
        full_url = f"{API_URL}?{query_string}"

        print(f"请求URL长度: {len(full_url)} 字符")

        # 发送GET请求
        response = requests.get(full_url, timeout=30)

        print(f"响应状态: {response.status_code}")
        print(f"响应内容: {response.text[:500]}")

        try:
            result = response.json()
            if result.get('success'):
                print(f"[OK] 部署成功: {filename}")
                return True
            else:
                print(f"[FAIL] 部署失败: {result.get('message')}")
                return False
        except:
            print(f"[FAIL] 无法解析响应: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"[ERROR] 部署异常: {e}")
        return False

def deploy_yangsan_page():
    """部署杨三员工页面"""

    # 读取PHP文件内容
    with open('yang-san.php', 'r', encoding='utf-8') as f:
        php_content = f.read()

    print(f"PHP文件大小: {len(php_content)} 字符")

    # 部署PHP文件
    success = deploy_file('yang-san.php', php_content)

    return success

if __name__ == '__main__':
    deploy_yangsan_page()
