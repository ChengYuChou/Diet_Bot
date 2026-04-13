import os
from google import genai
from dotenv import load_dotenv

# 1. 初始化環境與 Client
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def start_chat():
    print("=== 🤖 Gemini 3 互動模式 (輸入 'quit' 結束) ===")
    
    # 建立一個簡易的問答循環
    while True:
        user_input = input("\n👤 你：")
        
        if user_input.lower() in ['quit', 'exit', '離開', 'c']:
            print("👋 下次見！")
            break
            
        try:
            # 2. 發送請求
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=[
        "你是一位專業的台灣營養師。請根據使用者的描述，估算食物的熱量（大卡）與三大營養素（蛋白質、脂肪、碳水）。",
        "使用者說：『我剛才吃了一碗中份的排骨便當，有一塊排骨和三個配菜。』"
    ]
            )
            
            # 3. 取得回應 (處理可能出現的 thought_signature)
            print(f"🤖 Gemini：{response.text}")
            
        except Exception as e:
            print(f"❌ 發生錯誤：{e}")

if __name__ == "__main__":
    start_chat()