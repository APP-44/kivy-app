"""
嘉美净家政VIP管理系统 - 模拟运行版本
测试数据库连接和核心功能
"""

import sys
import pymysql
from datetime import datetime, timedelta

DB_CONFIG = {
    'host': '106.14.254.13',
    'port': 3306,
    'user': 'app',
    'password': 'app123456',
    'database': 'housekeeping',
    'charset': 'utf8mb4',
}

def test_database_connection():
    print("=" * 50)
    print("Test database connection...")
    print("=" * 50)
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        print("[OK] Database connected!")
        
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM vip_customers')
        count = cursor.fetchone()[0]
        print(f"[OK] Total customers: {count}")
        
        cursor.execute('SELECT COUNT(*) FROM employees')
        emp_count = cursor.fetchone()[0]
        print(f"[OK] Total employees: {emp_count}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"[FAIL] Database connection failed: {e}")
        return False

def test_list_customers():
    print("\n" + "=" * 50)
    print("Test get customer list...")
    print("=" * 50)
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.id, c.name, c.phone, c.address,
                COALESCE((SELECT SUM(total_amount) FROM recharge_records WHERE customer_id = c.id), 0) -
                COALESCE((SELECT SUM(consume_amount) FROM consumption_records WHERE customer_id = c.id), 0) as balance,
                COALESCE((SELECT SUM(total_times) FROM recharge_records WHERE customer_id = c.id), 0) -
                COALESCE((SELECT SUM(consume_times) FROM consumption_records WHERE customer_id = c.id), 0) as times
            FROM vip_customers c
            ORDER BY c.created_at DESC
            LIMIT 10
        ''')
        
        customers = cursor.fetchall()
        
        print(f"\nFirst {len(customers)} customers:")
        print("-" * 50)
        for customer in customers:
            cid, name, phone, address, balance, times = customer
            status = "Normal" if times > 2 else "Warning" if times > 0 else "Empty"
            print(f"ID: {cid} | {name} | {phone}")
            print(f"   Address: {address}")
            print(f"   Balance: {balance:.0f} | Remaining: {times} | Status: {status}")
            print()
        
        conn.close()
        return True
    except Exception as e:
        print(f"[FAIL] Get customer list failed: {e}")
        return False

def test_list_employees():
    print("\n" + "=" * 50)
    print("Test get employee list...")
    print("=" * 50)
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, age, work_years, skills, rating, review_count, status 
            FROM employees 
            ORDER BY status DESC, rating DESC
            LIMIT 10
        ''')
        
        employees = cursor.fetchall()
        
        print(f"\nFirst {len(employees)} employees:")
        print("-" * 50)
        for emp in employees:
            emp_id, name, age, work_years, skills, rating, review_count, status = emp
            print(f"ID: {emp_id} | {name} | Age: {age} | Years: {work_years}")
            print(f"   Skills: {skills}")
            print(f"   Rating: {rating} ({review_count} reviews) | Status: {status}")
            print()
        
        conn.close()
        return True
    except Exception as e:
        print(f"[FAIL] Get employee list failed: {e}")
        return False

def test_api_sync():
    print("\n" + "=" * 50)
    print("Test API sync to virtual host...")
    print("=" * 50)
    
    import requests
    import urllib.parse
    
    API_CONFIG = {
        'enabled': True,
        'url': 'https://scjmj.cn/api_sync.php',
        'key': 'jiameijing2024',
    }
    
    try:
        params = {
            'key': API_CONFIG['key'],
            'action': 'list'
        }
        
        url = f"{API_CONFIG['url']}?{urllib.parse.urlencode(params)}"
        print(f"Request URL: {url[:80]}...")
        
        response = requests.get(url, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"Response: {result}")
            except:
                print(f"Response text: {response.text[:200]}")
        
        return True
    except Exception as e:
        print(f"[FAIL] API sync test failed: {e}")
        return False

def show_dashboard():
    print("\n" + "=" * 50)
    print("Dashboard Statistics")
    print("=" * 50)
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
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
        
        print(f"""
[CUSTOMER STATISTICS]
   Total customers: {total_customers}
   VIP customers: {vip_customers}

[RECHARGE STATISTICS]
   Total recharge: {total_recharge:,.0f}
   Total times: {total_times}

[CONSUMPTION STATISTICS]
   Total consume: {total_consume:,.0f}
   Consume times: {total_consume_times}

[CURRENT BALANCE]
   Remaining amount: {current_balance:,.0f}
   Remaining times: {current_times}
""")
        
        conn.close()
        return True
    except Exception as e:
        print(f"[FAIL] Get statistics failed: {e}")
        return False

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print(" JiaMeiJing Housekeeping VIP System - Test Run")
    print("=" * 50)
    
    if not test_database_connection():
        print("\nDatabase connection failed, please check config!")
        exit(1)
    
    show_dashboard()
    test_list_customers()
    test_list_employees()
    test_api_sync()
    
    print("\n" + "=" * 50)
    print("[SUCCESS] Test run completed!")
    print("=" * 50)
