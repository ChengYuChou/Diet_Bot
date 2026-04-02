import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_manual_input():
    """模擬 AI 回傳格式的手動輸入函數"""
    print("\n--- 📝 手動營養成分輸入 ---")
    try:
        food = input("食物名稱 (如: 嫩煎雞腿蛋餅): ")
        cal = int(input("熱量 (kcal): "))
        pro = int(input("蛋白質 (g): "))
        fat = int(input("脂肪 (g): "))
        carb = int(input("碳水 (g): "))
        
        return {
            "food_item": food,
            "calories": cal,
            "protein": pro,
            "fat": fat,
            "carbs": carb,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except ValueError:
        print("❌ 錯誤：請輸入正確的數字格式！")
        return None

def save_to_db(data):
    """資料庫寫入邏輯 (之後補上 SQL 連線)"""
    print(f"\n💾 [DB 寫入成功]: {data['food_item']}")
    print(f"📊 詳細數據: {data}")

def main():
    print("=== 🥗 飲食紀錄機器人 (手動模式) ===")
    while True:
        data = get_manual_input()
        if data:
            save_to_db(data)
        
        if input("\n繼續記錄下一筆？(y/n): ").lower() != 'y':
            break

if __name__ == "__main__":
    main()