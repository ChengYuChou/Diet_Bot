import os
import psycopg2
from dotenv import load_dotenv

# 1. 載入 .env 檔案裡的變數
load_dotenv()

def get_db_connection():
    try:
        # 2. 從環境變數讀取資訊，避免將密碼寫死在程式碼中
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS")
        )
        return conn
    except Exception as e:
        print(f"❌ 無法連線到資料庫: {e}")
        return None

def insert_diet_log(food, kcal, protein):
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        sql = "INSERT INTO diet_logs (food_name, calories, protein) VALUES (%s, %s, %s)"
        cur.execute(sql, (food, kcal, protein))
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ 成功存入: {food} ({kcal} kcal)")

if __name__ == "__main__":
    # 測試一下是否能運作
    print("正在測試資料庫連線...")
    insert_diet_log("測試晚餐", 500, 20.5)
    insert_diet_log("測試早餐",300,14)