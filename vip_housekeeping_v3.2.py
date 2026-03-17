"""
🏠 家政VIP客户管理系统 v3.1 - 修复版
修复：新增客户对话框按钮不可见问题
"""

import customtkinter as ctk
from PIL import Image, ImageDraw
import pymysql
import json
from datetime import datetime, timedelta
from tkinter import messagebox, filedialog
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import os
import sys
import csv
import numpy as np
import requests
import hashlib
import hmac
import base64
import urllib.parse

# ==================== 全局配置 ====================
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")

# API同步配置（西部数码虚拟主机）
API_CONFIG = {
    'enabled': True,  # 同步开关
    'url': 'https://scjmj.cn/api_sync.php',  # API地址
    'key': 'jiameijing2024',  # API密钥
}

# 短信服务配置
SMS_CONFIG = {
    'enabled': True,  # 短信开关已启用，最终审核通过后改为 True
    'provider': 'aliyun',  # 短信服务商
    'access_key_id': 'LTAI5t5YTsJaqc9in8nc32Ws',  # 阿里云AccessKey ID
    'access_key_secret': 'Se3h5SI3QGmv2ZOP6a7DUruAqQl7MX',  # 阿里云AccessKey Secret
    'sign_name': '四川嘉美净清洁服务有限公司',  # 短信签名
    'template_code_recharge': 'SMS_501736161',  # 充值成功模板
    'template_code_consume': 'SMS_501641171',  # 消费提醒模板
    'template_code_alert': 'SMS_501801174',  # 余额预警模板
    'service_phone': '08162348822',  # 客服电话（用于余额预警）
    'admin_phone': '18081246654',  # 郭总手机号，余额预警时同步发送
}

# 颜色配置 - 高端商务风格
COLORS = {
    "primary": "#1E3A8A",      # 深蓝
    "secondary": "#3B82F6",   # 亮蓝
    "accent": "#F59E0B",      # 金色强调
    "success": "#10B981",     # 绿色
    "warning": "#F59E0B",     # 橙色
    "danger": "#EF4444",      # 红色
    "bg_dark": "#0F172A",     # 深色背景
    "bg_card": "#1E293B",     # 卡片背景
    "text_light": "#F1F5F9",  # 浅色文字
    "text_muted": "#94A3B8",  # 灰色文字
    "border": "#334155"       # 边框色
}# ==================== 数据库管理类 ====================
# ==================== 短信服务类 ====================
class SMSService:
    """短信服务类 - 阿里云短信"""

    def __init__(self):
        self.enabled = SMS_CONFIG['enabled']
        self.access_key_id = SMS_CONFIG['access_key_id']
        self.access_key_secret = SMS_CONFIG['access_key_secret']
        self.sign_name = SMS_CONFIG['sign_name']

    def _sign(self, params, access_key_secret):
        """生成阿里云API签名"""
        # 排序参数
        sorted_params = sorted(params.items())
        # 构造待签名字符串
        canonical_query_string = urllib.parse.urlencode(sorted_params)
        # 构造签名字符串
        string_to_sign = f"GET&%2F&{urllib.parse.quote(canonical_query_string, safe='')}".encode('utf-8')
        # 计算签名
        key = (access_key_secret + "&").encode('utf-8')
        signature = base64.b64encode(hmac.new(key, string_to_sign, hashlib.sha1).digest()).decode('utf-8')
        return signature

    def send_sms(self, phone, template_code, template_param):
        """发送短信"""
        if not self.enabled:
            # 短信未启用，只记录日志
            print(f"[短信模拟] 发送给 {phone}: 模板={template_code}, 参数={template_param}")
            return True, "短信模拟发送成功（短信服务未启用）"

        try:
            import time
            import uuid

            # 构造请求参数
            params = {
                'Action': 'SendSms',
                'Version': '2017-05-25',
                'RegionId': 'cn-hangzhou',
                'PhoneNumbers': phone,
                'SignName': self.sign_name,
                'TemplateCode': template_code,
                'TemplateParam': json.dumps(template_param, ensure_ascii=False),
                'AccessKeyId': self.access_key_id,
                'Format': 'JSON',
                'SignatureMethod': 'HMAC-SHA1',
                'SignatureVersion': '1.0',
                'SignatureNonce': str(uuid.uuid4()),
                'Timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }

            # 生成签名
            params['Signature'] = self._sign(params, self.access_key_secret)

            # 发送请求
            url = "https://dysmsapi.aliyuncs.com"
            response = requests.get(url, params=params, timeout=10)
            result = response.json()

            if result.get('Code') == 'OK':
                return True, "短信发送成功"
            else:
                return False, f"短信发送失败: {result.get('Message')}"

        except Exception as e:
            return False, f"短信发送异常: {str(e)}"

    def send_recharge_notification(self, phone, name, amount, times, remain):
        """发送充值通知
        模板：尊敬的${name}，您已成功充值${amount}元（${times}次），当前余额${remain}次。感谢支持！
        """
        template_code = SMS_CONFIG['template_code_recharge']
        param = {
            'name': name,
            'amount': str(amount),
            'times': str(times),
            'remain': str(remain)
        }
        return self.send_sms(phone, template_code, param)

    def send_consume_notification(self, phone, name, service_type, amount, balance):
        """发送消费通知
        模板：尊敬的${name}，您本次${service}服务已完成，消费${amount}元，账户余额${balance}元。感谢选择四川嘉美净清洁服务有限公司！
        """
        template_code = SMS_CONFIG['template_code_consume']
        param = {
            'name': name,
            'service': service_type,
            'amount': str(amount),
            'balance': str(balance)
        }
        return self.send_sms(phone, template_code, param)

    def send_low_balance_alert(self, phone, name, balance):
        """发送余额不足提醒
        模板：尊敬的${name}，您的账户余额不足（剩余${balance}元），请及时充值。客服电话：${phone}。
        """
        template_code = SMS_CONFIG['template_code_alert']
        param = {
            'name': name,
            'balance': str(balance),
            'phone': SMS_CONFIG['service_phone']
        }
        return self.send_sms(phone, template_code, param)


# ==================== 数据库管理类 ====================
class DatabaseManager:
    def __init__(self):
        self.db_config = {
            'host': '106.14.254.13',
            'port': 3306,
            'user': 'app',
            'password': 'app123456',
            'database': 'housekeeping',
            'charset': 'utf8mb4',
            'autocommit': False
        }
        self.init_database()

    def get_connection(self):
        return pymysql.connect(**self.db_config)
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # VIP客户主表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vip_customers (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                phone VARCHAR(20) UNIQUE NOT NULL,
                address VARCHAR(255),
                id_card VARCHAR(18),
                register_date DATE,
                status VARCHAR(20) DEFAULT '正常',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')

        # 充值记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recharge_records (
                id INT PRIMARY KEY AUTO_INCREMENT,
                customer_id INT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                times INT NOT NULL,
                gift_amount DECIMAL(10,2) DEFAULT 0,
                gift_times INT DEFAULT 0,
                total_amount DECIMAL(10,2) NOT NULL,
                total_times INT NOT NULL,
                recharge_date DATE,
                expiry_date DATE,
                payment_method VARCHAR(50),
                operator VARCHAR(50),
                notes TEXT,
                FOREIGN KEY (customer_id) REFERENCES vip_customers(id)
            )
        ''')

        # 消费记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consumption_records (
                id INT PRIMARY KEY AUTO_INCREMENT,
                customer_id INT NOT NULL,
                service_type VARCHAR(100) NOT NULL,
                consume_amount DECIMAL(10,2) NOT NULL,
                consume_times INT NOT NULL,
                remaining_amount DECIMAL(10,2) NOT NULL,
                remaining_times INT NOT NULL,
                service_date DATE,
                service_person VARCHAR(50),
                satisfaction INT,
                notes TEXT,
                FOREIGN KEY (customer_id) REFERENCES vip_customers(id)
            )
        ''')

        # 预警记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INT PRIMARY KEY AUTO_INCREMENT,
                customer_id INT NOT NULL,
                alert_type VARCHAR(50) NOT NULL,
                alert_level VARCHAR(20),
                message TEXT,
                is_resolved TINYINT(1) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP NULL,
                FOREIGN KEY (customer_id) REFERENCES vip_customers(id)
            )
        ''')

        # 员工信息表（电子名片模块）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(50) NOT NULL COMMENT '姓名',
                age INT COMMENT '年龄',
                work_years INT DEFAULT 0 COMMENT '工龄（年）',
                skills TEXT COMMENT '技能，逗号分隔（保洁/开荒/月嫂）',
                photo_path VARCHAR(255) COMMENT '照片相对路径',
                rating DECIMAL(2,1) DEFAULT 5.0 COMMENT '评分1-5',
                review_count INT DEFAULT 0 COMMENT '评价数量',
                status VARCHAR(20) DEFAULT '在职' COMMENT '在职/离职',
                id_card VARCHAR(18) COMMENT '身份证号（内部用）',
                phone VARCHAR(20) COMMENT '手机号（内部用）',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
    
    def add_customer(self, name, phone, address="", id_card="", notes=""):
        """添加新客户"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            print(f"【调试】添加客户: {name}, {phone}")
            
            cursor.execute('''
                INSERT INTO vip_customers (name, phone, address, id_card, notes)
                VALUES (%s, %s, %s, %s, %s)
            ''', (name, phone, address, id_card, notes))
            
            conn.commit()
            customer_id = cursor.lastrowid
            
            print(f"【调试】添加成功，ID: {customer_id}")
            return True, customer_id
            
        except pymysql.IntegrityError:
            return False, "电话号码已存在"
        except Exception as e:
            print(f"【调试】添加错误: {e}")
            return False, str(e)
        finally:
            if conn:
                conn.close()
    
    def get_customer(self, customer_id):
        """获取客户详细信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM vip_customers WHERE id = %s', (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            conn.close()
            return None
        
        cursor.execute('''
            SELECT COALESCE(SUM(total_amount), 0), COALESCE(SUM(total_times), 0)
            FROM recharge_records WHERE customer_id = %s
        ''', (customer_id,))
        total_recharge = cursor.fetchone()
        
        cursor.execute('''
            SELECT COALESCE(SUM(consume_amount), 0), COALESCE(SUM(consume_times), 0)
            FROM consumption_records WHERE customer_id = %s
        ''', (customer_id,))
        total_consume = cursor.fetchone()
        
        cursor.execute('''
            SELECT * FROM recharge_records
            WHERE customer_id = %s ORDER BY recharge_date DESC LIMIT 1
        ''', (customer_id,))
        last_recharge = cursor.fetchone()
        
        cursor.execute('''
            SELECT * FROM consumption_records
            WHERE customer_id = %s ORDER BY service_date DESC LIMIT 5
        ''', (customer_id,))
        recent_consumptions = cursor.fetchall()
        
        conn.close()
        
        remaining_amount = (total_recharge[0] or 0) - (total_consume[0] or 0)
        remaining_times = (total_recharge[1] or 0) - (total_consume[1] or 0)
        
        return {
            'id': customer[0],
            'name': customer[1],
            'phone': customer[2],
            'address': customer[3],
            'id_card': customer[4],
            'register_date': customer[5],
            'status': customer[6],
            'notes': customer[8],
            'total_recharge_amount': total_recharge[0] or 0,
            'total_recharge_times': total_recharge[1] or 0,
            'total_consume_amount': total_consume[0] or 0,
            'total_consume_times': total_consume[1] or 0,
            'remaining_amount': remaining_amount,
            'remaining_times': remaining_times,
            'last_recharge': last_recharge,
            'recent_consumptions': recent_consumptions
        }
    
    def get_all_customers(self, search=""):
        """获取所有客户列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if search:
            cursor.execute('''
                SELECT c.*,
                    COALESCE((SELECT SUM(total_amount) FROM recharge_records WHERE customer_id = c.id), 0) -
                    COALESCE((SELECT SUM(consume_amount) FROM consumption_records WHERE customer_id = c.id), 0) as balance,
                    COALESCE((SELECT SUM(total_times) FROM recharge_records WHERE customer_id = c.id), 0) -
                    COALESCE((SELECT SUM(consume_times) FROM consumption_records WHERE customer_id = c.id), 0) as times
                FROM vip_customers c
                WHERE c.name LIKE %s OR c.phone LIKE %s OR c.address LIKE %s
                ORDER BY c.created_at DESC
            ''', (f'%{search}%', f'%{search}%', f'%{search}%'))
        else:
            cursor.execute('''
                SELECT c.*,
                    COALESCE((SELECT SUM(total_amount) FROM recharge_records WHERE customer_id = c.id), 0) -
                    COALESCE((SELECT SUM(consume_amount) FROM consumption_records WHERE customer_id = c.id), 0) as balance,
                    COALESCE((SELECT SUM(total_times) FROM recharge_records WHERE customer_id = c.id), 0) -
                    COALESCE((SELECT SUM(consume_times) FROM consumption_records WHERE customer_id = c.id), 0) as times
                FROM vip_customers c
                ORDER BY c.created_at DESC
            ''')
        
        customers = cursor.fetchall()
        conn.close()
        return customers
    
    def recharge(self, customer_id, amount, times, gift_amount=0, gift_times=0, 
                 payment_method="现金", operator="管理员", notes="", months_valid=12):
        """客户充值"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            total_amount = amount + gift_amount
            total_times = times + gift_times
            
            expiry_date = (datetime.now() + timedelta(days=30*months_valid)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                INSERT INTO recharge_records
                (customer_id, amount, times, gift_amount, gift_times, total_amount, total_times,
                 expiry_date, payment_method, operator, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (customer_id, amount, times, gift_amount, gift_times, total_amount, total_times,
                  expiry_date, payment_method, operator, notes))
            
            conn.commit()
            conn.close()
            
            self.check_alerts(customer_id)
            
            return True, "充值成功"
        except Exception as e:
            return False, str(e)
    
    def get_recharge_history(self, customer_id):
        """获取充值历史"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM recharge_records
            WHERE customer_id = %s ORDER BY recharge_date DESC
        ''', (customer_id,))
        records = cursor.fetchall()
        conn.close()
        return records
    
    def consume(self, customer_id, service_type, consume_times=1, service_person="", 
                satisfaction=5, notes=""):
        """消费扣减"""
        try:
            customer = self.get_customer(customer_id)
            if not customer:
                return False, "客户不存在"
            
            current_amount = customer['remaining_amount']
            current_times = customer['remaining_times']
            
            if customer['total_recharge_times'] > 0:
                unit_price = customer['total_recharge_amount'] / customer['total_recharge_times']
            else:
                unit_price = 0
            
            consume_amount = unit_price * consume_times
            
            if current_times < consume_times:
                return False, f"次数不足，当前剩余{current_times}次"
            
            if current_amount < consume_amount:
                return False, f"余额不足，当前剩余¥{current_amount:.2f}"
            
            new_amount = current_amount - consume_amount
            new_times = current_times - consume_times
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO consumption_records
                (customer_id, service_type, consume_amount, consume_times,
                 remaining_amount, remaining_times, service_person, satisfaction, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (customer_id, service_type, consume_amount, consume_times,
                  new_amount, new_times, service_person, satisfaction, notes))
            
            conn.commit()
            conn.close()
            
            self.check_alerts(customer_id)
            
            return True, {
                'consume_amount': consume_amount,
                'remaining_amount': new_amount,
                'remaining_times': new_times
            }
            
        except Exception as e:
            return False, str(e)
    
    def check_alerts(self, customer_id=None):
        """检查并生成预警，返回需要发送短信预警的客户列表"""
        conn = self.get_connection()
        cursor = conn.cursor()

        alert_customers = []  # 需要发送短信预警的客户

        if customer_id:
            cursor.execute('SELECT id FROM vip_customers WHERE id = %s', (customer_id,))
            customer_ids = [customer_id]
        else:
            cursor.execute('SELECT id FROM vip_customers WHERE status = "正常"')
            customer_ids = [row[0] for row in cursor.fetchall()]

        for cid in customer_ids:
            customer = self.get_customer(cid)
            if not customer:
                continue

            cursor.execute('''
                UPDATE alerts SET is_resolved = 1, resolved_at = NOW()
                WHERE customer_id = %s AND is_resolved = 0
            ''', (cid,))

            if customer['remaining_amount'] < 100 or customer['remaining_times'] < 1:
                level = "高" if customer['remaining_amount'] <= 0 or customer['remaining_times'] <= 0 else "中"
                cursor.execute('''
                    INSERT INTO alerts (customer_id, alert_type, alert_level, message)
                    VALUES (%s, %s, %s, %s)
                ''', (cid, '余额不足', level,
                      f"客户{customer['name']}余额¥{customer['remaining_amount']:.2f}，剩余{customer['remaining_times']}次"))
                # 添加到短信预警列表
                alert_customers.append({
                    'id': cid,
                    'name': customer['name'],
                    'phone': customer['phone'],
                    'balance': customer['remaining_amount'],
                    'times': customer['remaining_times']
                })

            if customer['last_recharge'] and customer['last_recharge'][8]:
                try:
                    expiry = datetime.strptime(customer['last_recharge'][8], '%Y-%m-%d')
                    days_left = (expiry - datetime.now()).days
                    if days_left <= 30 and days_left > 0:
                        cursor.execute('''
                            INSERT INTO alerts (customer_id, alert_type, alert_level, message)
                            VALUES (%s, %s, %s, %s)
                        ''', (cid, '即将过期', '中',
                              f"客户{customer['name']}的年卡将在{days_left}天后过期"))
                except (ValueError, TypeError):
                    # 日期格式错误或为空，跳过过期检查
                    pass

        conn.commit()
        conn.close()
        return alert_customers
    
    def get_alerts(self, unresolved_only=True):
        """获取预警列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if unresolved_only:
            cursor.execute('''
                SELECT a.*, c.name, c.phone
                FROM alerts a
                JOIN vip_customers c ON a.customer_id = c.id
                WHERE a.is_resolved = 0
                ORDER BY a.created_at DESC
            ''')
        else:
            cursor.execute('''
                SELECT a.*, c.name, c.phone
                FROM alerts a
                JOIN vip_customers c ON a.customer_id = c.id
                ORDER BY a.created_at DESC
                LIMIT 50
            ''')
        
        alerts = cursor.fetchall()
        conn.close()
        return alerts
    
    def get_dashboard_stats(self):
        """获取仪表盘统计数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM vip_customers')
        total_customers = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT customer_id) FROM recharge_records')
        vip_customers = cursor.fetchone()[0]
        
        cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM recharge_records')
        total_recharge = cursor.fetchone()[0]
        
        cursor.execute('SELECT COALESCE(SUM(times), 0) FROM recharge_records')
        total_times = cursor.fetchone()[0]
        
        cursor.execute('SELECT COALESCE(SUM(consume_amount), 0) FROM consumption_records')
        total_consume = cursor.fetchone()[0]
        
        cursor.execute('SELECT COALESCE(SUM(consume_times), 0) FROM consumption_records')
        total_consume_times = cursor.fetchone()[0]
        
        current_balance = total_recharge - total_consume
        current_times = total_times - total_consume_times
        
        cursor.execute('''
            SELECT COUNT(*) FROM vip_customers
            WHERE DATE_FORMAT(created_at, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m')
        ''')
        new_this_month = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM alerts WHERE is_resolved = 0')
        alert_count = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT DATE(service_date) as day, SUM(consume_amount), SUM(consume_times)
            FROM consumption_records
            WHERE service_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY day
            ORDER BY day
        ''')
        weekly_trend = cursor.fetchall()
        
        cursor.execute('''
            SELECT
                CASE
                    WHEN remaining_times >= 20 THEN '高价值'
                    WHEN remaining_times >= 10 THEN '活跃'
                    WHEN remaining_times > 0 THEN '低活跃'
                    ELSE '需充值'
                END as level,
                COUNT(*) as count
            FROM (
                SELECT c.id,
                    COALESCE((SELECT SUM(total_times) FROM recharge_records WHERE customer_id = c.id), 0) -
                    COALESCE((SELECT SUM(consume_times) FROM consumption_records WHERE customer_id = c.id), 0) as remaining_times
                FROM vip_customers c
            ) sub
            GROUP BY level
        ''')
        level_distribution = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_customers': total_customers,
            'vip_customers': vip_customers,
            'total_recharge': total_recharge,
            'total_times': total_times,
            'total_consume': total_consume,
            'total_consume_times': total_consume_times,
            'current_balance': current_balance,
            'current_times': current_times,
            'new_this_month': new_this_month,
            'alert_count': alert_count,
            'weekly_trend': weekly_trend,
            'level_distribution': level_distribution
        }
    
    def get_revenue_statistics(self, period="本月"):
        """获取营收统计数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if period == "本月":
            date_filter = "DATE_FORMAT(date, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m')"
        elif period == "上月":
            date_filter = "DATE_FORMAT(date, '%Y-%m') = DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 1 MONTH), '%Y-%m')"
        elif period == "本季度":
            date_filter = "QUARTER(date) = QUARTER(NOW()) AND YEAR(date) = YEAR(NOW())"
        elif period == "本年度":
            date_filter = "YEAR(date) = YEAR(NOW())"
        else:
            date_filter = "1=1"
        
        recharge_filter = date_filter.replace('date', 'recharge_date')
        service_filter = date_filter.replace('date', 'service_date')

        cursor.execute(f'''
            SELECT
                dates.date as day,
                COALESCE(SUM(r.amount), 0) as recharge,
                COALESCE(SUM(r.times), 0) as r_times,
                COALESCE(SUM(c.consume_amount), 0) as consume,
                COALESCE(SUM(c.consume_times), 0) as c_times
            FROM (
                SELECT DISTINCT DATE(recharge_date) as date
                FROM recharge_records
                WHERE {recharge_filter}
                UNION
                SELECT DISTINCT DATE(service_date) as date
                FROM consumption_records
                WHERE {service_filter}
            ) dates
            LEFT JOIN recharge_records r ON DATE(r.recharge_date) = dates.date
            LEFT JOIN consumption_records c ON DATE(c.service_date) = dates.date
            GROUP BY dates.date
            ORDER BY dates.date DESC
            LIMIT 31
        ''')
        
        daily_data = cursor.fetchall()
        daily_data = [(d[0], d[1], int(d[2]), d[3], int(d[4]), d[1]-d[3]) for d in daily_data]
        
        total_recharge = sum(d[1] for d in daily_data)
        total_consume = sum(d[3] for d in daily_data)
        profit = total_recharge - total_consume
        
        service_filter = date_filter.replace('date', 'service_date')
        cursor.execute(f'''
            SELECT AVG(consume_amount) FROM consumption_records
            WHERE {service_filter}
        ''')
        avg_order = cursor.fetchone()[0] or 0
        
        recharge_filter = date_filter.replace('date', 'recharge_date')
        cursor.execute(f'''
            SELECT payment_method, SUM(amount) as total
            FROM recharge_records
            WHERE {recharge_filter}
            GROUP BY payment_method
            ORDER BY total DESC
        ''')
        payment_methods = cursor.fetchall()
        
        conn.close()
        
        return {
            'daily_data': daily_data,
            'total_recharge': total_recharge,
            'total_consume': total_consume,
            'profit': profit,
            'avg_order': avg_order,
            'payment_methods': payment_methods
        }
    
    def get_customer_value_distribution(self):
        """获取客户价值分层"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT
                CASE
                    WHEN remaining_value >= 5000 THEN '钻石VIP'
                    WHEN remaining_value >= 2000 THEN '白金VIP'
                    WHEN remaining_value >= 1000 THEN '黄金VIP'
                    WHEN remaining_value >= 500 THEN '白银VIP'
                    WHEN remaining_value > 0 THEN '普通VIP'
                    ELSE '零余额'
                END as level,
                COUNT(*) as count,
                SUM(remaining_value) as total_value
            FROM (
                SELECT c.id,
                    COALESCE((SELECT SUM(total_amount) FROM recharge_records WHERE customer_id = c.id), 0) -
                    COALESCE((SELECT SUM(consume_amount) FROM consumption_records WHERE customer_id = c.id), 0) as remaining_value
                FROM vip_customers c
                WHERE c.status = '正常'
            ) sub
            GROUP BY level
            ORDER BY total_value DESC
        ''')
        
        result = cursor.fetchall()
        conn.close()
        return result
    
    def get_monthly_growth(self):
        """获取月度客户增长数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT
                DATE_FORMAT(created_at, '%Y-%m') as month,
                COUNT(*) as new_customers,
                (SELECT COUNT(*) FROM vip_customers
                 WHERE status = '冻结'
                 AND DATE_FORMAT(updated_at, '%Y-%m') = DATE_FORMAT(v.created_at, '%Y-%m')) as churned
            FROM vip_customers v
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
            GROUP BY DATE_FORMAT(created_at, '%Y-%m')
            ORDER BY month
        ''')
        
        result = cursor.fetchall()
        conn.close()
        return result
    
    def get_service_type_stats(self):
        """获取服务类型统计"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT
                service_type,
                COUNT(*) as count,
                SUM(consume_amount) as total_amount,
                AVG(satisfaction) as avg_satisfaction
            FROM consumption_records
            WHERE service_date >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
            GROUP BY service_type
            ORDER BY count DESC
        ''')
        
        result = cursor.fetchall()
        conn.close()
        return result
    
    def get_satisfaction_stats(self):
        """获取满意度统计"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT satisfaction, COUNT(*) as count
            FROM consumption_records
            WHERE satisfaction IS NOT NULL
            AND service_date >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
            GROUP BY satisfaction
            ORDER BY satisfaction
        ''')
        
        result = cursor.fetchall()
        conn.close()
        return result
    
    def get_daily_revenue_history(self, days=90):
        """获取每日营收历史"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT
                dates.date as day,
                COALESCE(SUM(r.amount), 0) - COALESCE(SUM(c.consume_amount), 0) as net_revenue
            FROM (
                SELECT DISTINCT DATE(recharge_date) as date
                FROM recharge_records
                WHERE recharge_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                UNION
                SELECT DISTINCT DATE(service_date) as date
                FROM consumption_records
                WHERE service_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ) dates
            LEFT JOIN recharge_records r ON DATE(r.recharge_date) = dates.date
            LEFT JOIN consumption_records c ON DATE(c.service_date) = dates.date
            GROUP BY dates.date
            ORDER BY dates.date
        ''', (days, days))
        
        result = cursor.fetchall()
        conn.close()
        return result

    # ==================== 员工管理方法 ====================
    def sync_employee_to_virtualhost(self, employee_id, action='add'):
        """同步员工数据到西部数码虚拟主机"""
        if not API_CONFIG['enabled']:
            return True, "同步已禁用"

        try:
            # 获取员工信息
            employee = self.get_employee(employee_id)
            if not employee:
                return False, "员工不存在"

            # 准备同步数据
            data = {
                'action': action,
                'id': employee['id'],
                'name': employee['name'],
                'age': employee['age'] if employee['age'] else '',
                'work_years': employee['work_years'] if employee['work_years'] else 0,
                'skills': employee['skills'] if employee['skills'] else '',
                'photo_path': employee['photo_path'] if employee['photo_path'] else '',
                'rating': employee['rating'],
                'review_count': employee['review_count'],
                'status': employee['status']
            }

            # 发送API请求
            print(f"[调试] 正在同步到: {API_CONFIG['url']}")
            print(f"[调试] 数据: {data}")
            
            # 将所有数据放在POST中传递（使用JSON格式更可靠）
            post_data = {
                'key': API_CONFIG['key'],
                'action': data['action'],
                'id': data['id'],
                'name': data['name'],
                'age': data['age'],
                'work_years': data['work_years'],
                'skills': data['skills'],
                'photo_path': data['photo_path'],
                'rating': data['rating'],
                'review_count': data['review_count'],
                'status': data['status']
            }
            
            # 虚拟主机限制POST，使用GET方式传递所有数据
            import urllib.parse
            params = {
                'key': API_CONFIG['key'],
                'action': data['action'],
                'id': data['id'],
                'name': data['name'],
                'age': data['age'],
                'work_years': data['work_years'],
                'skills': data['skills'],
                'photo_path': data['photo_path'],
                'rating': data['rating'],
                'review_count': data['review_count'],
                'status': data['status']
            }
            
            # 构建带参数的URL
            query_string = urllib.parse.urlencode(params, encoding='utf-8')
            full_url = f"{API_CONFIG['url']}?{query_string}"
            
            print(f"[调试] 请求URL: {full_url[:200]}...")
            
            response = requests.get(
                full_url,
                timeout=10
            )
            
            print(f"[调试] 响应: {response.text}")
            result = response.json()
            if result.get('success'):
                print(f"[同步成功] 员工 {employee['name']} 已同步到虚拟主机")
                return True, result.get('message')
            else:
                print(f"[同步失败] {result.get('message')}")
                return False, result.get('message')

        except Exception as e:
            print(f"[同步异常] {str(e)}")
            return False, str(e)

    def add_employee(self, name, age=None, work_years=0, skills="", photo_path="",
                     id_card="", phone="", status="在职"):
        """添加新员工"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO employees (name, age, work_years, skills, photo_path,
                                       id_card, phone, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (name, age, work_years, skills, photo_path, id_card, phone, status))

            conn.commit()
            employee_id = cursor.lastrowid

            # 同步到虚拟主机
            self.sync_employee_to_virtualhost(employee_id, 'add')

            return True, employee_id

        except Exception as e:
            return False, str(e)
        finally:
            if conn:
                conn.close()

    def update_employee(self, employee_id, **kwargs):
        """更新员工信息"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            allowed_fields = ['name', 'age', 'work_years', 'skills', 'photo_path',
                            'rating', 'review_count', 'status', 'id_card', 'phone']
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

            if not updates:
                return False, "没有可更新的字段"

            set_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
            values = list(updates.values()) + [employee_id]

            cursor.execute(f'UPDATE employees SET {set_clause} WHERE id = %s', values)

            conn.commit()

            # 同步到虚拟主机
            self.sync_employee_to_virtualhost(employee_id, 'update')

            return True, "更新成功"

        except Exception as e:
            return False, str(e)
        finally:
            if conn:
                conn.close()

    def delete_employee(self, employee_id):
        """删除员工（软删除，改为离职状态）"""
        result = self.update_employee(employee_id, status='离职')
        if result[0]:
            # 同步到虚拟主机
            self.sync_employee_to_virtualhost(employee_id, 'delete')
        return result

    def get_employee(self, employee_id):
        """获取单个员工详情"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM employees WHERE id = %s', (employee_id,))
        employee = cursor.fetchone()
        conn.close()

        if not employee:
            return None

        return {
            'id': employee[0],
            'name': employee[1],
            'age': employee[2],
            'work_years': employee[3],
            'skills': employee[4],
            'photo_path': employee[5],
            'rating': float(employee[6]) if employee[6] else 5.0,
            'review_count': employee[7],
            'status': employee[8],
            'id_card': employee[9],
            'phone': employee[10],
            'created_at': employee[11]
        }

    def get_all_employees(self, search="", status=None):
        """获取员工列表"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM employees WHERE 1=1'
        params = []

        if search:
            query += ' AND (name LIKE %s OR skills LIKE %s)'
            params.extend([f'%{search}%', f'%{search}%'])

        if status:
            query += ' AND status = %s'
            params.append(status)

        query += ' ORDER BY created_at DESC'

        cursor.execute(query, params)
        employees = cursor.fetchall()
        conn.close()

        result = []
        for emp in employees:
            result.append({
                'id': emp[0],
                'name': emp[1],
                'age': emp[2],
                'work_years': emp[3],
                'skills': emp[4],
                'photo_path': emp[5],
                'rating': float(emp[6]) if emp[6] else 5.0,
                'review_count': emp[7],
                'status': emp[8]
            })
        return result

    def get_employee_stats(self):
        """获取员工统计信息"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM employees WHERE status = "在职"')
        active_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM employees WHERE status = "离职"')
        inactive_count = cursor.fetchone()[0]

        cursor.execute('SELECT AVG(rating) FROM employees WHERE status = "在职"')
        avg_rating = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT skills FROM employees WHERE status = '在职' AND skills IS NOT NULL
        ''')
        skills_data = cursor.fetchall()

        # 统计技能分布
        skill_count = {}
        for row in skills_data:
            if row[0]:
                for skill in row[0].split(','):
                    skill = skill.strip()
                    if skill:
                        skill_count[skill] = skill_count.get(skill, 0) + 1

        conn.close()

        return {
            'active_count': active_count,
            'inactive_count': inactive_count,
            'avg_rating': round(float(avg_rating), 1),
            'skill_distribution': skill_count
        }

# ==================== 主应用类 ====================
class VIPHousekeepingApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("🏠 家政VIP客户管理系统 v3.0")
        self.geometry("1400x800")
        self.minsize(1200, 700)
        
        self.db = DatabaseManager()
        self.sms = SMSService()
        self.current_customer_id = None
        
        self.create_layout()
        self.create_pages()
        
        self.show_page("dashboard")
        self.refresh_alerts()
    
    def create_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 左侧导航栏
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=COLORS["bg_dark"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(30, 20), padx=30, fill="x")
        
        ctk.CTkLabel(logo_frame, text="🏠 家政管家", font=ctk.CTkFont(size=26, weight="bold"), text_color=COLORS["text_light"]).pack(anchor="w")
        ctk.CTkLabel(logo_frame, text="VIP客户管理系统", font=ctk.CTkFont(size=14), text_color=COLORS["text_muted"]).pack(anchor="w", pady=(5, 0))
        
        ctk.CTkFrame(self.sidebar, height=2, fg_color=COLORS["border"]).pack(fill="x", padx=30, pady=20)
        
        # 导航按钮
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊", "数据仪表盘", COLORS["secondary"]),
            ("customers", "👥", "VIP客户管理", COLORS["secondary"]),
            ("employees", "🧑‍💼", "员工管理", COLORS["accent"]),
            ("recharge", "💳", "充值管理", COLORS["success"]),
            ("consume", "📝", "消费登记", COLORS["accent"]),
            ("alerts", "🔔", "预警中心", COLORS["danger"]),
            ("stats", "📈", "统计报表", COLORS["secondary"]),
        ]
        
        for page_id, icon, text, color in nav_items:
            btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            btn_frame.pack(fill="x", padx=20, pady=5)
            
            btn = ctk.CTkButton(
                btn_frame,
                text=f" {icon}  {text}",
                anchor="w",
                height=50,
                corner_radius=12,
                fg_color="transparent",
                text_color=COLORS["text_muted"],
                hover_color=COLORS["bg_card"],
                font=ctk.CTkFont(size=15),
                command=lambda p=page_id: self.show_page(p)
            )
            btn.pack(fill="x")
            self.nav_buttons[page_id] = btn
            
            if page_id == "alerts":
                self.alert_badge = ctk.CTkLabel(
                    btn, text="0", width=24, height=24,
                    corner_radius=12, fg_color=COLORS["danger"],
                    text_color="white", font=ctk.CTkFont(size=12, weight="bold")
                )
                self.alert_badge.place(relx=0.9, rely=0.5, anchor="center")
                self.alert_badge.place_forget()
        
        ctk.CTkFrame(self.sidebar, height=2, fg_color=COLORS["border"]).pack(fill="x", padx=30, pady=20)
        
        info_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        info_frame.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(info_frame, text=f"系统版本: v3.0\n日期: {datetime.now().strftime('%Y-%m-%d')}", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(anchor="w")
        
        # 右侧主内容区
        self.main_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"])
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # 顶部标题栏
        self.header = ctk.CTkFrame(self.main_frame, height=70, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 10))
        self.header.grid_propagate(False)
        
        self.page_title = ctk.CTkLabel(self.header, text="数据仪表盘", font=ctk.CTkFont(size=28, weight="bold"), text_color=COLORS["text_light"])
        self.page_title.pack(side="left")
        
        self.quick_actions = ctk.CTkFrame(self.header, fg_color="transparent")
        self.quick_actions.pack(side="right")
        
        # 页面容器
        self.content_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_container.grid(row=1, column=0, sticky="nsew", padx=25, pady=10)
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)
    
    def create_pages(self):
        self.pages = {}
        
        for name in ["dashboard", "customers", "employees", "recharge", "consume", "alerts", "stats"]:
            page = ctk.CTkFrame(self.content_container, fg_color="transparent")
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[name] = page

        self.init_dashboard()
        self.init_customers()
        self.init_employees()
        self.init_recharge()
        self.init_consume()
        self.init_alerts()
        self.init_stats()
    
    def show_page(self, page_id):
        self.pages[page_id].tkraise()
        
        titles = {
            "dashboard": "数据仪表盘",
            "customers": "VIP客户管理",
            "employees": "员工管理",
            "recharge": "充值管理",
            "consume": "消费登记",
            "alerts": "预警中心",
            "stats": "统计报表"
        }
        self.page_title.configure(text=titles.get(page_id, "未知页面"))
        
        for pid, btn in self.nav_buttons.items():
            if pid == page_id:
                btn.configure(fg_color=COLORS["primary"], text_color=COLORS["text_light"], font=ctk.CTkFont(size=15, weight="bold"))
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_muted"], font=ctk.CTkFont(size=15))
        
        if page_id == "dashboard":
            self.refresh_dashboard()
        elif page_id == "customers":
            self.refresh_customer_list()
        elif page_id == "employees":
            self.refresh_employee_list()
        elif page_id == "alerts":
            self.refresh_alerts_list()
    
    # ==================== 仪表盘页面 ====================
    def init_dashboard(self):
        page = self.pages["dashboard"]
        
        cards_frame = ctk.CTkFrame(page, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(0, 20))
        
        self.stat_cards = {}
        card_configs = [
            ("total_customers", "总客户数", "👥", COLORS["secondary"]),
            ("vip_customers", "VIP客户", "👑", COLORS["accent"]),
            ("current_balance", "账户余额", "💰", COLORS["success"]),
            ("current_times", "剩余次数", "🎫", COLORS["secondary"]),
            ("alert_count", "预警数量", "⚠️", COLORS["danger"]),
            ("new_this_month", "本月新增", "📈", COLORS["success"])
        ]
        
        for i, (key, title, icon, color) in enumerate(card_configs):
            card = ctk.CTkFrame(cards_frame, fg_color=COLORS["bg_dark"], corner_radius=16, border_width=1, border_color=COLORS["border"])
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            card.grid_columnconfigure(0, weight=1)
            
            header_frame = ctk.CTkFrame(card, fg_color="transparent")
            header_frame.pack(fill="x", padx=20, pady=(20, 10))
            
            ctk.CTkLabel(header_frame, text=f"{icon} {title}", font=ctk.CTkFont(size=14), text_color=COLORS["text_muted"]).pack(side="left")
            
            self.stat_cards[key] = ctk.CTkLabel(card, text="0", font=ctk.CTkFont(size=32, weight="bold"), text_color=color)
            self.stat_cards[key].pack(pady=(0, 20))
        
        cards_frame.grid_columnconfigure((0,1,2,3,4,5), weight=1)
        
        charts_frame = ctk.CTkFrame(page, fg_color="transparent")
        charts_frame.pack(fill="both", expand=True, pady=20)
        charts_frame.grid_columnconfigure((0, 1), weight=1)
        charts_frame.grid_rowconfigure(0, weight=1)
        
        trend_frame = ctk.CTkFrame(charts_frame, fg_color=COLORS["bg_dark"], corner_radius=16)
        trend_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(trend_frame, text="📊 近7天消费趋势", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text_light"]).pack(pady=15)
        
        self.trend_fig = Figure(figsize=(6, 4), facecolor=COLORS["bg_dark"])
        self.trend_ax = self.trend_fig.add_subplot(111)
        self.trend_ax.set_facecolor(COLORS["bg_dark"])
        self.trend_canvas = FigureCanvasTkAgg(self.trend_fig, trend_frame)
        self.trend_canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=10)
        
        pie_frame = ctk.CTkFrame(charts_frame, fg_color=COLORS["bg_dark"], corner_radius=16)
        pie_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(pie_frame, text="🥧 客户活跃度分布", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text_light"]).pack(pady=15)
        
        self.pie_fig = Figure(figsize=(6, 4), facecolor=COLORS["bg_dark"])
        self.pie_ax = self.pie_fig.add_subplot(111)
        self.pie_ax.set_facecolor(COLORS["bg_dark"])
        self.pie_canvas = FigureCanvasTkAgg(self.pie_fig, pie_frame)
        self.pie_canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=10)
        
        quick_frame = ctk.CTkFrame(page, fg_color=COLORS["bg_dark"], corner_radius=16, height=100)
        quick_frame.pack(fill="x", pady=20)
        quick_frame.pack_propagate(False)
        
        ctk.CTkLabel(quick_frame, text="⚡ 快捷操作", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text_light"]).pack(side="left", padx=30)
        
        ctk.CTkButton(quick_frame, text="+ 新增VIP客户", width=150, height=45, corner_radius=10, fg_color=COLORS["success"], hover_color="#059669", font=ctk.CTkFont(size=14, weight="bold"), command=lambda: self.show_page("customers")).pack(side="left", padx=10)
        ctk.CTkButton(quick_frame, text="💳 快速充值", width=150, height=45, corner_radius=10, fg_color=COLORS["accent"], hover_color="#D97706", font=ctk.CTkFont(size=14, weight="bold"), command=lambda: self.show_page("recharge")).pack(side="left", padx=10)
        ctk.CTkButton(quick_frame, text="📝 登记消费", width=150, height=45, corner_radius=10, fg_color=COLORS["secondary"], hover_color="#2563EB", font=ctk.CTkFont(size=14, weight="bold"), command=lambda: self.show_page("consume")).pack(side="left", padx=10)
    
    def refresh_dashboard(self):
        stats = self.db.get_dashboard_stats()
        
        self.stat_cards["total_customers"].configure(text=str(stats['total_customers']))
        self.stat_cards["vip_customers"].configure(text=str(stats['vip_customers']))
        self.stat_cards["current_balance"].configure(text=f"¥{stats['current_balance']:,.0f}")
        self.stat_cards["current_times"].configure(text=f"{stats['current_times']}次")
        self.stat_cards["alert_count"].configure(text=str(stats['alert_count']))
        self.stat_cards["new_this_month"].configure(text=str(stats['new_this_month']))
        
        if stats['alert_count'] > 0:
            self.alert_badge.configure(text=str(stats['alert_count']))
            self.alert_badge.place(relx=0.9, rely=0.5, anchor="center")
        else:
            self.alert_badge.place_forget()
        
        self.trend_ax.clear()
        if stats['weekly_trend']:
            days = [row[0][-5:] for row in stats['weekly_trend']]
            amounts = [row[1] for row in stats['weekly_trend']]
            times = [row[2] for row in stats['weekly_trend']]
            
            x = range(len(days))
            self.trend_ax.bar([i-0.2 for i in x], amounts, 0.4, label='金额(元)', color=COLORS["success"])
            self.trend_ax.bar([i+0.2 for i in x], [t*50 for t in times], 0.4, label='次数(x50)', color=COLORS["secondary"])
            self.trend_ax.set_xticks(x)
            self.trend_ax.set_xticklabels(days, color=COLORS["text_muted"])
            self.trend_ax.tick_params(colors=COLORS["text_muted"])
            self.trend_ax.legend(facecolor=COLORS["bg_dark"], labelcolor=COLORS["text_light"])
            self.trend_ax.set_title('近7天消费趋势', color=COLORS["text_light"], fontsize=12)
        else:
            self.trend_ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', color=COLORS["text_muted"], fontsize=14)
        
        self.trend_fig.tight_layout()
        self.trend_canvas.draw()
        
        self.pie_ax.clear()
        if stats['level_distribution']:
            labels = [row[0] for row in stats['level_distribution']]
            sizes = [row[1] for row in stats['level_distribution']]
            colors = [COLORS["success"], COLORS["secondary"], COLORS["accent"], COLORS["danger"]]
            
            self.pie_ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, textprops={'color': COLORS["text_light"]})
            self.pie_ax.set_title('客户活跃度分布', color=COLORS["text_light"], fontsize=12)
        else:
            self.pie_ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', color=COLORS["text_muted"], fontsize=14)
        
        self.pie_fig.tight_layout()
        self.pie_canvas.draw()
    
    # ==================== 客户管理页面（修复版）====================
    def init_customers(self):
        page = self.pages["customers"]
        
        search_frame = ctk.CTkFrame(page, fg_color=COLORS["bg_dark"], corner_radius=12)
        search_frame.pack(fill="x", pady=(0, 20))
        
        self.customer_search = ctk.CTkEntry(search_frame, placeholder_text="🔍 搜索客户姓名、电话或地址...", width=400, height=45, font=ctk.CTkFont(size=14), corner_radius=10)
        self.customer_search.pack(side="left", padx=20, pady=15)
        
        ctk.CTkButton(search_frame, text="搜索", width=80, height=45, corner_radius=10, command=self.refresh_customer_list).pack(side="left", padx=5)
        ctk.CTkButton(search_frame, text="+ 新增客户", width=120, height=45, corner_radius=10, fg_color=COLORS["success"], hover_color="#059669", font=ctk.CTkFont(size=14, weight="bold"), command=self.show_add_customer_dialog).pack(side="right", padx=20)
        
        list_frame = ctk.CTkFrame(page, fg_color=COLORS["bg_dark"], corner_radius=16)
        list_frame.pack(fill="both", expand=True)
        
        headers = ["ID", "姓名", "电话", "地址", "余额", "剩余次数", "状态", "操作"]
        header_frame = ctk.CTkFrame(list_frame, fg_color=COLORS["primary"], height=50, corner_radius=0)
        header_frame.pack(fill="x", padx=2, pady=2)
        header_frame.pack_propagate(False)
        
        for i, h in enumerate(headers):
            ctk.CTkLabel(header_frame, text=h, font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["text_light"]).place(relx=(i+0.5)/len(headers), rely=0.5, anchor="center")
        
        self.customer_scroll = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.customer_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.customer_list_frame = ctk.CTkFrame(self.customer_scroll, fg_color="transparent")
        self.customer_list_frame.pack(fill="x", expand=True)
    
    def refresh_customer_list(self):
        for widget in self.customer_list_frame.winfo_children():
            widget.destroy()
        
        search = self.customer_search.get()
        customers = self.db.get_all_customers(search)
        
        for customer in customers:
            cid, name, phone, address, id_card, reg_date, status, notes, created, updated, balance, times = customer
            
            row = ctk.CTkFrame(self.customer_list_frame, fg_color=COLORS["bg_card"], height=60, corner_radius=8)
            row.pack(fill="x", pady=3)
            row.pack_propagate(False)
            
            if times <= 0:
                status_color = COLORS["danger"]
                status_text = "已用完"
            elif times <= 2:
                status_color = COLORS["warning"]
                status_text = "即将用完"
            else:
                status_color = COLORS["success"]
                status_text = "正常"
            
            data = [str(cid), name, phone, address[:15]+"..." if len(address)>15 else address, f"¥{balance:.0f}", f"{times}次", status_text]
            
            for i, d in enumerate(data):
                ctk.CTkLabel(row, text=d, font=ctk.CTkFont(size=12), text_color=COLORS["text_light"] if i < 6 else status_color).place(relx=(i+0.5)/8, rely=0.5, anchor="center")
            
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.place(relx=7.5/8, rely=0.5, anchor="center")
            
            ctk.CTkButton(btn_frame, text="充值", width=60, height=30, corner_radius=6, fg_color=COLORS["success"], hover_color="#059669", font=ctk.CTkFont(size=11), command=lambda c=cid: self.quick_recharge(c)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="详情", width=60, height=30, corner_radius=6, fg_color=COLORS["secondary"], hover_color="#2563EB", font=ctk.CTkFont(size=11), command=lambda c=cid: self.show_customer_detail(c)).pack(side="left", padx=2)
    
    def show_add_customer_dialog(self):
        """新增客户对话框 - 修复版（确保按钮可见）"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("新增VIP客户")
        dialog.geometry("500x750")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.focus_force()
        dialog.lift()
        
        # 标题
        ctk.CTkLabel(dialog, text="👤 新增VIP客户", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=15)
        
        # 表单区域
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(fill="x", padx=30, pady=10)
        
        # 姓名字段
        ctk.CTkLabel(form_frame, text="姓名 *", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(10,0))
        name_entry = ctk.CTkEntry(form_frame, placeholder_text="请输入客户姓名", height=40)
        name_entry.pack(fill="x", pady=5)
        
        # 电话字段
        ctk.CTkLabel(form_frame, text="电话 *", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(10,0))
        phone_entry = ctk.CTkEntry(form_frame, placeholder_text="请输入手机号码", height=40)
        phone_entry.pack(fill="x", pady=5)
        
        # 地址字段
        ctk.CTkLabel(form_frame, text="地址", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(10,0))
        address_entry = ctk.CTkEntry(form_frame, placeholder_text="请输入服务地址", height=40)
        address_entry.pack(fill="x", pady=5)
        
        # 身份证字段
        ctk.CTkLabel(form_frame, text="身份证号", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(10,0))
        idcard_entry = ctk.CTkEntry(form_frame, placeholder_text="请输入身份证号", height=40)
        idcard_entry.pack(fill="x", pady=5)
        
        # 备注字段
        ctk.CTkLabel(form_frame, text="备注", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(10,0))
        notes_text = ctk.CTkTextbox(form_frame, height=80)
        notes_text.pack(fill="x", pady=5)
        
        # 状态提示
        status_label = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=12))
        status_label.pack(pady=10)
        
        # 保存函数
        def do_save():
            name = name_entry.get().strip()
            phone = phone_entry.get().strip()
            
            print(f"【调试】保存数据：name={name}, phone={phone}")
            
            if not name:
                status_label.configure(text="❌ 姓名不能为空", text_color=COLORS["danger"])
                return
            if not phone:
                status_label.configure(text="❌ 电话不能为空", text_color=COLORS["danger"])
                return
            
            save_btn.configure(state="disabled", text="保存中...")
            
            try:
                success, result = self.db.add_customer(
                    name=name,
                    phone=phone,
                    address=address_entry.get().strip(),
                    id_card=idcard_entry.get().strip(),
                    notes=notes_text.get("1.0", "end").strip()
                )
                
                print(f"【调试】保存结果：success={success}, result={result}")
                
                if success:
                    status_label.configure(text=f"✅ 保存成功！客户ID: {result}", text_color=COLORS["success"])
                    dialog.after(1500, lambda: [dialog.destroy(), self.refresh_customer_list()])
                else:
                    status_label.configure(text=f"❌ 保存失败: {result}", text_color=COLORS["danger"])
                    save_btn.configure(state="normal", text="✅ 确认保存")
                    
            except Exception as e:
                print(f"【调试】保存异常：{e}")
                status_label.configure(text=f"❌ 系统错误: {str(e)}", text_color=COLORS["danger"])
                save_btn.configure(state="normal", text="✅ 确认保存")
        
        # 按钮区域 - 关键！固定在底部
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=20, side="bottom")
        
        save_btn = ctk.CTkButton(
            btn_frame,
            text="✅ 确认保存",
            height=50,
            fg_color=COLORS["success"],
            hover_color="#059669",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=do_save
        )
        save_btn.pack(fill="x", pady=5)
        
        ctk.CTkButton(
            btn_frame,
            text="❌ 取消",
            height=40,
            fg_color="transparent",
            border_color=COLORS["border"],
            border_width=2,
            text_color=COLORS["text_muted"],
            hover_color=COLORS["bg_dark"],
            font=ctk.CTkFont(size=14),
            command=dialog.destroy
        ).pack(fill="x", pady=5)
        
        # 绑定回车
        dialog.bind("<Return>", lambda e: do_save())
        
        print(f"【调试】对话框创建完成，尺寸：500x750")
    
    def show_customer_detail(self, customer_id):
        customer = self.db.get_customer(customer_id)
        if not customer:
            return
        
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"客户详情 - {customer['name']}")
        dialog.geometry("700x800")
        dialog.transient(self)
        
        info_card = ctk.CTkFrame(dialog, fg_color=COLORS["bg_dark"], corner_radius=16)
        info_card.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(info_card, text=f"👤 {customer['name']}", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(info_card, text=f"📞 {customer['phone']} | 📍 {customer['address']}", font=ctk.CTkFont(size=14), text_color=COLORS["text_muted"]).pack(pady=5)
        
        balance_frame = ctk.CTkFrame(info_card, fg_color=COLORS["bg_card"], corner_radius=12)
        balance_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(balance_frame, text=f"当前余额: ¥{customer['remaining_amount']:.2f}", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["success"] if customer['remaining_amount'] > 0 else COLORS["danger"]).pack(side="left", padx=30, pady=20)
        ctk.CTkLabel(balance_frame, text=f"剩余次数: {customer['remaining_times']}次", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["success"] if customer['remaining_times'] > 0 else COLORS["danger"]).pack(side="right", padx=30, pady=20)
        
        ctk.CTkLabel(dialog, text="💳 充值记录", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        
        recharge_frame = ctk.CTkScrollableFrame(dialog, height=200)
        recharge_frame.pack(fill="x", padx=20, pady=5)
        
        history = self.db.get_recharge_history(customer_id)
        for record in history:
            row = ctk.CTkFrame(recharge_frame, fg_color=COLORS["bg_card"])
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"充值 ¥{record[2]} ({record[3]}次) | 赠送 ¥{record[4]} ({record[5]}次)", font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=record[8], font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(side="right", padx=10)
        
        ctk.CTkLabel(dialog, text="📝 消费记录", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        
        consume_frame = ctk.CTkScrollableFrame(dialog, height=200)
        consume_frame.pack(fill="x", padx=20, pady=5)
        
        for consume in customer['recent_consumptions']:
            row = ctk.CTkFrame(consume_frame, fg_color=COLORS["bg_card"])
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{consume[3]} | 消费 ¥{consume[4]:.2f} ({consume[5]}次)", font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=f"剩余 ¥{consume[6]:.2f} ({consume[7]}次)", font=ctk.CTkFont(size=12), text_color=COLORS["success"]).pack(side="right", padx=10)
            ctk.CTkLabel(row, text=consume[8], font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(side="right", padx=10)
    
    def quick_recharge(self, customer_id):
        self.show_page("recharge")
        self.recharge_customer_id.delete(0, "end")
        self.recharge_customer_id.insert(0, str(customer_id))
        self.load_customer_for_recharge()
    
    # ==================== 充值页面 ====================
    def init_recharge(self):
        page = self.pages["recharge"]

        # 创建滚动框架
        scroll_frame = ctk.CTkScrollableFrame(page, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        select_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_dark"], corner_radius=16)
        select_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(select_frame, text="👤 选择客户", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text_light"]).pack(anchor="w", padx=20, pady=(20, 10))

        input_frame = ctk.CTkFrame(select_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=10)

        self.recharge_customer_id = ctk.CTkEntry(input_frame, placeholder_text="输入客户ID或电话", width=300, height=45, font=ctk.CTkFont(size=14))
        self.recharge_customer_id.pack(side="left", padx=5)

        ctk.CTkButton(input_frame, text="查询", width=100, height=45, command=lambda: [print("[调试] 充值查询按钮被点击"), self.load_customer_for_recharge()]).pack(side="left", padx=5)

        self.recharge_info_frame = ctk.CTkFrame(select_frame, fg_color=COLORS["bg_card"], corner_radius=12)
        self.recharge_info_frame.pack(fill="x", padx=20, pady=20)

        self.recharge_info_label = ctk.CTkLabel(self.recharge_info_frame, text="请先查询客户", font=ctk.CTkFont(size=14), text_color=COLORS["text_muted"])
        self.recharge_info_label.pack(pady=30)

        form_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_dark"], corner_radius=16)
        form_frame.pack(fill="x", pady=20)

        ctk.CTkLabel(form_frame, text="💳 充值信息", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text_light"]).pack(anchor="w", padx=20, pady=(20, 10))

        grid_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        grid_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(grid_frame, text="充值金额 (元) *", font=ctk.CTkFont(size=14), text_color=COLORS["text_light"]).grid(row=0, column=0, sticky="w", pady=5)
        self.recharge_amount = ctk.CTkEntry(grid_frame, placeholder_text="例如: 1200", height=40, width=200)
        self.recharge_amount.grid(row=1, column=0, sticky="w", padx=5)

        ctk.CTkLabel(grid_frame, text="充值次数 *", font=ctk.CTkFont(size=14), text_color=COLORS["text_light"]).grid(row=0, column=1, sticky="w", pady=5, padx=20)
        self.recharge_times = ctk.CTkEntry(grid_frame, placeholder_text="例如: 12", height=40, width=200)
        self.recharge_times.grid(row=1, column=1, sticky="w", padx=20)

        ctk.CTkLabel(grid_frame, text="赠送金额 (元)", font=ctk.CTkFont(size=14), text_color=COLORS["text_light"]).grid(row=2, column=0, sticky="w", pady=(15, 5))
        self.gift_amount = ctk.CTkEntry(grid_frame, placeholder_text="例如: 100", height=40, width=200)
        self.gift_amount.grid(row=3, column=0, sticky="w", padx=5)

        ctk.CTkLabel(grid_frame, text="赠送次数", font=ctk.CTkFont(size=14), text_color=COLORS["text_light"]).grid(row=2, column=1, sticky="w", pady=(15, 5), padx=20)
        self.gift_times = ctk.CTkEntry(grid_frame, placeholder_text="例如: 2", height=40, width=200)
        self.gift_times.grid(row=3, column=1, sticky="w", padx=20)

        ctk.CTkLabel(grid_frame, text="有效期 (月)", font=ctk.CTkFont(size=14), text_color=COLORS["text_light"]).grid(row=4, column=0, sticky="w", pady=(15, 5))
        self.valid_months = ctk.CTkComboBox(grid_frame, values=["3", "6", "12", "24"], width=200, height=40)
        self.valid_months.set("12")
        self.valid_months.grid(row=5, column=0, sticky="w", padx=5)

        ctk.CTkLabel(grid_frame, text="支付方式", font=ctk.CTkFont(size=14), text_color=COLORS["text_light"]).grid(row=4, column=1, sticky="w", pady=(15, 5), padx=20)
        self.payment_method = ctk.CTkComboBox(grid_frame, values=["现金", "微信", "支付宝", "银行卡"], width=200, height=40)
        self.payment_method.set("现金")
        self.payment_method.grid(row=5, column=1, sticky="w", padx=20)

        ctk.CTkLabel(form_frame, text="备注", font=ctk.CTkFont(size=14), text_color=COLORS["text_light"]).pack(anchor="w", padx=20, pady=(15, 5))
        self.recharge_notes = ctk.CTkTextbox(form_frame, height=80, corner_radius=8)
        self.recharge_notes.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkButton(form_frame, text="✅ 确认充值", width=200, height=50, corner_radius=12, fg_color=COLORS["success"], hover_color="#059669", font=ctk.CTkFont(size=16, weight="bold"), command=self.do_recharge).pack(pady=30)
    
    def load_customer_for_recharge(self):
        search = self.recharge_customer_id.get().strip()
        print(f"[调试] 搜索内容: '{search}'")
        if not search:
            return

        # 判断是ID还是手机号：ID通常小于10000，手机号是11位
        if search.isdigit() and len(search) <= 5:
            # 认为是ID
            customer_id = int(search)
            print(f"[调试] 尝试作为ID查询: {customer_id}")
            customer = self.db.get_customer(customer_id)
            print(f"[调试] ID查询结果: {customer}")
        else:
            # 认为是手机号
            print(f"[调试] 尝试手机号查询: {search}")
            conn = self.db.get_connection()
            cursor = conn.cursor()
            # 尝试精确匹配
            cursor.execute('SELECT id FROM vip_customers WHERE phone = %s', (search,))
            result = cursor.fetchone()
            print(f"[调试] 精确匹配结果: {result}")
            if not result:
                # 尝试模糊匹配
                cursor.execute('SELECT id FROM vip_customers WHERE phone LIKE %s', (f'%{search}%',))
                result = cursor.fetchone()
                print(f"[调试] 模糊匹配结果: {result}")
            conn.close()
            if result:
                customer = self.db.get_customer(result[0])
                print(f"[调试] 获取客户详情: {customer}")
            else:
                customer = None

        if customer:
            self.current_customer_id = customer['id']
            self.recharge_info_label.configure(
                text=f"客户: {customer['name']} | 电话: {customer['phone']}\n当前余额: ¥{customer['remaining_amount']:.2f} | 剩余次数: {customer['remaining_times']}次",
                text_color=COLORS["text_light"],
                font=ctk.CTkFont(size=14, weight="bold")
            )
        else:
            messagebox.showerror("错误", "未找到客户")
    
    def do_recharge(self):
        if not self.current_customer_id:
            messagebox.showwarning("提示", "请先查询客户")
            return
        
        try:
            amount = float(self.recharge_amount.get())
            times = int(self.recharge_times.get())
        except ValueError:
            messagebox.showerror("错误", "金额和次数必须为数字")
            return
        
        gift_amount = float(self.gift_amount.get() or 0)
        gift_times = int(self.gift_times.get() or 0)
        
        success, result = self.db.recharge(
            customer_id=self.current_customer_id,
            amount=amount,
            times=times,
            gift_amount=gift_amount,
            gift_times=gift_times,
            payment_method=self.payment_method.get(),
            notes=self.recharge_notes.get("1.0", "end").strip(),
            months_valid=int(self.valid_months.get())
        )
        
        if success:
            # 获取客户信息发送短信
            customer = self.db.get_customer(self.current_customer_id)
            if customer:
                total_amount = amount + gift_amount
                total_times = times + gift_times
                new_remain = customer['remaining_times'] + total_times
                sms_success, sms_msg = self.sms.send_recharge_notification(
                    phone=customer['phone'],
                    name=customer['name'],
                    amount=total_amount,
                    times=total_times,
                    remain=new_remain
                )
                if not sms_success:
                    print(f"短信通知失败: {sms_msg}")

            messagebox.showinfo("成功", "充值成功！")
            self.refresh_dashboard()
            self.load_customer_for_recharge()
        else:
            messagebox.showerror("错误", result)
    
    # ==================== 消费页面 ====================
    def init_consume(self):
        page = self.pages["consume"]

        # 创建滚动框架
        scroll_frame = ctk.CTkScrollableFrame(page, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        select_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_dark"], corner_radius=16)
        select_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(select_frame, text="👤 选择客户", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(20, 10))

        input_frame = ctk.CTkFrame(select_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=10)

        self.consume_customer_id = ctk.CTkEntry(input_frame, placeholder_text="输入客户ID或电话", width=300, height=45, font=ctk.CTkFont(size=14))
        self.consume_customer_id.pack(side="left", padx=5)

        ctk.CTkButton(input_frame, text="查询", width=100, height=45, command=lambda: [print("[调试] 消费查询按钮被点击"), self.load_customer_for_consume()]).pack(side="left", padx=5)

        self.consume_info_frame = ctk.CTkFrame(select_frame, fg_color=COLORS["bg_card"], corner_radius=12)
        self.consume_info_frame.pack(fill="x", padx=20, pady=20)

        self.consume_info_label = ctk.CTkLabel(self.consume_info_frame, text="请先查询客户", font=ctk.CTkFont(size=14), text_color=COLORS["text_muted"])
        self.consume_info_label.pack(pady=30)

        form_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_dark"], corner_radius=16)
        form_frame.pack(fill="x", pady=20)
        
        ctk.CTkLabel(form_frame, text="📝 消费登记", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text_light"]).pack(anchor="w", padx=20, pady=(20, 10))

        grid_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        grid_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(grid_frame, text="服务类型 *", font=ctk.CTkFont(size=14), text_color=COLORS["text_light"]).grid(row=0, column=0, sticky="w", pady=5)
        self.service_type = ctk.CTkComboBox(grid_frame, values=["日常保洁", "深度保洁", "开荒保洁", "家电清洗", "保姆服务", "月嫂服务", "其他"], width=250, height=40)
        self.service_type.set("日常保洁")
        self.service_type.grid(row=1, column=0, sticky="w", padx=5)

        ctk.CTkLabel(grid_frame, text="消费次数 *", font=ctk.CTkFont(size=14), text_color=COLORS["text_light"]).grid(row=0, column=1, sticky="w", pady=5, padx=20)
        self.consume_times = ctk.CTkEntry(grid_frame, placeholder_text="例如: 1", height=40, width=200)
        self.consume_times.insert(0, "1")
        self.consume_times.grid(row=1, column=1, sticky="w", padx=20)

        ctk.CTkLabel(grid_frame, text="服务人员", font=ctk.CTkFont(size=14), text_color=COLORS["text_light"]).grid(row=2, column=0, sticky="w", pady=(15, 5))
        self.service_person = ctk.CTkEntry(grid_frame, placeholder_text="请输入服务人员姓名", height=40, width=250)
        self.service_person.grid(row=3, column=0, sticky="w", padx=5)

        ctk.CTkLabel(grid_frame, text="满意度", font=ctk.CTkFont(size=14), text_color=COLORS["text_light"]).grid(row=2, column=1, sticky="w", pady=(15, 5), padx=20)
        self.satisfaction = ctk.CTkComboBox(grid_frame, values=["5-非常满意", "4-满意", "3-一般", "2-不满意", "1-非常不满意"], width=200, height=40)
        self.satisfaction.set("5-非常满意")
        self.satisfaction.grid(row=3, column=1, sticky="w", padx=20)

        ctk.CTkLabel(form_frame, text="服务备注", font=ctk.CTkFont(size=14), text_color=COLORS["text_light"]).pack(anchor="w", padx=20, pady=(15, 5))
        self.consume_notes = ctk.CTkTextbox(form_frame, height=100, corner_radius=8)
        self.consume_notes.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkButton(form_frame, text="✅ 确认消费", width=200, height=50, corner_radius=12, fg_color=COLORS["accent"], hover_color="#D97706", font=ctk.CTkFont(size=16, weight="bold"), command=self.do_consume).pack(pady=30)
    
    def load_customer_for_consume(self):
        search = self.consume_customer_id.get().strip()
        if not search:
            return

        # 判断是ID还是手机号：ID通常小于10000，手机号是11位
        if search.isdigit() and len(search) <= 5:
            # 认为是ID
            customer_id = int(search)
            customer = self.db.get_customer(customer_id)
        else:
            # 认为是手机号
            conn = self.db.get_connection()
            cursor = conn.cursor()
            # 尝试精确匹配
            cursor.execute('SELECT id FROM vip_customers WHERE phone = %s', (search,))
            result = cursor.fetchone()
            print(f"[调试-消费] 精确匹配结果: {result}")
            if not result:
                # 尝试模糊匹配
                cursor.execute('SELECT id FROM vip_customers WHERE phone LIKE %s', (f'%{search}%',))
                result = cursor.fetchone()
                print(f"[调试-消费] 模糊匹配结果: {result}")
            conn.close()
            if result:
                customer = self.db.get_customer(result[0])
                print(f"[调试-消费] 获取客户详情: {customer}")
            else:
                customer = None

        if customer:
            self.current_customer_id = customer['id']

            if customer['remaining_times'] <= 0:
                color = COLORS["danger"]
                status = "⚠️ 余额不足，请充值！"
            elif customer['remaining_times'] <= 2:
                color = COLORS["warning"]
                status = "⚡ 余额即将用完"
            else:
                color = COLORS["success"]
                status = "✅ 账户正常"
            
            self.consume_info_label.configure(
                text=f"客户: {customer['name']} | 电话: {customer['phone']}\n当前余额: ¥{customer['remaining_amount']:.2f} | 剩余次数: {customer['remaining_times']}次\n{status}",
                text_color=color,
                font=ctk.CTkFont(size=14, weight="bold")
            )
        else:
            messagebox.showerror("错误", "未找到客户")
    
    def do_consume(self):
        if not self.current_customer_id:
            messagebox.showwarning("提示", "请先查询客户")
            return
        
        try:
            times = int(self.consume_times.get())
        except ValueError:
            messagebox.showerror("错误", "消费次数必须为数字")
            return
        
        satisfaction = int(self.satisfaction.get().split("-")[0])
        
        success, result = self.db.consume(
            customer_id=self.current_customer_id,
            service_type=self.service_type.get(),
            consume_times=times,
            service_person=self.service_person.get(),
            satisfaction=satisfaction,
            notes=self.consume_notes.get("1.0", "end").strip()
        )
        
        if success:
            # 获取客户信息发送短信
            customer = self.db.get_customer(self.current_customer_id)
            if customer:
                sms_success, sms_msg = self.sms.send_consume_notification(
                    phone=customer['phone'],
                    name=customer['name'],
                    service_type=self.service_type.get(),
                    amount=round(result['consume_amount'], 2),
                    balance=round(result['remaining_amount'], 2)
                )
                if not sms_success:
                    print(f"短信通知失败: {sms_msg}")

            messagebox.showinfo("成功", f"消费成功！\n本次消费: ¥{result['consume_amount']:.2f} ({times}次)\n剩余余额: ¥{result['remaining_amount']:.2f}\n剩余次数: {result['remaining_times']}次")
            self.refresh_dashboard()
            self.load_customer_for_consume()
        else:
            messagebox.showerror("错误", result)
    
    # ==================== 预警页面 ====================
    def init_alerts(self):
        page = self.pages["alerts"]
        
        stats_frame = ctk.CTkFrame(page, fg_color=COLORS["bg_dark"], corner_radius=16)
        stats_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(stats_frame, text="🔔 预警中心", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=20)
        
        self.alert_stats_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
        self.alert_stats_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        list_frame = ctk.CTkFrame(page, fg_color=COLORS["bg_dark"], corner_radius=16)
        list_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(list_frame, text="待处理预警", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=15)
        
        self.alerts_scroll = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.alerts_scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.alerts_list_frame = ctk.CTkFrame(self.alerts_scroll, fg_color="transparent")
        self.alerts_list_frame.pack(fill="x", expand=True)
    
    def refresh_alerts_list(self):
        for widget in self.alert_stats_frame.winfo_children():
            widget.destroy()
        for widget in self.alerts_list_frame.winfo_children():
            widget.destroy()
        
        self.db.check_alerts()
        alerts = self.db.get_alerts(unresolved_only=True)
        
        high_count = sum(1 for a in alerts if a[4] == "高")
        medium_count = sum(1 for a in alerts if a[4] == "中")
        low_count = sum(1 for a in alerts if a[4] == "低")
        
        for label, count, color in [("高危预警", high_count, COLORS["danger"]), ("中危预警", medium_count, COLORS["warning"]), ("低危预警", low_count, COLORS["success"])]:
            card = ctk.CTkFrame(self.alert_stats_frame, fg_color=COLORS["bg_card"], corner_radius=12, width=200)
            card.pack(side="left", padx=10, fill="y")
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=14), text_color=COLORS["text_muted"]).pack(pady=(15, 5))
            ctk.CTkLabel(card, text=str(count), font=ctk.CTkFont(size=28, weight="bold"), text_color=color).pack(pady=(0, 15))
        
        if not alerts:
            ctk.CTkLabel(self.alerts_list_frame, text="✅ 当前没有预警信息", font=ctk.CTkFont(size=16), text_color=COLORS["success"]).pack(pady=50)
        else:
            for alert in alerts:
                alert_id, cid, atype, level, message, resolved, created, resolved_at, name, phone = alert
                
                row = ctk.CTkFrame(self.alerts_list_frame, fg_color=COLORS["bg_card"], corner_radius=10)
                row.pack(fill="x", pady=5)
                
                color = COLORS["danger"] if level == "高" else COLORS["warning"] if level == "中" else COLORS["success"]
                
                left_frame = ctk.CTkFrame(row, fg_color="transparent")
                left_frame.pack(side="left", padx=15, pady=15, fill="y")
                
                ctk.CTkLabel(left_frame, text=f"⚠️ {atype}", font=ctk.CTkFont(size=14, weight="bold"), text_color=color).pack(anchor="w")
                ctk.CTkLabel(left_frame, text=f"客户: {name} ({phone})", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(anchor="w", pady=(5, 0))
                ctk.CTkLabel(left_frame, text=message, font=ctk.CTkFont(size=12), wraplength=600).pack(anchor="w", pady=(5, 0))
                
                right_frame = ctk.CTkFrame(row, fg_color="transparent")
                right_frame.pack(side="right", padx=15, pady=15)
                
                ctk.CTkButton(right_frame, text="处理", width=80, height=35, corner_radius=8, fg_color=COLORS["success"], command=lambda c=cid: self.handle_alert(c)).pack(side="left", padx=5)
                ctk.CTkButton(right_frame, text="忽略", width=80, height=35, corner_radius=8, fg_color=COLORS["text_muted"], command=lambda a=alert_id: self.ignore_alert(a)).pack(side="left", padx=5)
    
    def handle_alert(self, customer_id):
        self.show_page("recharge")
        self.recharge_customer_id.delete(0, "end")
        self.recharge_customer_id.insert(0, str(customer_id))
        self.load_customer_for_recharge()
    
    def ignore_alert(self, alert_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE alerts SET is_resolved = 1, resolved_at = NOW() WHERE id = %s', (alert_id,))
        conn.commit()
        conn.close()
        self.refresh_alerts_list()
    
    def refresh_alerts(self):
        # 检查预警并获取需要发送短信的客户列表
        alert_customers = self.db.check_alerts()

        # 给余额不足的客户和郭总发送预警短信
        for customer in alert_customers:
            # 给客户发送预警
            self.sms.send_low_balance_alert(
                phone=customer['phone'],
                name=customer['name'],
                balance=round(customer['balance'], 2)
            )
            # 给郭总同步发送预警
            self.sms.send_low_balance_alert(
                phone=SMS_CONFIG['admin_phone'],
                name=customer['name'],
                balance=round(customer['balance'], 2)
            )
            print(f"已发送余额预警短信给客户 {customer['name']} 和郭总")

        self.after(300000, self.refresh_alerts)
    
    # ==================== 统计报表页面 ====================
    def init_stats(self):
        page = self.pages["stats"]
        
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text="📈 统计报表中心", font=ctk.CTkFont(size=24, weight="bold"), text_color=COLORS["text_light"]).pack(side="left")
        
        export_frame = ctk.CTkFrame(header, fg_color="transparent")
        export_frame.pack(side="right")
        
        ctk.CTkButton(export_frame, text="📊 导出Excel", width=130, height=40, corner_radius=10, fg_color=COLORS["success"], hover_color="#059669", command=lambda: self.export_report("excel")).pack(side="left", padx=5)
        ctk.CTkButton(export_frame, text="📄 导出CSV", width=130, height=40, corner_radius=10, fg_color=COLORS["secondary"], hover_color="#2563EB", command=lambda: self.export_report("csv")).pack(side="left", padx=5)
        ctk.CTkButton(export_frame, text="🖨️ 打印报表", width=130, height=40, corner_radius=10, fg_color=COLORS["accent"], hover_color="#D97706", command=self.print_report).pack(side="left", padx=5)
        
        self.stats_tabview = ctk.CTkTabview(page, corner_radius=16, fg_color=COLORS["bg_dark"], segmented_button_fg_color=COLORS["bg_card"], segmented_button_selected_color=COLORS["primary"], segmented_button_selected_hover_color=COLORS["secondary"], segmented_button_unselected_color=COLORS["bg_card"], segmented_button_unselected_hover_color=COLORS["border"])
        self.stats_tabview.pack(fill="both", expand=True)
        
        self.stats_tabview.add("营收统计")
        self.stats_tabview.add("客户分析")
        self.stats_tabview.add("服务统计")
        self.stats_tabview.add("趋势预测")
        
        self.init_revenue_stats(self.stats_tabview.tab("营收统计"))
        self.init_customer_stats(self.stats_tabview.tab("客户分析"))
        self.init_service_stats(self.stats_tabview.tab("服务统计"))
        self.init_trend_stats(self.stats_tabview.tab("趋势预测"))
        
        self.stats_tabview.configure(command=self.on_stats_tab_change)
    
    def on_stats_tab_change(self):
        current = self.stats_tabview.get()
        if current == "营收统计":
            self.refresh_revenue_stats()
        elif current == "客户分析":
            self.refresh_customer_stats()
        elif current == "服务统计":
            self.refresh_service_stats()
        elif current == "趋势预测":
            self.refresh_trend_stats()
    
    def init_revenue_stats(self, parent):
        filter_frame = ctk.CTkFrame(parent, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(filter_frame, text="时间范围:", font=ctk.CTkFont(size=14)).pack(side="left", padx=5)
        
        self.revenue_period = ctk.CTkComboBox(filter_frame, values=["本月", "上月", "本季度", "本年度", "自定义"], width=120, height=35, command=self.refresh_revenue_stats)
        self.revenue_period.set("本月")
        self.revenue_period.pack(side="left", padx=5)
        
        ctk.CTkButton(filter_frame, text="🔄 刷新", width=80, height=35, command=self.refresh_revenue_stats).pack(side="left", padx=20)
        
        cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20, pady=10)
        
        self.revenue_cards = {}
        card_configs = [("recharge_total", "充值总额", "💰", COLORS["success"]), ("consume_total", "消费总额", "💸", COLORS["accent"]), ("profit", "净收入", "📈", COLORS["secondary"]), ("avg_order", "客单价", "🎯", COLORS["warning"])]
        
        for i, (key, title, icon, color) in enumerate(card_configs):
            card = ctk.CTkFrame(cards_frame, fg_color=COLORS["bg_card"], corner_radius=12, height=100)
            card.grid(row=0, column=i, padx=10, pady=5, sticky="nsew")
            card.grid_propagate(False)
            card.grid_columnconfigure(0, weight=1)
            
            ctk.CTkLabel(card, text=f"{icon} {title}", font=ctk.CTkFont(size=13), text_color=COLORS["text_muted"]).pack(pady=(15, 5))
            self.revenue_cards[key] = ctk.CTkLabel(card, text="¥0", font=ctk.CTkFont(size=22, weight="bold"), text_color=color)
            self.revenue_cards[key].pack(pady=(0, 15))
        
        cards_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        charts_frame = ctk.CTkFrame(parent, fg_color="transparent")
        charts_frame.pack(fill="both", expand=True, padx=20, pady=10)
        charts_frame.grid_columnconfigure((0, 1), weight=1)
        charts_frame.grid_rowconfigure(0, weight=1)
        
        trend_frame = ctk.CTkFrame(charts_frame, fg_color=COLORS["bg_card"], corner_radius=12)
        trend_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(trend_frame, text="📊 营收趋势对比", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=15)
        
        self.revenue_trend_fig = Figure(figsize=(6, 4.5), facecolor=COLORS["bg_card"])
        self.revenue_trend_ax = self.revenue_trend_fig.add_subplot(111)
        self.revenue_trend_ax.set_facecolor(COLORS["bg_card"])
        self.revenue_trend_canvas = FigureCanvasTkAgg(self.revenue_trend_fig, trend_frame)
        self.revenue_trend_canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=10)
        
        pie_frame = ctk.CTkFrame(charts_frame, fg_color=COLORS["bg_card"], corner_radius=12)
        pie_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(pie_frame, text="💳 支付方式分布", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=15)
        
        self.payment_pie_fig = Figure(figsize=(6, 4.5), facecolor=COLORS["bg_card"])
        self.payment_pie_ax = self.payment_pie_fig.add_subplot(111)
        self.payment_pie_ax.set_facecolor(COLORS["bg_card"])
        self.payment_pie_canvas = FigureCanvasTkAgg(self.payment_pie_fig, pie_frame)
        self.payment_pie_canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=10)
        
        detail_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12, height=200)
        detail_frame.pack(fill="x", padx=20, pady=10)
        detail_frame.pack_propagate(False)
        
        ctk.CTkLabel(detail_frame, text="📝 每日明细", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=15, pady=10)
        
        header_frame = ctk.CTkFrame(detail_frame, fg_color=COLORS["primary"], height=35)
        header_frame.pack(fill="x", padx=15, pady=(0, 5))
        header_frame.pack_propagate(False)
        
        headers = ["日期", "充值金额", "充值次数", "消费金额", "消费次数", "净收入"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(header_frame, text=h, font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text_light"]).place(relx=(i+0.5)/len(headers), rely=0.5, anchor="center")
        
        self.revenue_scroll = ctk.CTkScrollableFrame(detail_frame, height=120)
        self.revenue_scroll.pack(fill="x", padx=15, pady=5)
        
        self.revenue_table_frame = ctk.CTkFrame(self.revenue_scroll, fg_color="transparent")
        self.revenue_table_frame.pack(fill="x")
    
    def refresh_revenue_stats(self, *args):
        period = self.revenue_period.get()
        stats = self.db.get_revenue_statistics(period)
        
        self.revenue_cards["recharge_total"].configure(text=f"¥{stats['total_recharge']:,.2f}")
        self.revenue_cards["consume_total"].configure(text=f"¥{stats['total_consume']:,.2f}")
        self.revenue_cards["profit"].configure(text=f"¥{stats['profit']:,.2f}")
        self.revenue_cards["avg_order"].configure(text=f"¥{stats['avg_order']:,.2f}")
        
        self.revenue_trend_ax.clear()
        if stats['daily_data']:
            days = [d[0][-5:] for d in stats['daily_data']]
            recharges = [d[1] for d in stats['daily_data']]
            consumes = [d[3] for d in stats['daily_data']]
            
            x = range(len(days))
            width = 0.35
            
            self.revenue_trend_ax.bar([i-width/2 for i in x], recharges, width, label='充值', color=COLORS["success"], alpha=0.8)
            self.revenue_trend_ax.bar([i+width/2 for i in x], consumes, width, label='消费', color=COLORS["accent"], alpha=0.8)
            
            self.revenue_trend_ax.set_xticks(x)
            self.revenue_trend_ax.set_xticklabels(days, rotation=45, ha='right', color=COLORS["text_muted"])
            self.revenue_trend_ax.tick_params(colors=COLORS["text_muted"])
            self.revenue_trend_ax.legend(facecolor=COLORS["bg_card"], labelcolor=COLORS["text_light"])
            self.revenue_trend_ax.set_title(f'{period}营收趋势', color=COLORS["text_light"], fontsize=12)
        else:
            self.revenue_trend_ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', color=COLORS["text_muted"], fontsize=14)
        
        self.revenue_trend_fig.tight_layout()
        self.revenue_trend_canvas.draw()
        
        self.payment_pie_ax.clear()
        if stats['payment_methods']:
            methods = [m[0] for m in stats['payment_methods']]
            amounts = [m[1] for m in stats['payment_methods']]
            colors = [COLORS["success"], COLORS["secondary"], COLORS["accent"], COLORS["warning"]]
            
            self.payment_pie_ax.pie(amounts, labels=methods, autopct='%1.1f%%', startangle=90, colors=colors[:len(methods)], textprops={'color': COLORS["text_light"]})
            self.payment_pie_ax.set_title('支付方式占比', color=COLORS["text_light"], fontsize=12)
        else:
            self.payment_pie_ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', color=COLORS["text_muted"], fontsize=14)
        
        self.payment_pie_fig.tight_layout()
        self.payment_pie_canvas.draw()
        
        for widget in self.revenue_table_frame.winfo_children():
            widget.destroy()
        
        for row_data in stats['daily_data']:
            row = ctk.CTkFrame(self.revenue_table_frame, fg_color=COLORS["bg_dark"], height=30)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)
            
            date, recharge, r_times, consume, c_times, profit = row_data
            values = [date, f"¥{recharge:.2f}", f"{r_times}次", f"¥{consume:.2f}", f"{c_times}次", f"¥{profit:.2f}"]
            colors = [COLORS["text_light"], COLORS["success"], COLORS["text_muted"], COLORS["accent"], COLORS["text_muted"], COLORS["secondary"]]
            
            for i, (v, c) in enumerate(zip(values, colors)):
                ctk.CTkLabel(row, text=v, font=ctk.CTkFont(size=11), text_color=c).place(relx=(i+0.5)/len(values), rely=0.5, anchor="center")
    
    def init_customer_stats(self, parent):
        filter_frame = ctk.CTkFrame(parent, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(filter_frame, text="分析维度:", font=ctk.CTkFont(size=14)).pack(side="left", padx=5)
        
        self.customer_stats_type = ctk.CTkComboBox(filter_frame, values=["价值分层", "增长趋势", "流失分析"], width=150, height=35, command=self.refresh_customer_stats)
        self.customer_stats_type.set("价值分层")
        self.customer_stats_type.pack(side="left", padx=5)
        
        ctk.CTkButton(filter_frame, text="🔄 刷新", width=80, height=35, command=self.refresh_customer_stats).pack(side="left", padx=20)
        
        content_frame = ctk.CTkFrame(parent, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        content_frame.grid_columnconfigure((0, 1), weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        chart_frame = ctk.CTkFrame(content_frame, fg_color=COLORS["bg_card"], corner_radius=12)
        chart_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(chart_frame, text="📊 客户分析图表", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=15)
        
        self.customer_chart_fig = Figure(figsize=(6, 5), facecolor=COLORS["bg_card"])
        self.customer_chart_ax = self.customer_chart_fig.add_subplot(111)
        self.customer_chart_ax.set_facecolor(COLORS["bg_card"])
        self.customer_chart_canvas = FigureCanvasTkAgg(self.customer_chart_fig, chart_frame)
        self.customer_chart_canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=10)
        
        list_frame = ctk.CTkFrame(content_frame, fg_color=COLORS["bg_card"], corner_radius=12)
        list_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(list_frame, text="📝 详细数据", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=15)
        
        self.customer_stats_scroll = ctk.CTkScrollableFrame(list_frame)
        self.customer_stats_scroll.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.customer_stats_list = ctk.CTkFrame(self.customer_stats_scroll, fg_color="transparent")
        self.customer_stats_list.pack(fill="x")
    
    def refresh_customer_stats(self, *args):
        analysis_type = self.customer_stats_type.get()
        
        if analysis_type == "价值分层":
            data = self.db.get_customer_value_distribution()
            
            self.customer_chart_ax.clear()
            if data:
                levels = [d[0] for d in data]
                counts = [d[1] for d in data]
                values = [d[2] for d in data]
                
                y_pos = range(len(levels))
                bars = self.customer_chart_ax.barh(y_pos, counts, color=[COLORS["success"], COLORS["secondary"], COLORS["accent"], COLORS["warning"], COLORS["danger"]])
                
                self.customer_chart_ax.set_yticks(y_pos)
                self.customer_chart_ax.set_yticklabels(levels, color=COLORS["text_light"])
                self.customer_chart_ax.tick_params(colors=COLORS["text_muted"])
                self.customer_chart_ax.set_xlabel('客户数量', color=COLORS["text_muted"])
                self.customer_chart_ax.set_title('客户价值分层', color=COLORS["text_light"], fontsize=12)
                
                for i, (bar, val) in enumerate(zip(bars, values)):
                    width = bar.get_width()
                    self.customer_chart_ax.text(width, bar.get_y() + bar.get_height()/2, f'{int(width)}人 (¥{val:.0f})', ha='left', va='center', color=COLORS["text_muted"], fontsize=10)
            else:
                self.customer_chart_ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', color=COLORS["text_muted"], fontsize=14)
            
            self.customer_chart_fig.tight_layout()
            self.customer_chart_canvas.draw()
            
            for widget in self.customer_stats_list.winfo_children():
                widget.destroy()
            
            headers = ["层级", "客户数", "总余额", "占比", "平均余额"]
            header = ctk.CTkFrame(self.customer_stats_list, fg_color=COLORS["primary"], height=30)
            header.pack(fill="x", pady=2)
            header.pack_propagate(False)
            
            for i, h in enumerate(headers):
                ctk.CTkLabel(header, text=h, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["text_light"]).place(relx=(i+0.5)/len(headers), rely=0.5, anchor="center")
            
            total_count = sum(d[1] for d in data) if data else 1
            
            for row_data in data:
                level, count, total_value = row_data
                avg = total_value / count if count > 0 else 0
                ratio = count / total_count * 100
                
                row = ctk.CTkFrame(self.customer_stats_list, fg_color=COLORS["bg_dark"], height=28)
                row.pack(fill="x", pady=2)
                row.pack_propagate(False)
                
                values = [level, str(count), f"¥{total_value:.0f}", f"{ratio:.1f}%", f"¥{avg:.0f}"]
                for i, v in enumerate(values):
                    ctk.CTkLabel(row, text=v, font=ctk.CTkFont(size=11), text_color=COLORS["text_light"]).place(relx=(i+0.5)/len(values), rely=0.5, anchor="center")
        
        elif analysis_type == "增长趋势":
            data = self.db.get_monthly_growth()
            
            self.customer_chart_ax.clear()
            if data:
                months = [d[0] for d in data]
                new_customers = [d[1] for d in data]
                churn_customers = [d[2] for d in data]
                
                x = range(len(months))
                self.customer_chart_ax.plot(x, new_customers, marker='o', label='新增客户', color=COLORS["success"], linewidth=2)
                self.customer_chart_ax.plot(x, churn_customers, marker='s', label='流失客户', color=COLORS["danger"], linewidth=2)
                
                self.customer_chart_ax.set_xticks(x)
                self.customer_chart_ax.set_xticklabels(months, rotation=45, ha='right', color=COLORS["text_muted"])
                self.customer_chart_ax.tick_params(colors=COLORS["text_muted"])
                self.customer_chart_ax.legend(facecolor=COLORS["bg_card"], labelcolor=COLORS["text_light"])
                self.customer_chart_ax.set_title('客户增长趋势', color=COLORS["text_light"], fontsize=12)
                self.customer_chart_ax.grid(True, alpha=0.3, color=COLORS["border"])
            else:
                self.customer_chart_ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', color=COLORS["text_muted"], fontsize=14)
            
            self.customer_chart_fig.tight_layout()
            self.customer_chart_canvas.draw()
    
    def init_service_stats(self, parent):
        content_frame = ctk.CTkFrame(parent, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=15)
        content_frame.grid_columnconfigure((0, 1), weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        type_frame = ctk.CTkFrame(content_frame, fg_color=COLORS["bg_card"], corner_radius=12)
        type_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(type_frame, text="🔧 服务类型分布", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=15)
        
        self.service_type_fig = Figure(figsize=(6, 5), facecolor=COLORS["bg_card"])
        self.service_type_ax = self.service_type_fig.add_subplot(111)
        self.service_type_ax.set_facecolor(COLORS["bg_card"])
        self.service_type_canvas = FigureCanvasTkAgg(self.service_type_fig, type_frame)
        self.service_type_canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=10)
        
        sat_frame = ctk.CTkFrame(content_frame, fg_color=COLORS["bg_card"], corner_radius=12)
        sat_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(sat_frame, text="⭐ 满意度分析", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=15)
        
        self.sat_fig = Figure(figsize=(6, 5), facecolor=COLORS["bg_card"])
        self.sat_ax = self.sat_fig.add_subplot(111)
        self.sat_ax.set_facecolor(COLORS["bg_card"])
        self.sat_canvas = FigureCanvasTkAgg(self.sat_fig, sat_frame)
        self.sat_canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=10)
    
    def refresh_service_stats(self):
        type_data = self.db.get_service_type_stats()
        
        self.service_type_ax.clear()
        if type_data:
            types = [t[0] for t in type_data]
            counts = [t[1] for t in type_data]
            amounts = [t[2] for t in type_data]
            
            ax2 = self.service_type_ax.twinx()
            
            bars = self.service_type_ax.bar(types, counts, alpha=0.7, color=COLORS["secondary"], label='次数')
            line = ax2.plot(types, amounts, color=COLORS["accent"], marker='o', linewidth=2, label='金额')
            
            self.service_type_ax.set_ylabel('服务次数', color=COLORS["text_muted"])
            ax2.set_ylabel('服务金额(元)', color=COLORS["text_muted"])
            self.service_type_ax.tick_params(colors=COLORS["text_muted"], rotation=45)
            ax2.tick_params(colors=COLORS["text_muted"])
            self.service_type_ax.set_title('各类型服务统计', color=COLORS["text_light"], fontsize=12)
            
            lines1, labels1 = self.service_type_ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            self.service_type_ax.legend(lines1 + lines2, labels1 + labels2, facecolor=COLORS["bg_card"], labelcolor=COLORS["text_light"])
        else:
            self.service_type_ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', color=COLORS["text_muted"], fontsize=14)
        
        self.service_type_fig.tight_layout()
        self.service_type_canvas.draw()
        
        sat_data = self.db.get_satisfaction_stats()
        
        self.sat_ax.clear()
        if sat_data:
            ratings = [s[0] for s in sat_data]
            counts = [s[1] for s in sat_data]
            colors = [COLORS["danger"], COLORS["warning"], COLORS["accent"], COLORS["secondary"], COLORS["success"]]
            
            bars = self.sat_ax.barh([f"{r}星" for r in ratings], counts, color=colors)
            self.sat_ax.set_xlabel('评价数量', color=COLORS["text_muted"])
            self.sat_ax.tick_params(colors=COLORS["text_muted"])
            self.sat_ax.set_title('客户满意度分布', color=COLORS["text_light"], fontsize=12)
            
            total = sum(counts)
            avg = sum(r*c for r, c in zip(ratings, counts)) / total if total > 0 else 0
            
            self.sat_ax.text(0.95, 0.95, f'平均分: {avg:.1f}', transform=self.sat_ax.transAxes, ha='right', va='top', fontsize=12, color=COLORS["text_light"], bbox=dict(boxstyle='round', facecolor=COLORS["bg_dark"], alpha=0.8))
        else:
            self.sat_ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', color=COLORS["text_muted"], fontsize=14)
        
        self.sat_fig.tight_layout()
        self.sat_canvas.draw()
    
    def init_trend_stats(self, parent):
        content_frame = ctk.CTkFrame(parent, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=15)
        
        ctk.CTkLabel(content_frame, text="📈 基于历史数据的趋势预测", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        chart_frame = ctk.CTkFrame(content_frame, fg_color=COLORS["bg_card"], corner_radius=12)
        chart_frame.pack(fill="both", expand=True, pady=10)
        
        self.trend_pred_fig = Figure(figsize=(10, 6), facecolor=COLORS["bg_card"])
        self.trend_pred_ax = self.trend_pred_fig.add_subplot(111)
        self.trend_pred_ax.set_facecolor(COLORS["bg_card"])
        self.trend_pred_canvas = FigureCanvasTkAgg(self.trend_pred_fig, chart_frame)
        self.trend_pred_canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)
        
        info_frame = ctk.CTkFrame(content_frame, fg_color=COLORS["bg_card"], corner_radius=12, height=100)
        info_frame.pack(fill="x", pady=10)
        info_frame.pack_propagate(False)
        
        ctk.CTkLabel(info_frame, text="💡 预测说明：基于近3个月数据，使用线性回归预测未来30天趋势。实际数据可能因季节性、促销活动等因素有所偏差。", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"], wraplength=800).pack(pady=20)
    
    def refresh_trend_stats(self):
        history = self.db.get_daily_revenue_history(days=90)
        
        self.trend_pred_ax.clear()
        
        if len(history) >= 7:
            days = list(range(len(history)))
            revenues = [h[1] for h in history]
            
            z = np.polyfit(days, revenues, 1)
            p = np.poly1d(z)
            
            future_days = list(range(len(history), len(history) + 30))
            all_days = days + future_days
            predicted = [p(d) for d in all_days]
            
            self.trend_pred_ax.plot(days, revenues, 'o-', label='历史数据', color=COLORS["secondary"], markersize=3)
            self.trend_pred_ax.plot(all_days, predicted, '--', label='趋势预测', color=COLORS["accent"], alpha=0.7)
            self.trend_pred_ax.axvline(x=len(history)-1, color=COLORS["warning"], linestyle=':', alpha=0.5, label='今天')
            
            self.trend_pred_ax.fill_between(future_days, [p(d) for d in future_days], alpha=0.2, color=COLORS["accent"])
            
            self.trend_pred_ax.set_xlabel('天数', color=COLORS["text_muted"])
            self.trend_pred_ax.set_ylabel('营收(元)', color=COLORS["text_muted"])
            self.trend_pred_ax.tick_params(colors=COLORS["text_muted"])
            self.trend_pred_ax.legend(facecolor=COLORS["bg_card"], labelcolor=COLORS["text_light"])
            self.trend_pred_ax.set_title('营收趋势预测（未来30天）', color=COLORS["text_light"], fontsize=12)
            self.trend_pred_ax.grid(True, alpha=0.3, color=COLORS["border"])
        else:
            self.trend_pred_ax.text(0.5, 0.5, '数据不足，需要至少7天数据进行预测', ha='center', va='center', color=COLORS["text_muted"], fontsize=14)
        
        self.trend_pred_fig.tight_layout()
        self.trend_pred_canvas.draw()
    
    def export_report(self, format_type):
        current_tab = self.stats_tabview.get()
        
        if format_type == "excel":
            try:
                import openpyxl
                file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel文件", "*.xlsx")], initialfile=f"{current_tab}报表_{datetime.now().strftime('%Y%m%d')}")
                if file_path:
                    wb = openpyxl.Workbook()
                    ws = wb.active
                    ws.title = current_tab
                    
                    if current_tab == "营收统计":
                        data = self.db.get_revenue_statistics(self.revenue_period.get())
                        ws.append(["日期", "充值金额", "充值次数", "消费金额", "消费次数", "净收入"])
                        for row in data['daily_data']:
                            ws.append(row)
                        ws.append([])
                        ws.append(["统计项", "数值"])
                        ws.append(["充值总额", data['total_recharge']])
                        ws.append(["消费总额", data['total_consume']])
                        ws.append(["净收入", data['profit']])
                    
                    wb.save(file_path)
                    messagebox.showinfo("成功", f"报表已导出到:\n{file_path}")
            except ImportError:
                messagebox.showerror("错误", "请先安装openpyxl: pip install openpyxl")
        
        elif format_type == "csv":
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV文件", "*.csv")], initialfile=f"{current_tab}报表_{datetime.now().strftime('%Y%m%d')}")
            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    if current_tab == "营收统计":
                        data = self.db.get_revenue_statistics(self.revenue_period.get())
                        writer.writerow(["日期", "充值金额", "充值次数", "消费金额", "消费次数", "净收入"])
                        writer.writerows(data['daily_data'])
                messagebox.showinfo("成功", f"报表已导出到:\n{file_path}")
    
    def print_report(self):
        messagebox.showinfo("提示", "打印功能需要连接打印机。\n建议先导出PDF或Excel后打印。")

    # ==================== 员工管理页面 ====================
    def init_employees(self):
        """初始化员工管理页面"""
        page = self.pages["employees"]

        # 顶部工具栏
        toolbar = ctk.CTkFrame(page, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(toolbar, text="🧑‍💼 员工电子名片管理", font=ctk.CTkFont(size=22, weight="bold"), text_color=COLORS["text_light"]).pack(side="left")

        btn_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_frame.pack(side="right")

        ctk.CTkButton(btn_frame, text="➕ 添加员工", width=120, height=40, corner_radius=10,
                     fg_color=COLORS["success"], hover_color="#059669",
                     command=self.show_add_employee_dialog).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="🔄 刷新", width=100, height=40, corner_radius=10,
                     fg_color=COLORS["secondary"], hover_color="#2563EB",
                     command=self.refresh_employee_list).pack(side="left", padx=5)

        # 搜索栏
        search_frame = ctk.CTkFrame(page, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 15))

        self.employee_search_entry = ctk.CTkEntry(search_frame, placeholder_text="🔍 搜索员工姓名或技能...", width=300, height=40)
        self.employee_search_entry.pack(side="left", padx=5)
        self.employee_search_entry.bind("<Return>", lambda e: self.refresh_employee_list())

        ctk.CTkButton(search_frame, text="搜索", width=80, height=40, command=self.refresh_employee_list).pack(side="left", padx=5)

        # 状态筛选
        self.employee_status_filter = ctk.CTkComboBox(search_frame, values=["全部", "在职", "离职"], width=100, height=40)
        self.employee_status_filter.set("全部")
        self.employee_status_filter.pack(side="left", padx=20)
        self.employee_status_filter.configure(command=lambda x: self.refresh_employee_list())

        # 员工列表区域（带滚动条）
        list_container = ctk.CTkFrame(page, fg_color=COLORS["bg_dark"], corner_radius=12)
        list_container.pack(fill="both", expand=True, pady=10)
        list_container.grid_columnconfigure(0, weight=1)
        list_container.grid_rowconfigure(0, weight=1)

        # 创建滚动条和列表
        self.employee_list_frame = ctk.CTkScrollableFrame(list_container, fg_color="transparent")
        self.employee_list_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # 初始化列标题
        self.init_employee_list_headers()

        # 统计信息
        stats_frame = ctk.CTkFrame(page, fg_color=COLORS["bg_dark"], corner_radius=12, height=80)
        stats_frame.pack(fill="x", pady=(15, 0))
        stats_frame.pack_propagate(False)

        self.employee_stats_labels = {}
        stats_items = [
            ("active_count", "在职员工", COLORS["success"]),
            ("avg_rating", "平均评分", COLORS["accent"]),
            ("total_count", "员工总数", COLORS["secondary"])
        ]

        for i, (key, label, color) in enumerate(stats_items):
            frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
            frame.pack(side="left", padx=30, pady=15)
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack()
            self.employee_stats_labels[key] = ctk.CTkLabel(frame, text="0", font=ctk.CTkFont(size=20, weight="bold"), text_color=color)
            self.employee_stats_labels[key].pack()

    def init_employee_list_headers(self):
        """初始化员工列表表头"""
        headers = ["照片", "姓名", "年龄", "工龄", "技能", "评分", "状态", "操作"]
        widths = [80, 100, 60, 60, 200, 80, 80, 200]

        header_frame = ctk.CTkFrame(self.employee_list_frame, fg_color=COLORS["bg_card"], corner_radius=8, height=40)
        header_frame.pack(fill="x", pady=(0, 10))
        header_frame.pack_propagate(False)

        for i, (header, width) in enumerate(zip(headers, widths)):
            lbl = ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(size=13, weight="bold"),
                             text_color=COLORS["text_light"], width=width)
            lbl.pack(side="left", padx=5)

    def refresh_employee_list(self):
        """刷新员工列表"""
        # 清空现有列表（保留表头）
        for widget in self.employee_list_frame.winfo_children()[1:]:
            widget.destroy()

        # 获取搜索和筛选条件
        search = self.employee_search_entry.get().strip()
        status_filter = self.employee_status_filter.get()

        status = None if status_filter == "全部" else status_filter

        # 获取员工数据
        employees = self.db.get_all_employees(search=search, status=status)

        if not employees:
            empty_label = ctk.CTkLabel(self.employee_list_frame, text="暂无员工数据",
                                      font=ctk.CTkFont(size=14), text_color=COLORS["text_muted"])
            empty_label.pack(pady=50)
            return

        # 显示员工列表
        for emp in employees:
            self.create_employee_row(emp)

        # 更新统计
        self.refresh_employee_stats()

    def create_employee_row(self, emp):
        """创建员工列表行"""
        row_frame = ctk.CTkFrame(self.employee_list_frame, fg_color=COLORS["bg_card"], corner_radius=8, height=70)
        row_frame.pack(fill="x", pady=5)
        row_frame.pack_propagate(False)

        # 照片
        photo_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=80, height=60)
        photo_frame.pack(side="left", padx=5)
        if emp['photo_path'] and os.path.exists(emp['photo_path']):
            try:
                img = Image.open(emp['photo_path'])
                img = img.resize((50, 50))
                photo = ctk.CTkImage(light_image=img, dark_image=img, size=(50, 50))
                photo_label = ctk.CTkLabel(photo_frame, image=photo, text="")
                photo_label.pack()
            except:
                ctk.CTkLabel(photo_frame, text="📷", font=ctk.CTkFont(size=20)).pack()
        else:
            ctk.CTkLabel(photo_frame, text="👤", font=ctk.CTkFont(size=24)).pack()

        # 姓名
        ctk.CTkLabel(row_frame, text=emp['name'], font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=COLORS["text_light"], width=100).pack(side="left", padx=5)

        # 年龄
        age_text = str(emp['age']) if emp['age'] else "-"
        ctk.CTkLabel(row_frame, text=age_text, font=ctk.CTkFont(size=13),
                    text_color=COLORS["text_light"], width=60).pack(side="left", padx=5)

        # 工龄
        work_years_text = f"{emp['work_years']}年" if emp['work_years'] else "-"
        ctk.CTkLabel(row_frame, text=work_years_text, font=ctk.CTkFont(size=13),
                    text_color=COLORS["text_light"], width=60).pack(side="left", padx=5)

        # 技能
        skills_text = emp['skills'] if emp['skills'] else "未设置"
        skills_label = ctk.CTkLabel(row_frame, text=skills_text, font=ctk.CTkFont(size=12),
                                   text_color=COLORS["text_muted"], width=200)
        skills_label.pack(side="left", padx=5)

        # 评分
        rating_text = f"⭐ {emp['rating']}"
        ctk.CTkLabel(row_frame, text=rating_text, font=ctk.CTkFont(size=13),
                    text_color=COLORS["accent"], width=80).pack(side="left", padx=5)

        # 状态
        status_color = COLORS["success"] if emp['status'] == '在职' else COLORS["text_muted"]
        ctk.CTkLabel(row_frame, text=emp['status'], font=ctk.CTkFont(size=13),
                    text_color=status_color, width=80).pack(side="left", padx=5)

        # 操作按钮
        btn_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=200)
        btn_frame.pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="查看", width=60, height=30, corner_radius=6,
                     fg_color=COLORS["secondary"], hover_color="#2563EB",
                     command=lambda e=emp: self.show_employee_detail(e)).pack(side="left", padx=2)

        ctk.CTkButton(btn_frame, text="二维码", width=60, height=30, corner_radius=6,
                     fg_color=COLORS["accent"], hover_color="#D97706",
                     command=lambda e=emp: self.show_employee_qrcode(e)).pack(side="left", padx=2)

        if emp['status'] == '在职':
            ctk.CTkButton(btn_frame, text="离职", width=60, height=30, corner_radius=6,
                         fg_color=COLORS["warning"], hover_color="#D97706",
                         command=lambda e=emp: self.set_employee_inactive(e['id'])).pack(side="left", padx=2)
        
        # 删除按钮（彻底删除）
        ctk.CTkButton(btn_frame, text="删除", width=60, height=30, corner_radius=6,
                     fg_color="#6B7280", hover_color="#4B5563",
                     command=lambda e=emp: self.delete_employee_permanent(e['id'])).pack(side="left", padx=2)

    def refresh_employee_stats(self):
        """刷新员工统计信息"""
        stats = self.db.get_employee_stats()
        self.employee_stats_labels['active_count'].configure(text=str(stats['active_count']))
        self.employee_stats_labels['avg_rating'].configure(text=str(stats['avg_rating']))
        total = stats['active_count'] + stats['inactive_count']
        self.employee_stats_labels['total_count'].configure(text=str(total))

    def show_add_employee_dialog(self):
        """显示添加员工对话框"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("添加新员工")
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="➕ 添加新员工", font=ctk.CTkFont(size=20, weight="bold"),
                    text_color=COLORS["text_light"]).pack(pady=20)

        # 表单
        form_frame = ctk.CTkScrollableFrame(dialog, fg_color="transparent", width=450, height=400)
        form_frame.pack(padx=20, pady=10, fill="both", expand=True)

        # 姓名
        ctk.CTkLabel(form_frame, text="姓名 *", font=ctk.CTkFont(size=13), text_color=COLORS["text_light"]).pack(anchor="w", pady=(10, 5))
        name_entry = ctk.CTkEntry(form_frame, placeholder_text="请输入姓名", height=40)
        name_entry.pack(fill="x", pady=5)

        # 年龄
        ctk.CTkLabel(form_frame, text="年龄", font=ctk.CTkFont(size=13), text_color=COLORS["text_light"]).pack(anchor="w", pady=(10, 5))
        age_entry = ctk.CTkEntry(form_frame, placeholder_text="请输入年龄", height=40)
        age_entry.pack(fill="x", pady=5)

        # 工龄
        ctk.CTkLabel(form_frame, text="工龄（年）", font=ctk.CTkFont(size=13), text_color=COLORS["text_light"]).pack(anchor="w", pady=(10, 5))
        work_years_entry = ctk.CTkEntry(form_frame, placeholder_text="请输入工龄", height=40)
        work_years_entry.pack(fill="x", pady=5)

        # 技能
        ctk.CTkLabel(form_frame, text="技能（用逗号分隔）", font=ctk.CTkFont(size=13), text_color=COLORS["text_light"]).pack(anchor="w", pady=(10, 5))
        skills_entry = ctk.CTkEntry(form_frame, placeholder_text="例如：保洁,开荒,月嫂", height=40)
        skills_entry.pack(fill="x", pady=5)

        # 照片
        ctk.CTkLabel(form_frame, text="照片", font=ctk.CTkFont(size=13), text_color=COLORS["text_light"]).pack(anchor="w", pady=(10, 5))
        photo_path_var = tk.StringVar()
        photo_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        photo_frame.pack(fill="x", pady=5)
        photo_entry = ctk.CTkEntry(photo_frame, placeholder_text="选择照片...", height=40, textvariable=photo_path_var)
        photo_entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(photo_frame, text="浏览", width=80, height=40,
                     command=lambda: self.select_employee_photo(photo_path_var)).pack(side="left", padx=5)

        # 手机号（内部用）
        ctk.CTkLabel(form_frame, text="手机号（内部用）", font=ctk.CTkFont(size=13), text_color=COLORS["text_light"]).pack(anchor="w", pady=(10, 5))
        phone_entry = ctk.CTkEntry(form_frame, placeholder_text="请输入手机号", height=40)
        phone_entry.pack(fill="x", pady=5)

        # 身份证号（内部用）
        ctk.CTkLabel(form_frame, text="身份证号（内部用）", font=ctk.CTkFont(size=13), text_color=COLORS["text_light"]).pack(anchor="w", pady=(10, 5))
        id_card_entry = ctk.CTkEntry(form_frame, placeholder_text="请输入身份证号", height=40)
        id_card_entry.pack(fill="x", pady=5)

        # 按钮
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)

        def save_employee():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("错误", "请输入员工姓名")
                return

            age = int(age_entry.get()) if age_entry.get().strip().isdigit() else None
            work_years = int(work_years_entry.get()) if work_years_entry.get().strip().isdigit() else 0
            skills = skills_entry.get().strip()
            photo_path = photo_path_var.get()
            phone = phone_entry.get().strip()
            id_card = id_card_entry.get().strip()

            success, result = self.db.add_employee(
                name=name, age=age, work_years=work_years, skills=skills,
                photo_path=photo_path, phone=phone, id_card=id_card
            )

            if success:
                messagebox.showinfo("成功", f"员工 {name} 添加成功！")
                dialog.destroy()
                self.refresh_employee_list()
            else:
                messagebox.showerror("错误", f"添加失败：{result}")

        ctk.CTkButton(btn_frame, text="保存", width=120, height=40, corner_radius=10,
                     fg_color=COLORS["success"], hover_color="#059669", command=save_employee).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="取消", width=120, height=40, corner_radius=10,
                     fg_color=COLORS["text_muted"], hover_color="#64748B", command=dialog.destroy).pack(side="left", padx=10)

    def select_employee_photo(self, path_var):
        """选择员工照片"""
        file_path = filedialog.askopenfilename(
            title="选择员工照片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png")]
        )
        if file_path:
            path_var.set(file_path)

    def show_employee_detail(self, emp):
        """显示员工详情"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"员工详情 - {emp['name']}")
        dialog.geometry("400x500")
        dialog.transient(self)

        # 照片
        photo_frame = ctk.CTkFrame(dialog, fg_color=COLORS["bg_card"], corner_radius=12, width=150, height=150)
        photo_frame.pack(pady=20)
        photo_frame.pack_propagate(False)

        if emp['photo_path'] and os.path.exists(emp['photo_path']):
            try:
                img = Image.open(emp['photo_path'])
                img = img.resize((120, 120))
                photo = ctk.CTkImage(light_image=img, dark_image=img, size=(120, 120))
                ctk.CTkLabel(photo_frame, image=photo, text="").pack(pady=15)
            except:
                ctk.CTkLabel(photo_frame, text="👤", font=ctk.CTkFont(size=60)).pack(pady=30)
        else:
            ctk.CTkLabel(photo_frame, text="👤", font=ctk.CTkFont(size=60)).pack(pady=30)

        # 信息
        info_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        info_frame.pack(padx=30, pady=10, fill="x")

        info_items = [
            ("姓名", emp['name']),
            ("年龄", f"{emp['age']}岁" if emp['age'] else "未设置"),
            ("工龄", f"{emp['work_years']}年" if emp['work_years'] else "未设置"),
            ("技能", emp['skills'] if emp['skills'] else "未设置"),
            ("评分", f"⭐ {emp['rating']} ({emp['review_count']}条评价)"),
            ("状态", emp['status'])
        ]

        for label, value in info_items:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", pady=8)
            ctk.CTkLabel(row, text=f"{label}:", font=ctk.CTkFont(size=13), text_color=COLORS["text_muted"], width=80).pack(side="left")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text_light"]).pack(side="left", padx=10)

        ctk.CTkButton(dialog, text="关闭", width=120, height=40, corner_radius=10,
                     command=dialog.destroy).pack(pady=20)

    def show_employee_qrcode(self, emp):
        """显示员工二维码"""
        try:
            import qrcode

            # 生成二维码URL
            # 使用 scjmj.cn 域名生成访问链接
            qr_url = f"http://www.scjmj.cn/employee/{emp['id']}"

            # 生成二维码
            qr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr.add_data(qr_url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            img = img.resize((250, 250))

            # 保存临时文件
            temp_path = f"temp_qr_employee_{emp['id']}.png"
            img.save(temp_path)

            # 显示对话框
            dialog = ctk.CTkToplevel(self)
            dialog.title(f"{emp['name']} - 电子名片二维码")
            dialog.geometry("350x450")
            dialog.transient(self)

            ctk.CTkLabel(dialog, text=f"🧑‍💼 {emp['name']}", font=ctk.CTkFont(size=18, weight="bold"),
                        text_color=COLORS["text_light"]).pack(pady=15)

            # 显示二维码
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(250, 250))
            qr_label = ctk.CTkLabel(dialog, image=ctk_img, text="")
            qr_label.pack(pady=10)

            ctk.CTkLabel(dialog, text="扫码查看员工电子名片", font=ctk.CTkFont(size=12),
                        text_color=COLORS["text_muted"]).pack()

            ctk.CTkLabel(dialog, text=qr_url, font=ctk.CTkFont(size=10),
                        text_color=COLORS["secondary"]).pack(pady=5)

            # 添加复制链接按钮
            def copy_link():
                self.clipboard_clear()
                self.clipboard_append(qr_url)
                self.update()
                messagebox.showinfo("成功", "链接已复制到剪贴板")

            ctk.CTkButton(btn_frame, text="📋 复制链接", width=100, height=35, corner_radius=8,
                         fg_color=COLORS["secondary"], command=copy_link).pack(side="left", padx=5)

            # 按钮
            btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_frame.pack(pady=20)

            def save_qr():
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".png",
                    filetypes=[("PNG图片", "*.png")],
                    initialfile=f"{emp['name']}_二维码.png"
                )
                if save_path:
                    img.save(save_path)
                    messagebox.showinfo("成功", f"二维码已保存到：\n{save_path}")

            ctk.CTkButton(btn_frame, text="💾 保存", width=100, height=35, corner_radius=8,
                         fg_color=COLORS["success"], command=save_qr).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="关闭", width=100, height=35, corner_radius=8,
                         command=dialog.destroy).pack(side="left", padx=5)

        except ImportError:
            messagebox.showerror("错误", "请先安装qrcode库：pip install qrcode[pil]")
        except Exception as e:
            messagebox.showerror("错误", f"生成二维码失败：{str(e)}")

    def set_employee_inactive(self, employee_id):
        """设置员工离职"""
        if messagebox.askyesno("确认", "确定要将该员工设为离职状态吗？"):
            success, msg = self.db.delete_employee(employee_id)
            if success:
                messagebox.showinfo("成功", "员工状态已更新")
                self.refresh_employee_list()
            else:
                messagebox.showerror("错误", f"操作失败：{msg}")

    def delete_employee_permanent(self, employee_id):
        """彻底删除员工（从数据库中删除）"""
        if messagebox.askyesno("⚠️ 警告", "确定要彻底删除该员工吗？\n此操作不可恢复！"):
            try:
                # 先同步删除到虚拟主机
                self.db.sync_employee_to_virtualhost(employee_id, 'delete')
                
                # 从本地数据库删除
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("成功", "员工已彻底删除")
                self.refresh_employee_list()
            except Exception as e:
                messagebox.showerror("错误", f"删除失败：{str(e)}")

# ==================== 启动应用 ====================
if __name__ == "__main__":
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    app = VIPHousekeepingApp()
    app.mainloop()