import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    # 這裡確保抓到 .env 的設定，若無則用你的預設值
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "diet_db"),
        user=os.getenv("DB_USER", "myuser"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT", "5432")
    )

def save_diet_record(data):
    """存入紀錄 (加入錯誤處理與自動關閉)"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        sql = """
            INSERT INTO diet_logs (food_name, calories, protein, fat, carbs)
            VALUES (%s, %s, %s, %s, %s)
        """
        cur.execute(sql, (
            data['food_name'], 
            data['calories'], 
            data['protein'], 
            data['fat'], 
            data['carbs']
        ))
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"❌ 資料庫寫入失敗: {e}")
        if conn:
            conn.rollback() # 發生錯誤時撤回交易
    finally:
        if conn:
            conn.close() # 無論成功失敗都關閉連線，避免連線數爆滿

def get_today_records():
    """讀取今日紀錄"""
    conn = None
    rows = []
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # 修正：如果你的 created_at 是時區相關，這行最穩
        sql = "SELECT * FROM diet_logs WHERE created_at >= CURRENT_DATE ORDER BY created_at DESC"
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
            WHERE created_at >= CURRENT_DATE
        """
        cur.execute(sql)
        row = cur.fetchone()
        if row and row['total_cal']: # 確保不是 None
            summary = row
        cur.close()
    except Exception as e:
        print(f"❌ 統計讀取失敗: {e}")
    finally:
        if conn:
            conn.close()
    return summary