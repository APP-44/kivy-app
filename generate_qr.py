#!/usr/bin/env python3
"""
生成杨三员工档案页面的二维码
"""

import qrcode
from PIL import Image
import os

def generate_employee_qr(employee_name, url, output_path):
    """生成员工档案二维码"""

    # 创建QR码实例
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    # 添加数据
    qr.add_data(url)
    qr.make(fit=True)

    # 生成图像
    img = qr.make_image(fill_color="#e85d04", back_color="white")

    # 转换为RGBA模式
    img = img.convert('RGBA')

    # 创建带标题的图像
    from PIL import ImageDraw, ImageFont

    # 添加底部文字区域
    title_height = 60
    new_height = img.size[1] + title_height

    # 创建新图像
    new_img = Image.new('RGBA', (img.size[0], new_height), 'white')
    new_img.paste(img, (0, 0))

    # 添加文字
    draw = ImageDraw.Draw(new_img)

    # 尝试使用系统字体
    try:
        # Windows字体
        font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 24)
        small_font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 16)
    except:
        try:
            # Linux字体
            font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 24)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 16)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()

    # 添加员工姓名
    text = f"{employee_name} - 员工档案"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (new_img.size[0] - text_width) // 2
    draw.text((text_x, img.size[1] + 10), text, fill="#e85d04", font=font)

    # 添加公司名称
    company_text = "四川嘉美净清洁服务"
    bbox2 = draw.textbbox((0, 0), company_text, font=small_font)
    company_width = bbox2[2] - bbox2[0]
    company_x = (new_img.size[0] - company_width) // 2
    draw.text((company_x, img.size[1] + 38), company_text, fill="#666666", font=small_font)

    # 保存图像
    new_img.save(output_path, 'PNG')
    print(f"[OK] 二维码已生成: {output_path}")
    print(f"  URL: {url}")

    return output_path

if __name__ == '__main__':
    # 杨三员工档案二维码
    employee_name = "杨三"
    url = "https://scjmj.cn/yang-san.php"
    output_path = "C:\\Users\\Administrator\\.qoderwork\\workspace\\mmsfmwhfvbss29v1\\outputs\\yang-san-qr.png"

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    generate_employee_qr(employee_name, url, output_path)
