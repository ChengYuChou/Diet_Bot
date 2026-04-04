# 🥗 AI 飲食追蹤助手 (Diet Bot)

這是一個結合 **AI 語意分析**與**資料視覺化**的飲食管理系統。透過容器化技術 (Docker) 部署資料庫，並使用 Streamlit 打造直觀的互動介面，旨在簡化每日營養攝取的紀錄流程。

## 🚀 技術架構 (Tech Stack)

* **前端開發**: [Streamlit](https://streamlit.io/) - 快速建構資料互動網頁。
* **數據視覺化**: [Plotly](https://plotly.com/python/) - 動態生成營養比例圓餅圖。
* **後端邏輯**: Python 3.10+
* **資料庫**: [PostgreSQL](https://www.postgresql.org/) - 關聯式資料庫，確保資料持久化。
* **基礎設施**: [Docker](https://www.docker.com/) - 使用 Docker Compose 管理資料庫環境。
* **版本控制**: Git & GitHub - 遵循資管開發標準流程。

## 📂 專案目錄結構

```text
diet-bot-project/
├── app.py                 # Streamlit 主程式 (UI 與互動邏輯)
├── db_manager.py          # 資料庫存取層 (SQL CRUD 邏輯)
├── database.py            # 資料庫初始設定測試
├── API_check.py           # API 連線驗證工具
├── docker-compose.yml     # Docker 容器配置檔案
├── requirements.txt       # 專案套件相依清單
├── .gitignore             # Git 忽略清單 (保護 .env 與 .venv)
└── README.md              # 專案說明文件 (本檔案)