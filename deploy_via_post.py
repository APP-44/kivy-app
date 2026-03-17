#!/usr/bin/env python3
"""
通过POST方式部署员工页面到虚拟主机
"""

import requests
import base64
import urllib.parse
import json

# API配置
API_URL = 'https://scjmj.cn/api_sync.php'
API_KEY = 'jiameijing2024'

def deploy_file_post(filename, content):
    """通过POST部署文件"""

    # 将内容转为base64
    content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')

    # 准备POST数据
    post_data = {
        'key': API_KEY,
        'action': 'deploy_file',
        'filename': filename,
        'content': content_b64,
    }

    try:
        print(f"正在通过POST部署 {filename}...")
        print(f"内容大小: {len(content)} 字符")
        print(f"Base64大小: {len(content_b64)} 字符")

        # 发送POST请求
        response = requests.post(
            API_URL,
            data=post_data,
            timeout=30,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

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
        except Exception as e:
            print(f"[FAIL] 无法解析响应: {e}")
            print(f"响应内容: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"[ERROR] 部署异常: {e}")
        return False

def test_api():
    """测试API是否可用"""
    try:
        response = requests.get(f"{API_URL}?key={API_KEY}&action=test", timeout=10)
        print(f"API测试响应: {response.text}")
        return True
    except Exception as e:
        print(f"API测试失败: {e}")
        return False

def deploy_yangsan_page():
    """部署杨三员工页面"""

    # 先测试API
    print("=== 测试API ===")
    test_api()

    print("\n=== 部署文件 ===")

    # 读取PHP文件内容
    with open('yang-san.php', 'r', encoding='utf-8') as f:
        php_content = f.read()

    # 部署PHP文件
    success = deploy_file_post('yang-san.php', php_content)

    return success

if __name__ == '__main__':
    deploy_yangsan_page()
