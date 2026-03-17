"""
嘉美净家政APP - Google Colab 打包脚本
使用步骤：
1. 打开 https://colab.research.google.com
2. 新建笔记本
3. 依次运行以下代码块
"""

# ========== 第1步：安装依赖 ==========
"""
!pip install -q buildozer cython
!apt-get update -qq > /dev/null 2>&1
!apt-get install -qq -y python3-pip build-essential git ffmpeg libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev zlib1g-dev libgstreamer1.0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good > /dev/null 2>&1
print('✅ 依赖安装完成')
"""

# ========== 第2步：创建项目目录 ==========
"""
import os
os.makedirs('/content/jiamaijing', exist_ok=True)
os.chdir('/content/jiamaijing')
!mkdir -p bin
print('✅ 项目目录创建完成')
"""

# ========== 第3步：初始化 buildozer ==========
"""
!buildozer init
print('✅ buildozer 初始化完成')
"""

# ========== 第4步：配置 buildozer.spec ==========
"""
spec_content = '''[app]
title = 嘉美净家政
package.name = jiamaijing
package.domain = com.jiamaijing
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,db
version = 1.0.0
requirements = python3,kivy==2.2.1,kivymd==1.1.1,pymysql,cryptography,requests,urllib3,charset-normalizer,idna,certifi
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.arch = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
'''.strip()

with open('buildozer.spec', 'w') as f:
    f.write(spec_content)
print('✅ buildozer.spec 配置完成')
"""

# ========== 第5步：准备主程序 ==========
"""
# 请手动上传 移动端_main.py 到左侧文件管理器
# 然后运行：
import shutil
import os

if os.path.exists('/content/移动端_main.py'):
    shutil.move('/content/移动端_main.py', '/content/jiamaijing/main.py')
    print('✅ 主程序文件已准备')
else:
    print('⚠️ 请先上传 移动端_main.py 文件')
"""

# ========== 第6步：开始打包（约10-20分钟） ==========
"""
!buildozer android debug -v
print('✅ 打包完成')
"""

# ========== 第7步：下载APK ==========
"""
import glob
import shutil

apk_files = glob.glob('/content/jiamaijing/bin/*.apk')
if apk_files:
    for apk in apk_files:
        print(f'📱 APK文件: {apk}')
        shutil.copy(apk, f'/content/{os.path.basename(apk)}')
    print('✅ APK已准备好，请在左侧文件管理器下载')
else:
    print('❌ 未找到APK文件')
"""
