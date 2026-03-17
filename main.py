"""
🏠 嘉美净家政VIP管理系统 - 移动端
基于Kivy + KivyMD开发
与PC端共用MySQL数据库
"""

from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '800')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem, ThreeLineListItem
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.tab import MDTabs, MDTabsBase
from kivymd.theming import ThemableBehavior
from kivymd.color_definitions import colors

import pymysql
import json
import hashlib
import hmac
import base64
import urllib.parse
import requests
from datetime import datetime, timedelta
from decimal import Decimal

# API同步配置（西部数码虚拟主机）
API_CONFIG = {
    'enabled': True,
    'url': 'https://scjmj.cn/api_sync.php',
    'key': 'jiameijing2024',
}

# ==================== 短信服务配置 ====================
SMS_CONFIG = {
    'enabled': False,  # 短信开关，最终审核通过后改为 True
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

# ==================== 全局配置 ====================
# 颜色配置 - 高端商务深色主题
COLORS = {
    'primary': '#1E3A8A',      # 深蓝
    'secondary': '#3B82F6',    # 亮蓝
    'accent': '#F59E0B',       # 金色强调
    'success': '#10B981',      # 绿色
    'warning': '#F59E0B',      # 橙色
    'danger': '#EF4444',       # 红色
    'bg_dark': '#0F172A',      # 深色背景
    'bg_card': '#1E293B',      # 卡片背景
    'bg_light': '#334155',     # 浅背景
    'text_light': '#F1F5F9',   # 浅色文字
    'text_muted': '#94A3B8',   # 灰色文字
    'border': '#475569',       # 边框色
}

# 数据库配置
DB_CONFIG = {
    'host': '106.14.254.13',
    'port': 3306,
    'user': 'app',
    'password': 'app123456',
    'database': 'housekeeping',
    'charset': 'utf8mb4',
    'autocommit': False
}

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
        sorted_params = sorted(params.items())
        canonical_query_string = urllib.parse.urlencode(sorted_params)
        string_to_sign = f"GET&%2F&{urllib.parse.quote(canonical_query_string, safe='')}".encode('utf-8')
        key = (access_key_secret + "&").encode('utf-8')
        signature = base64.b64encode(hmac.new(key, string_to_sign, hashlib.sha1).digest()).decode('utf-8')
        return signature

    def send_sms(self, phone, template_code, template_param):
        """发送短信"""
        if not self.enabled:
            print(f"[短信模拟] 发送给 {phone}: 模板={template_code}, 参数={template_param}")
            return True, "短信模拟发送成功（短信服务未启用）"

        try:
            import time
            import uuid

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

            params['Signature'] = self._sign(params, self.access_key_secret)

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
        """发送充值通知"""
        template_code = SMS_CONFIG['template_code_recharge']
        param = {
            'name': name,
            'amount': str(amount),
            'times': str(times),
            'remain': str(remain)
        }
        return self.send_sms(phone, template_code, param)

    def send_consume_notification(self, phone, name, service_type, amount, balance):
        """发送消费通知"""
        template_code = SMS_CONFIG['template_code_consume']
        param = {
            'name': name,
            'service': service_type,
            'amount': str(amount),
            'balance': str(balance)
        }
        return self.send_sms(phone, template_code, param)

    def send_low_balance_alert(self, phone, name, balance):
        """发送余额不足提醒"""
        template_code = SMS_CONFIG['template_code_alert']
        param = {
            'name': name,
            'balance': str(balance),
            'phone': SMS_CONFIG['service_phone']
        }
        return self.send_sms(phone, template_code, param)


# ==================== 数据库管理类 ====================
class DatabaseManager:
    """数据库管理类 - 与PC端共用"""
    
    def __init__(self):
        self.db_config = DB_CONFIG
    
    def get_connection(self):
        return pymysql.connect(**self.db_config)
    
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
        
        remaining_amount = float(total_recharge[0] or 0) - float(total_consume[0] or 0)
        remaining_times = (total_recharge[1] or 0) - (total_consume[1] or 0)
        
        return {
            'id': customer[0],
            'name': customer[1],
            'phone': customer[2],
            'address': customer[3] or '',
            'id_card': customer[4] or '',
            'register_date': customer[5],
            'status': customer[6],
            'notes': customer[8] or '',
            'total_recharge_amount': float(total_recharge[0] or 0),
            'total_recharge_times': total_recharge[1] or 0,
            'total_consume_amount': float(total_consume[0] or 0),
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
    
    def add_customer(self, name, phone, address="", id_card="", notes=""):
        """添加新客户"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO vip_customers (name, phone, address, id_card, notes)
                VALUES (%s, %s, %s, %s, %s)
            ''', (name, phone, address, id_card, notes))
            
            conn.commit()
            customer_id = cursor.lastrowid
            return True, customer_id
            
        except pymysql.IntegrityError:
            return False, "电话号码已存在"
        except Exception as e:
            return False, str(e)
        finally:
            if conn:
                conn.close()
    
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

            # 发送充值短信通知
            try:
                customer = self.get_customer(customer_id)
                if customer:
                    sms = SMSService()
                    # 计算充值后剩余
                    remaining_times = customer['remaining_times'] + total_times
                    sms.send_recharge_notification(
                        customer['phone'],
                        customer['name'],
                        amount,
                        times,
                        remaining_times
                    )
            except:
                pass  # 短信发送失败不影响业务

            return True, "充值成功"
        except Exception as e:
            return False, str(e)
    
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

            # 发送消费短信通知
            try:
                sms = SMSService()
                sms.send_consume_notification(
                    customer['phone'],
                    customer['name'],
                    service_type,
                    round(consume_amount, 2),
                    round(new_amount, 2)
                )
            except:
                pass  # 短信发送失败不影响业务

            return True, {
                'consume_amount': consume_amount,
                'remaining_amount': new_amount,
                'remaining_times': new_times
            }

        except Exception as e:
            return False, str(e)
    
    # ==================== 员工管理方法 ====================
    def get_all_employees(self, search="", status=None):
        """获取员工列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT id, name, age, work_years, skills, photo_path, rating, review_count, status FROM employees WHERE 1=1'
        params = []
        
        if search:
            query += ' AND (name LIKE %s OR skills LIKE %s)'
            params.extend([f'%{search}%', f'%{search}%'])
        
        if status:
            query += ' AND status = %s'
            params.append(status)
        
        query += ' ORDER BY status DESC, rating DESC'
        
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
    
    def get_employee(self, employee_id):
        """获取单个员工详情"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM employees WHERE id = %s', (employee_id,))
        emp = cursor.fetchone()
        conn.close()
        
        if not emp:
            return None
        
        return {
            'id': emp[0],
            'name': emp[1],
            'age': emp[2],
            'work_years': emp[3],
            'skills': emp[4],
            'photo_path': emp[5],
            'rating': float(emp[6]) if emp[6] else 5.0,
            'review_count': emp[7],
            'status': emp[8],
            'id_card': emp[9],
            'phone': emp[10]
        }
    
    def get_employee_stats(self):
        """获取员工统计"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM employees WHERE status = "在职"')
        active_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM employees WHERE status = "离职"')
        inactive_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(rating) FROM employees WHERE status = "在职"')
        avg_rating = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'active_count': active_count,
            'inactive_count': inactive_count,
            'avg_rating': round(float(avg_rating), 1)
        }
    
    def sync_employee_to_virtualhost(self, employee_id, action='add'):
        """同步员工数据到西部数码虚拟主机"""
        if not API_CONFIG['enabled']:
            return True, "同步已禁用"
        
        try:
            employee = self.get_employee(employee_id)
            if not employee:
                return False, "员工不存在"
            
            # 虚拟主机限制POST，使用GET方式传递所有数据
            import urllib.parse
            params = {
                'key': API_CONFIG['key'],
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
            
            query_string = urllib.parse.urlencode(params, encoding='utf-8')
            full_url = f"{API_CONFIG['url']}?{query_string}"
            
            print(f"[调试] 同步URL: {full_url[:100]}...")
            
            response = requests.get(
                full_url,
                timeout=10
            )
            
            result = response.json()
            if result.get('success'):
                print(f"[同步成功] 员工 {employee['name']} 已同步")
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
            
            cursor.execute(f'''
                UPDATE employees SET {set_clause} WHERE id = %s
            ''', values)
            
            conn.commit()
            
            # 同步到虚拟主机
            self.sync_employee_to_virtualhost(employee_id, 'update')
            
            return True, "更新成功"
            
        except Exception as e:
            return False, str(e)
        finally:
            if conn:
                conn.close()
    
    def get_dashboard_stats(self):
        """获取仪表盘统计数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM vip_customers')
        total_customers = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT customer_id) FROM recharge_records')
        vip_customers = cursor.fetchone()[0]
        
        cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM recharge_records')
        total_recharge = float(cursor.fetchone()[0] or 0)
        
        cursor.execute('SELECT COALESCE(SUM(times), 0) FROM recharge_records')
        total_times = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COALESCE(SUM(consume_amount), 0) FROM consumption_records')
        total_consume = float(cursor.fetchone()[0] or 0)
        
        cursor.execute('SELECT COALESCE(SUM(consume_times), 0) FROM consumption_records')
        total_consume_times = cursor.fetchone()[0] or 0
        
        current_balance = total_recharge - total_consume
        current_times = total_times - total_consume_times
        
        cursor.execute('''
            SELECT COUNT(*) FROM vip_customers 
            WHERE DATE_FORMAT(created_at, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m')
        ''')
        new_this_month = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM alerts WHERE is_resolved = 0
        ''')
        alert_count = cursor.fetchone()[0]
        
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
            'alert_count': alert_count
        }


# ==================== 全局数据库实例 ====================
db = DatabaseManager()


# ==================== 屏幕基类 ====================
class BaseScreen(MDScreen):
    """屏幕基类"""
    
    def show_snackbar(self, text, duration=2):
        """显示底部提示"""
        Snackbar(text=text, duration=duration).open()
    
    def show_dialog(self, title, text, buttons=None):
        """显示对话框"""
        if not buttons:
            buttons = [MDFlatButton(text="确定", on_release=lambda x: self.dialog.dismiss())]
        self.dialog = MDDialog(title=title, text=text, buttons=buttons)
        self.dialog.open()


# ==================== 仪表盘屏幕 ====================
class DashboardScreen(BaseScreen):
    """仪表盘屏幕"""
    
    def on_enter(self):
        """进入屏幕时刷新数据"""
        self.load_data()
    
    def load_data(self):
        """加载仪表盘数据"""
        try:
            stats = db.get_dashboard_stats()
            
            # 更新统计卡片
            self.ids.total_customers.text = str(stats['total_customers'])
            self.ids.vip_customers.text = str(stats['vip_customers'])
            self.ids.current_balance.text = f"¥{stats['current_balance']:,.0f}"
            self.ids.current_times.text = f"{stats['current_times']}次"
            self.ids.new_this_month.text = str(stats['new_this_month'])
            self.ids.alert_count.text = str(stats['alert_count'])
            
        except Exception as e:
            self.show_snackbar(f"数据加载失败: {str(e)}")


# ==================== 客户列表屏幕 ====================
class CustomerListScreen(BaseScreen):
    """客户列表屏幕"""
    
    def on_enter(self):
        self.load_customers()
    
    def load_customers(self, search=""):
        """加载客户列表"""
        try:
            customers = db.get_all_customers(search)
            self.ids.customer_list.clear_widgets()
            
            for customer in customers:
                cid, name, phone, address, id_card, reg_date, status, notes, created, updated, balance, times = customer
                
                # 确定状态颜色
                if times <= 0:
                    status_color = COLORS['danger']
                    status_text = "已用完"
                elif times <= 2:
                    status_color = COLORS['warning']
                    status_text = "即将用完"
                else:
                    status_color = COLORS['success']
                    status_text = "正常"
                
                item = ThreeLineListItem(
                    text=f"{name}  {phone}",
                    secondary_text=f"余额: ¥{balance:.0f}  剩余: {times}次",
                    tertiary_text=f"状态: {status_text}",
                    on_release=lambda x, cid=cid: self.show_customer_detail(cid)
                )
                self.ids.customer_list.add_widget(item)
                
        except Exception as e:
            self.show_snackbar(f"加载失败: {str(e)}")
    
    def search_customers(self, text):
        """搜索客户"""
        self.load_customers(text)
    
    def show_customer_detail(self, customer_id):
        """显示客户详情"""
        app = MDApp.get_running_app()
        app.customer_id = customer_id
        app.root.current = 'customer_detail'


# ==================== 客户详情屏幕 ====================
class CustomerDetailScreen(BaseScreen):
    """客户详情屏幕"""
    
    def on_enter(self):
        self.load_customer()
    
    def load_customer(self):
        """加载客户详情"""
        app = MDApp.get_running_app()
        customer_id = getattr(app, 'customer_id', None)
        
        if not customer_id:
            self.show_snackbar("客户ID错误")
            return
        
        try:
            customer = db.get_customer(customer_id)
            if not customer:
                self.show_snackbar("客户不存在")
                return
            
            # 更新界面
            self.ids.customer_name.text = customer['name']
            self.ids.customer_phone.text = customer['phone']
            self.ids.customer_address.text = customer['address'] or '未填写'
            self.ids.remaining_amount.text = f"¥{customer['remaining_amount']:.2f}"
            self.ids.remaining_times.text = f"{customer['remaining_times']}次"
            
            # 保存客户ID用于后续操作
            self.current_customer = customer
            
        except Exception as e:
            self.show_snackbar(f"加载失败: {str(e)}")
    
    def go_recharge(self):
        """去充值"""
        if hasattr(self, 'current_customer'):
            app = MDApp.get_running_app()
            app.customer_id = self.current_customer['id']
            app.root.current = 'recharge'
    
    def go_consume(self):
        """去消费"""
        if hasattr(self, 'current_customer'):
            app = MDApp.get_running_app()
            app.customer_id = self.current_customer['id']
            app.root.current = 'consume'


# ==================== 充值屏幕 ====================
class RechargeScreen(BaseScreen):
    """充值屏幕"""
    
    def on_enter(self):
        self.load_customer()
    
    def load_customer(self):
        """加载客户信息"""
        app = MDApp.get_running_app()
        customer_id = getattr(app, 'customer_id', None)
        
        if not customer_id:
            self.show_snackbar("请先选择客户")
            return
        
        try:
            customer = db.get_customer(customer_id)
            if customer:
                self.ids.customer_info.text = f"客户: {customer['name']}  电话: {customer['phone']}"
                self.current_customer = customer
        except Exception as e:
            self.show_snackbar(f"加载失败: {str(e)}")
    
    def do_recharge(self):
        """执行充值"""
        if not hasattr(self, 'current_customer'):
            self.show_snackbar("客户信息错误")
            return
        
        try:
            amount = float(self.ids.amount_input.text or 0)
            times = int(self.ids.times_input.text or 0)
            gift_amount = float(self.ids.gift_amount_input.text or 0)
            gift_times = int(self.ids.gift_times_input.text or 0)
            
            if amount <= 0 or times <= 0:
                self.show_snackbar("金额和次数必须大于0")
                return
            
            success, result = db.recharge(
                customer_id=self.current_customer['id'],
                amount=amount,
                times=times,
                gift_amount=gift_amount,
                gift_times=gift_times,
                payment_method=self.ids.payment_method.text
            )
            
            if success:
                self.show_dialog("成功", "充值成功！")
                self.clear_inputs()
            else:
                self.show_snackbar(f"充值失败: {result}")
                
        except ValueError:
            self.show_snackbar("请输入正确的数字")
        except Exception as e:
            self.show_snackbar(f"充值失败: {str(e)}")
    
    def clear_inputs(self):
        """清空输入"""
        self.ids.amount_input.text = ""
        self.ids.times_input.text = ""
        self.ids.gift_amount_input.text = ""
        self.ids.gift_times_input.text = ""


# ==================== 消费屏幕 ====================
class ConsumeScreen(BaseScreen):
    """消费屏幕"""
    
    service_types = ['日常保洁', '深度保洁', '开荒保洁', '家电清洗', '保姆服务', '月嫂服务', '其他']
    
    def on_enter(self):
        self.load_customer()
        self.setup_service_type_menu()
    
    def setup_service_type_menu(self):
        """设置服务类型下拉菜单"""
        menu_items = [
            {"text": st, "on_release": lambda x=st: self.set_service_type(x)}
            for st in self.service_types
        ]
        self.menu = MDDropdownMenu(
            caller=self.ids.service_type_btn,
            items=menu_items,
            width_mult=4
        )
    
    def set_service_type(self, text):
        """设置服务类型"""
        self.ids.service_type_btn.text = text
        self.menu.dismiss()
    
    def load_customer(self):
        """加载客户信息"""
        app = MDApp.get_running_app()
        customer_id = getattr(app, 'customer_id', None)
        
        if not customer_id:
            self.show_snackbar("请先选择客户")
            return
        
        try:
            customer = db.get_customer(customer_id)
            if customer:
                self.ids.customer_info.text = f"客户: {customer['name']}  剩余: {customer['remaining_times']}次"
                self.current_customer = customer
        except Exception as e:
            self.show_snackbar(f"加载失败: {str(e)}")
    
    def do_consume(self):
        """执行消费"""
        if not hasattr(self, 'current_customer'):
            self.show_snackbar("客户信息错误")
            return
        
        try:
            times = int(self.ids.times_input.text or 0)
            service_type = self.ids.service_type_btn.text
            service_person = self.ids.person_input.text
            
            if times <= 0:
                self.show_snackbar("消费次数必须大于0")
                return
            
            if service_type == '选择服务类型':
                self.show_snackbar("请选择服务类型")
                return
            
            success, result = db.consume(
                customer_id=self.current_customer['id'],
                service_type=service_type,
                consume_times=times,
                service_person=service_person
            )
            
            if success:
                msg = f"消费成功！\n本次消费: ¥{result['consume_amount']:.2f}\n剩余次数: {result['remaining_times']}次"
                self.show_dialog("成功", msg)
                self.clear_inputs()
            else:
                self.show_snackbar(f"消费失败: {result}")
                
        except ValueError:
            self.show_snackbar("请输入正确的数字")
        except Exception as e:
            self.show_snackbar(f"消费失败: {str(e)}")
    
    def clear_inputs(self):
        """清空输入"""
        self.ids.times_input.text = ""
        self.ids.person_input.text = ""
        self.ids.service_type_btn.text = "选择服务类型"


# ==================== 员工列表屏幕 ====================
class EmployeeListScreen(BaseScreen):
    """员工列表屏幕"""
    
    def on_enter(self):
        """进入屏幕时加载数据"""
        self.load_employees()
        self.load_stats()
    
    def load_employees(self, search=""):
        """加载员工列表"""
        self.ids.employee_list.clear_widgets()
        
        try:
            employees = db.get_all_employees(search=search, status='在职')
            
            if not employees:
                self.ids.employee_list.add_widget(
                    MDLabel(
                        text="暂无员工数据",
                        halign="center",
                        theme_text_color="Secondary"
                    )
                )
                return
            
            for emp in employees:
                # 技能标签
                skills_text = emp['skills'] if emp['skills'] else "未设置"
                
                item = ThreeLineListItem(
                    text=f"{emp['name']}  ⭐{emp['rating']}",
                    secondary_text=f"工龄: {emp['work_years']}年  技能: {skills_text}",
                    tertiary_text=f"评价: {emp['review_count']}条",
                    on_release=lambda x, eid=emp['id']: self.show_employee_detail(eid)
                )
                self.ids.employee_list.add_widget(item)
                
        except Exception as e:
            self.show_snackbar(f"加载失败: {str(e)}")
    
    def load_stats(self):
        """加载统计"""
        try:
            stats = db.get_employee_stats()
            self.ids.active_count.text = str(stats['active_count'])
            self.ids.avg_rating.text = str(stats['avg_rating'])
        except Exception as e:
            pass
    
    def search_employees(self, text):
        """搜索员工"""
        self.load_employees(text)
    
    def show_employee_detail(self, employee_id):
        """显示员工详情"""
        app = MDApp.get_running_app()
        app.employee_id = employee_id
        app.root.current = 'employee_detail'


# ==================== 员工详情屏幕 ====================
class EmployeeDetailScreen(BaseScreen):
    """员工详情屏幕"""
    
    def on_enter(self):
        self.load_employee()
    
    def load_employee(self):
        """加载员工详情"""
        app = MDApp.get_running_app()
        employee_id = getattr(app, 'employee_id', None)
        
        if not employee_id:
            self.show_snackbar("员工ID错误")
            return
        
        try:
            emp = db.get_employee(employee_id)
            if emp:
                self.ids.emp_name.text = emp['name']
                self.ids.emp_info.text = f"工龄: {emp['work_years']}年  年龄: {emp['age']}岁"
                self.ids.emp_skills.text = f"技能: {emp['skills'] if emp['skills'] else '未设置'}"
                self.ids.emp_rating.text = f"⭐ {emp['rating']} ({emp['review_count']}条评价)"
                self.current_employee = emp
            else:
                self.show_snackbar("员工不存在")
        except Exception as e:
            self.show_snackbar(f"加载失败: {str(e)}")
    
    def show_qrcode(self):
        """显示员工二维码"""
        if hasattr(self, 'current_employee'):
            emp = self.current_employee
            qr_url = f"https://scjmj.cn/employee.php?id={emp['id']}"
            self.show_dialog(
                "员工电子名片",
                f"{emp['name']}的二维码链接:\n\n{qr_url}\n\n客户扫码即可查看员工详情"
            )


# ==================== 添加客户屏幕 ====================
class AddCustomerScreen(BaseScreen):
    """添加客户屏幕"""
    
    def save_customer(self):
        """保存客户"""
        name = self.ids.name_input.text.strip()
        phone = self.ids.phone_input.text.strip()
        address = self.ids.address_input.text.strip()
        notes = self.ids.notes_input.text.strip()
        
        if not name:
            self.show_snackbar("姓名不能为空")
            return
        
        if not phone:
            self.show_snackbar("电话不能为空")
            return
        
        success, result = db.add_customer(name, phone, address, notes=notes)
        
        if success:
            self.show_dialog("成功", f"客户添加成功！ID: {result}")
            self.clear_inputs()
        else:
            self.show_snackbar(f"添加失败: {result}")
    
    def clear_inputs(self):
        """清空输入"""
        self.ids.name_input.text = ""
        self.ids.phone_input.text = ""
        self.ids.address_input.text = ""
        self.ids.notes_input.text = ""


# ==================== 主应用类 ====================
class HousekeepingApp(MDApp):
    """主应用类"""
    
    customer_id = None  # 当前选中的客户ID
    
    def build(self):
        """构建应用"""
        # 设置主题
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Amber"
        
        # 创建屏幕管理器
        sm = ScreenManager(transition=SlideTransition())
        
        # 添加屏幕
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(CustomerListScreen(name='customer_list'))
        sm.add_widget(CustomerDetailScreen(name='customer_detail'))
        sm.add_widget(EmployeeListScreen(name='employee_list'))
        sm.add_widget(EmployeeDetailScreen(name='employee_detail'))
        sm.add_widget(RechargeScreen(name='recharge'))
        sm.add_widget(ConsumeScreen(name='consume'))
        sm.add_widget(AddCustomerScreen(name='add_customer'))

        return sm


# ==================== 启动应用 ====================
if __name__ == '__main__':
    HousekeepingApp().run()
