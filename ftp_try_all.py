#!/usr/bin/env python3
"""
尝试所有可能的FTP连接方式
"""

import ftplib
import socket
import ssl

def try_ftp_connect(host, port=21, username='', password='', timeout=10):
    """尝试FTP连接"""
    try:
        print(f"\n尝试连接 {host}:{port} ...")
        ftp = ftplib.FTP()
        ftp.connect(host, port, timeout=timeout)
        print(f"  连接成功!")

        if username and password:
            print(f"  尝试登录...")
            ftp.login(username, password)
            print(f"  登录成功!")
            print(f"  当前目录: {ftp.pwd()}")

        ftp.quit()
        return True
    except Exception as e:
        print(f"  失败: {e}")
        return False

def try_ftps_connect(host, port=990, username='', password='', timeout=10):
    """尝试FTPS (FTP over SSL)连接"""
    try:
        print(f"\n尝试FTPS连接 {host}:{port} ...")

        # 创建SSL上下文
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        ftp = ftplib.FTP_TLS(context=context)
        ftp.connect(host, port, timeout=timeout)
        print(f"  连接成功!")

        if username and password:
            print(f"  尝试登录...")
            ftp.login(username, password)
            print(f"  登录成功!")
            print(f"  当前目录: {ftp.pwd()}")

        ftp.quit()
        return True
    except Exception as e:
        print(f"  失败: {e}")
        return False

if __name__ == '__main__':
    # 配置
    hosts = ['scjmj.cn', '211.149.140.78']
    ftp_ports = [21, 2121, 10021]
    ftps_ports = [990, 989]
    username = 'shizhnegwheng'
    password = '63zskcx5m8kk'

    print("=== FTP连接测试 ===")

    # 尝试普通FTP
    for host in hosts:
        for port in ftp_ports:
            if try_ftp_connect(host, port, username, password):
                print(f"\n[成功] FTP可用: {host}:{port}")
                exit(0)

    # 尝试FTPS
    for host in hosts:
        for port in ftps_ports:
            if try_ftps_connect(host, port, username, password):
                print(f"\n[成功] FTPS可用: {host}:{port}")
                exit(0)

    print("\n[失败] 所有连接方式都失败了")
    print("\n可能的原因:")
    print("1. FTP服务未启用")
    print("2. 使用了非标准端口")
    print("3. 防火墙阻止了连接")
    print("4. 需要通过虚拟主机控制面板上传")
