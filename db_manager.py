import os
import psycopg2
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "diet_db.db")

def get_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "diet_db"),
            user=os.getenv("DB_USER", "myuser"),
            password=os.getenv("DB_PASS"),
            port=os.getenv("DB_PORT", "5432")
        )
    except Exception as e:
        print(f"❌ 資料庫連線失敗: {e}")
        return None

def save_diet_record(food_name, calories, protein, fat, carbs, meal_type):
    conn = get_connection()
    if not conn: return
    try:
        cur = conn.cursor()
        # 注意：如果資料庫欄位設有 DEFAULT CURRENT_DATE，就不需要手動傳 created_at
        query = """
        INSERT INTO diet_logs (food_name, calories, protein, fat, carbs, meal_type, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE);
        """
        cur.execute(query, (food_name, calories, protein, fat, carbs, meal_type))
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"❌ 儲存失敗: {e}")
    finally:
        conn.close()

def get_today_records():
    """讀取今日紀錄"""
    conn = None
    rows = []
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # 修正：如果你的 created_at 是時區相關，這行最穩
        sql = """
                SELECT id, food_name, calories, protein, fat, carbs, meal_type 
                FROM diet_logs 
                WHERE created_at = CURRENT_DATE 
                ORDER BY id DESC; 
                """
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
    except Exception as e:
        print(f"❌ 資料庫讀取失敗: {e}")
    finally:
        if conn:
            conn.close()
    return rows

def get_today_summary():
    """使用 SQL SUM 進行聚合運算，獲取今日營養總和"""
    conn = None
    summary = {"total_cal": 0, "total_protein": 0, "total_fat": 0, "total_carbs": 0}
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # SQL 聚合函數：直接計算總和
        sql = """
            SELECT 
                SUM(calories) as total_cal, 
                SUM(protein) as total_protein, 
                SUM(fat) as total_fat, 
                SUM(carbs) as total_carbs 
            FROM diet_logs 
            WHERE record_date = CURRENT_DATE
        """
        cur.execute(sql)
        row = cur.fetchone()
        if row and row['total_cal'] is not None:
            summary = {
                "total_cal": row['total_cal'],
                "total_protein": row['total_protein'],
                "total_fat": row['total_fat'],
                "total_carbs": row['total_carbs']
            }
        cur.close()
    except Exception as e:
        print(f"❌ 統計讀取失敗: {e}")
    finally:
        if conn:
            conn.close()
    return summary

def delete_record(record_id):
    """根據 ID 刪除指定的飲食紀錄"""
    conn = get_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        # 使用 WHERE id = %s 來確保只刪除那一筆特定資料
        query = "DELETE FROM diet_logs WHERE id = %s;"
        cur.execute(query, (record_id,))
        
        conn.commit()  # 記得一定要 Commit，不然資料庫不會真的刪掉
        cur.close()
        print(f"✅ 成功刪除 ID: {record_id} 的紀錄")
    except Exception as e:
        print(f"❌ 刪除失敗: {e}")
    finally:
        conn.close()

def get_setting(key, default_value):
    """從資料庫讀取設定值"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT value FROM user_settings WHERE key = %s", (key,))
        row = cur.fetchone()
        # 如果有資料就回傳，沒有就回傳預設值
        return row[0] if row else default_value
    except Exception as e:
        print(f"❌ 讀取設定失敗: {e}")
        return default_value
    finally:
        conn.close()

def update_setting(key, value):
    """更新或插入設定值 (Upsert)"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        # 使用 ON CONFLICT 來處理：如果 key 已存在就更新，不存在就插入
        query = """
        INSERT INTO user_settings (key, value) VALUES (%s, %s)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
        """
        cur.execute(query, (key, str(value)))
        conn.commit()
    except Exception as e:
        print(f"❌ 更新設定失敗: {e}")
    finally:
        conn.close()
def save_exercise_record(name, calories, duration):
    """存入運動紀錄"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        query = """
        INSERT INTO exercise_logs (exercise_name, calories_burned, duration_min)
        VALUES (%s, %s, %s);
        """
        cur.execute(query, (name, calories, duration))
        conn.commit()
    except Exception as e:
        print(f"❌ 運動紀錄儲存失敗: {e}")
    finally:
        conn.close()

def get_today_exercise():
    """讀取今日運動總消耗"""
    conn = get_connection()
    total = 0
    try:
        cur = conn.cursor()
        cur.execute("SELECT SUM(calories_burned) FROM exercise_logs WHERE record_date = CURRENT_DATE")
        row = cur.fetchone()
        total = row[0] if row[0] else 0
    finally:
        conn.close()
    return total

def get_weekly_summary():
    """撈取過去七天熱量趨勢 (PostgreSQL 版)"""
    conn = get_connection()
    if not conn: return pd.DataFrame()
    
    # PostgreSQL 的時間語法與 SQLite 不同
    # 我們使用 CURRENT_DATE - INTERVAL '7 days'
    query = """
    SELECT created_at::date as diet_date, SUM(calories) as daily_total 
    FROM diet_logs
    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY created_at::date
    ORDER BY diet_date ASC;
    """
    
    try:
        # PostgreSQL 使用 read_sql，且不需要 params
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"❌ 趨勢資料讀取失敗：{e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_weekly_nutrition():
    """撈取過去七天營養比例 (PostgreSQL 版)"""
    conn = get_connection()
    if not conn: return pd.DataFrame()
    
    # PostgreSQL 使用 COALESCE 代替 IFNULL
    query = """
    SELECT 
        COALESCE(SUM(protein), 0) as total_protein, 
        COALESCE(SUM(fat), 0) as total_fat, 
        COALESCE(SUM(carbs), 0) as total_carbs 
    FROM diet_logs
    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days';
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"❌ 營養比例讀取失敗: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def delete_record(record_id):
    conn = get_connection() # 確保這是連到 PostgreSQL
    if not conn: return
    try:
        cur = conn.cursor()
        # PostgreSQL 使用 %s 作為佔位符
        cur.execute("DELETE FROM diet_logs WHERE id = %s", (record_id,))
        conn.commit() # <--- 沒這行，資料就不會真的消失
        cur.close()
    except Exception as e:
        print(f"刪除失敗: {e}")
    finally:
        conn.close()