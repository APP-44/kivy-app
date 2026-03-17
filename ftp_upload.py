#!/usr/bin/env python3
"""
FTP上传脚本 - 用于部署文件到西部数码虚拟主机
"""

import ftplib
import os
import sys

# FTP配置 - 西部数码虚拟主机
# FTP_HOST = 'scjmj.cn'
FTP_HOST = '211.149.140.78'  # IP地址
FTP_USER = 'shizhnegwheng'
FTP_PASS = '63zskcx5m8kk'

def upload_file(local_path, remote_name=None):
    """上传单个文件到FTP服务器"""
    if not os.path.exists(local_path):
        print(f"错误: 本地文件不存在 {local_path}")
        return False

    if remote_name is None:
        remote_name = os.path.basename(local_path)

    try:
        print(f"正在连接FTP服务器 {FTP_HOST}...")
        ftp = ftplib.FTP(FTP_HOST, timeout=30)
        ftp.set_debuglevel(0)

        print(f"正在登录...")
        ftp.login(FTP_USER, FTP_PASS)

        print(f"当前目录: {ftp.pwd()}")

        # 上传文件
        print(f"正在上传 {local_path} -> {remote_name}...")
        with open(local_path, 'rb') as f:
            ftp.storbinary(f'STOR {remote_name}', f)

        print(f"✓ 上传成功: {remote_name}")

        # 列出文件确认
        files = ftp.nlst()
        if remote_name in files:
            print(f"✓ 文件已确认在服务器上")

        ftp.quit()
        return True

    except Exception as e:
        print(f"✗ 上传失败: {e}")
        return False

def upload_to_wwwroot(local_path, remote_name=None):
    """上传到wwwroot目录（网站根目录）"""
    if not os.path.exists(local_path):
        print(f"错误: 本地文件不存在 {local_path}")
        return False

    if remote_name is None:
        remote_name = os.path.basename(local_path)

    try:
        print(f"正在连接FTP服务器 {FTP_HOST}...")
        ftp = ftplib.FTP(FTP_HOST, timeout=30)
        ftp.login(FTP_USER, FTP_PASS)

        print(f"当前目录: {ftp.pwd()}")

        # 尝试切换到wwwroot目录
        try:
            ftp.cwd('wwwroot')
            print(f"切换到wwwroot目录: {ftp.pwd()}")
        except:
            print("注意: 无法切换到wwwroot目录，将在当前目录上传")

        # 上传文件
        print(f"正在上传 {local_path} -> {remote_name}...")
        with open(local_path, 'rb') as f:
            ftp.storbinary(f'STOR {remote_name}', f)

        print(f"✓ 上传成功: {remote_name}")
        ftp.quit()
        return True

    except Exception as e:
        print(f"✗ 上传失败: {e}")
        return False

def list_remote_files():
    """列出远程服务器上的文件"""
    try:
        ftp = ftplib.FTP(FTP_HOST, timeout=30)
        ftp.login(FTP_USER, FTP_PASS)

        print(f"当前目录: {ftp.pwd()}")
        print("文件列表:")
        files = ftp.nlst()
        for f in files:
            print(f"  - {f}")

        ftp.quit()
        return True
    except Exception as e:
        print(f"✗ 列出文件失败: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python ftp_upload.py <本地文件路径> [远程文件名]")
        print("  或: python ftp_upload.py --list (列出远程文件)")
        sys.exit(1)

    if sys.argv[1] == '--list':
        list_remote_files()
    else:
        local_file = sys.argv[1]
        remote_file = sys.argv[2] if len(sys.argv) > 2 else None
        upload_to_wwwroot(local_file, remote_file)
