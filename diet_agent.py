import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_tool_calling_agent
import db_manager

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0, 
    api_key=api_key
)

# ==========================================
# 🛠️ 工具一：計算今日剩餘飲食營養素預算
# ==========================================
@tool
def get_today_remaining_nutrition() -> str:
    """
    獲取使用者今天『剩餘』可攝取的熱量(kcal)與蛋白質(g)。
    當使用者詢問今天還能吃什麼、要求規劃晚餐/點心菜單，或詢問剩餘額度時，必須呼叫此工具。
    """
    # 1. 撈取使用者的熱量目標設定 (預設 2000)
    initial_goal = int(db_manager.get_setting('daily_calorie_goal', 2000))
    
    # 2. 撈取使用者今天所有的飲食紀錄
    records = db_manager.get_today_records()
    
    # 3. 計算今日已攝取總量
    total_calories = sum(r['calories'] for r in records) if records else 0
    total_protein = sum(r['protein'] for r in records) if records else 0
    
    # 4. 蛋白質動態目標邏輯 (體重 × 1.5)
    weight = 70.0 
    protein_goal = weight * 1.5
    
    # 5. 計算剩餘預算
    remaining_calories = initial_goal - total_calories
    remaining_protein = protein_goal - total_protein
    
    return f"今日已攝取熱量: {total_calories} kcal, 剩餘熱量預算: {remaining_calories} kcal | 今日已攝取蛋白質: {total_protein} g, 剩餘蛋白質需求: {remaining_protein:.1f} g"


# ==========================================
# 🛠️ 工具二：獲取今日運動消耗熱量 (活用運動數據)
# ==========================================
@tool
def get_today_exercise_burn() -> str:
    """
    獲取使用者今天透過運動額外消耗的熱量(kcal)。
    當使用者詢問『我今天有運動，可以多吃什麼』、評估總消耗熱量，或進行綜合飲食規劃時，必須呼叫此工具。
    """
    try:
        burned = db_manager.get_today_exercise()
        return f"使用者今日運動累計消耗熱量: {burned} kcal"
    except Exception as e:
        return f"無法獲取運動數據: {str(e)}"


# ==========================================
# 🛠️ 工具三：獲取過去七天營養統計 (活用週期大數據)
# ==========================================
@tool
def get_weekly_nutrition_trend() -> str:
    """
    獲取使用者過去七天累積的蛋白質、脂肪、碳水化合物總攝取克數。
    當使用者要求『評估我最近的飲食習慣』、『找出我減肥沒成效的原因』或做『每週飲食大檢討』時，必須呼叫此工具。
    """
    try:
        df_weekly = db_manager.get_weekly_nutrition()
        if df_weekly.empty:
            return "資料庫中目前尚無過去七天的飲食統計數據。"
        
        p = df_weekly['total_protein'].iloc[0]
        f = df_weekly['total_fat'].iloc[0]
        c = df_weekly['total_carbs'].iloc[0]
        return f"過去七天總攝取統計 -> 蛋白質: {p}g, 脂肪: {f}g, 碳水化合物: {c}g"
    except Exception as e:
        return f"無法獲取過去七天營養數據: {str(e)}"


# 🌟 把所有賦予 AI 超能力的工具通通塞進工具箱
tools = [get_today_remaining_nutrition, get_today_exercise_burn, get_weekly_nutrition_trend]

# ==========================================
# 3. 設計【智慧顧問級】的大腦思維與提示詞 (Prompt)
# ==========================================
prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一位精通資料分析與運動營養學的『智慧飲食規劃教練』。
你擁有讀取使用者本地 PostgreSQL 資料庫的特權工具。

【核心思維邏輯：數據交叉活用】
當使用者向你尋求飲食建議、晚餐推薦或近況檢討時，你【嚴禁】直接給出籠統的罐頭回答。你必須啟動以下資管推論鏈：
1. 【多維度調閱】：根據問題，主動組合呼叫多個工具（例如：要規劃晚餐，應同時查看『今日剩餘營養素』與『今日運動消耗』；要檢討習慣，必須查看『過去七天趨勢』）。
2. 【數據交叉診斷】：
   - 結合運動：如果使用者今天有運動（`get_today_exercise_burn` > 0），在規劃晚餐時可以適度放寬熱量預算，並強調補充蛋白質修復肌肉。
   - 習慣檢視：檢視過去七天的三大營養素比例是否失衡（例如碳水化合物爆表或蛋白質過低）。
3. 【給出高價值洞察】：將冰冷的資料庫數字，轉化為有溫度的專業分析與『具體到可以直接去吃』的菜單提案。

【回覆格式規範】
請統一使用溫和流暢的繁體中文，並結構化為以下區塊回覆：
📊 【多維數據診斷報告】：（點出你從資料庫看見的今日剩餘、運動量或近日三大營養素比例趨勢）
💡 【教練私房盲點點評】：（一針見血指出使用者的飲食盲點或做得棒的地方）
🍽️ 【客製化智慧飲食提案】：（給出精準、符合今日賸餘預算、能補足營養缺口的具體食物推薦）"""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# 物理綁定工具箱到 LLM
llm_with_tools = llm.bind_tools(tools)

# 建立 Tool Calling Agent
agent = create_tool_calling_agent(llm_with_tools, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 5. 封裝給 Streamlit (app.py) 呼叫的接口
def ask_diet_agent(user_question: str) -> str:
    """接收 Streamlit 輸入，執行 Agent 思考並回傳最終答案"""
    try:
        response = agent_executor.invoke({"input": user_question})
        return response["output"]
    except Exception as e:
        return f"Agent 執行失敗，可能是環境或套件衝突：{str(e)}"