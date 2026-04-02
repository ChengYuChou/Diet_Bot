import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# 1. 載入環境變數
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ 錯誤：找不到 API Key，請檢查 .env 檔案")
    exit()

# 配置 Gemini API
genai.configure(api_key=api_key)

# 使用最新穩定版路徑，避開 404 與 429 Limit: 0 錯誤
# 根據你的清單與最新指南，這個名稱是最保險的
MODEL_NAME = 'models/gemini-2.0-flash'
model = genai.GenerativeModel(MODEL_NAME)

def analyze_diet(user_input):
    """使用 AI 分析飲食內容並回傳 JSON 格式"""
    prompt = f"""
    你是一個營養專家，請分析使用者的飲食內容："{user_input}"。
    請精確回傳以下 JSON 格式（不要包含任何額外文字或 Markdown 標籤）：
    {{
        "food_item": "食物名稱",
        "calories": 數字(kcal),
        "protein": 數字(g),
        "fat": 數字(g),
        "carbs": 數字(g)
    }}
    """
    
    try:
        print(f"\n🤖 AI 正在努力分析：'{user_input}'...")
        response = model.generate_content(prompt)
        
        # 清除 AI 可能夾帶的 Markdown 語法 (例如 ```json)
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_text)
        
    except Exception as e:
        error_msg = str(e)
        print("\n😱 糟糕！處理過程中出錯了：")
        
        if "429" in error_msg:
            print(">>> [錯誤 429]：API 配額不足。請確認是否已等待 5 分鐘，或更換新專案的 API Key。")
        elif "404" in error_msg:
            print(f">>> [錯誤 404]：模型路徑 '{MODEL_NAME}' 無法辨識，請嘗試 API_check 腳本中的其他名稱。")
        else:
            print(f">>> 發生未知錯誤：{error_msg}")
            
        return None

def save_to_db(data):
    """將分析結果存入資料庫 (此處可對應你的 Docker 資料庫邏輯)"""
    # 這裡預留給你的資料庫存取程式碼 (例如 psycopg2 或 SQLAlchemy)
    print(f"✅ 成功解析：{data['food_item']} ({data['calories']} kcal)")
    print("💾 資料已準備好存入 Docker 資料庫...")

def main():
    print("=== 🥗 我的 AI 飲食紀錄機器人 ===")
    print(f"當前使用模型：{MODEL_NAME}")
    
    user_input = input("請輸入你剛才吃了什麼（例如：一份雞排跟珍奶）：\n> ")
    
    if not user_input.strip():
        print("請輸入有效的內容！")
        return

    result = analyze_diet(user_input)
    
    if result:
        save_to_db(result)
        print("\n🎉 紀錄完成！繼續加油保持健康！")
    else:
        print("\n💡 提示：請檢查 .env 裡的 API Key 是否正確，以及網路連線是否穩定。")

if __name__ == "__main__":
    main()