import os
import requests
import db_manager  # 💡 確保有引入 db_manager 

def send_to_discord(content: str) -> bool:
    """將文字內容透過 Webhook 推播至 Discord（內建自動切片機制，防止超過 2000 字限制）"""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("❌ 錯誤：未在 .env 中設定 DISCORD_WEBHOOK_URL")
        return False
        
    # Discord 單則訊息最大限制為 2000 字，保險起見我們用 1900 字當一切片
    MAX_LENGTH = 1900
    
    # 如果內容小於限制，直接發送即可
    if len(content) <= MAX_LENGTH:
        chunks = [content]
    else:
        # 依照換行符號或字數精準切片，避免文字在中間被腰斬
        chunks = []
        lines = content.split('\n')
        current_chunk = ""
        for line in lines:
            if len(current_chunk) + len(line) + 1 > MAX_LENGTH:
                chunks.append(current_chunk)
                current_chunk = line
            else:
                if current_chunk:
                    current_chunk += "\n" + line
                else:
                    current_chunk = line
        if current_chunk:
            chunks.append(current_chunk)

    # 開始依序發送切片訊息
    try:
        all_success = True
        for idx, chunk in enumerate(chunks, 1):
            payload_content = chunk
            if len(chunks) > 1:
                payload_content += f"\n\n*(續下一則訊息... {idx}/{len(chunks)})*"

            payload = {
                "content": payload_content
            }
            
            response = requests.post(webhook_url, json=payload)
            
            if response.status_code != 204: 
                print(f"❌ 切片 {idx} 推播失敗，Discord 回傳代碼: {response.status_code}")
                all_success = False
                
        if all_success:
            print("🚀 [SUCCESS] 智慧週報已成功完整推播至 Discord！")
            return True
        return False

    except Exception as e:
        print(f"❌ 連線至 Discord 時發生異常: {str(e)}")
        return False

# ==========================================
# 🎯 核心修正：從資料庫撈取最新週報並推播
# ==========================================
def push_latest_report_from_db() -> bool:
    """直接從 PostgreSQL 資料庫撈取最新一筆週報建議，並發送到 Discord"""
    print("💾 正在從資料庫調閱最新一筆健檢報告...")
    
    # 1. 呼叫下方寫好的 db_manager 函數撈取資料
    latest_report = db_manager.get_latest_weekly_report()
    
    if not latest_report:
        print("⚠️ 提示：資料庫中目前沒有任何週報紀錄，取消推播。")
        return False
        
    # 2. 加上 Discord 的外觀包裝裝飾
    discord_message = f"📢 **【每週 AI 飲食智慧顧問健檢報告】** 🗓️\n\n{latest_report}"
    
    # 3. 執行安全推播並回傳結果
    return send_to_discord(discord_message)