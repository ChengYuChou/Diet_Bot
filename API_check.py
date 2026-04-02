import os
import google.generativeai as genai
from dotenv import load_dotenv

# 1. 載入環境變數
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ 錯誤：在 .env 中找不到 GEMINI_API_KEY")
    exit()

genai.configure(api_key=api_key)

# 2. 根據你剛才的清單，挑選三個最有可能成功的路徑
# 在 v1beta 模式下，必須使用 'models/' 前綴
test_targets = [
    'models/gemini-1.5-flash',
    'models/gemini-2.0-flash',
    'models/gemini-1.5-pro'
]

print(f"=== 🔍 Gemini API 深度診斷 (Python 3.9) ===")

for target in test_targets:
    print(f"\n📡 正在測試模型：{target}")
    try:
        # 建立模型實例
        model = genai.GenerativeModel(model_name=target)
        
        # 發送一個極簡的測試請求
        response = model.generate_content("Hi", generation_config={"max_output_tokens": 10})
        
        print(f"✅ 測試成功！")
        print(f"🤖 AI 回應：{response.text.strip()}")
        
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            print(f"❌ 錯誤 404：伺服器找不到這個路徑。請檢查模型名稱是否精確。")
        elif "429" in error_msg:
            print(f"❌ 錯誤 429：配額不足 (Limit: 0)。這通常是 Google 帳號或專案權限問題。")
        else:
            print(f"❌ 發生其他錯誤：\n{error_msg}")

print("\n" + "="*40)
print("💡 資管系 Debug 指南：")
print("1. 如果全部都 404 -> 代表你的 SDK 強制要求不同的路徑格式。")
print("2. 如果全部都 429 -> 代表你需要去 AI Studio 建立一個『全新專案』的 Key。")