# 系統架構設計：數位時光膠囊

## 1. 技術架構說明

本專案採用經典的 MVC (Model-View-Controller) 架構模式，並以 Python Flask 框架作為核心開發基礎：

*   **選用技術與原因：**
    *   **Python + Flask**：輕量且靈活，非常適合快速開發與小型專案的後端邏輯。
    *   **Jinja2**：與 Flask 整合度高，能快速將後端資料渲染成 HTML 頁面，不需前後端分離，降低開發複雜度。
    *   **SQLite**：輕量級關聯式資料庫，無需額外安裝資料庫伺服器，資料直接存在本地檔案中，非常適合本專案的儲存需求。
*   **MVC 模式職責劃分：**
    *   **Model (模型)**：負責定義資料結構（膠囊標題、內容、解鎖日期、心情標籤等）以及與 SQLite 資料庫的互動。
    *   **View (視圖)**：負責呈現使用者介面，使用 HTML/CSS 與 Jinja2 模板動態顯示資料。
    *   **Controller (控制器)**：由 Flask 的路由 (Routes) 擔任，負責接收使用者的請求 (如：建立膠囊、查看列表)，呼叫 Model 處理資料，最後將結果傳遞給 View 渲染。

## 2. 專案資料夾結構

本專案的資料夾結構設計如下，旨在讓程式碼職責分離，方便後續維護與擴充：

```text
time5.demo/
├── app/                      # 應用程式主程式庫
│   ├── __init__.py           # Flask App 初始化設定
│   ├── models.py             # 資料庫模型 (定義 Capsule 等資料表)
│   ├── routes/               # 路由模組 (Controller)
│   │   ├── __init__.py
│   │   └── main_routes.py    # 主要頁面路由與 API (如建立、讀取膠囊)
│   ├── templates/            # Jinja2 HTML 模板 (View)
│   │   ├── base.html         # 共用版面 (Header, Footer)
│   │   ├── index.html        # 首頁 (倒數計時與統計)
│   │   ├── create.html       # 建立膠囊頁面
│   │   └── list.html         # 回憶清單與解鎖頁面
│   └── static/               # 靜態資源 (CSS, JavaScript, 圖片)
│       ├── css/
│       │   └── style.css     # 全局樣式
│       ├── js/
│       │   └── main.js       # 互動邏輯 (如倒數計時計算)
│       └── images/           # 預設圖片與素材
├── instance/                 # 本地端運行資料 (不進版控)
│   └── database.db           # SQLite 資料庫檔案
├── docs/                     # 專案文件 (PRD, 架構圖等)
│   ├── PRD.md                # 產品需求文件
│   └── ARCHITECTURE.md       # 系統架構設計文件
├── app.py                    # 專案啟動入口 (執行此檔啟動伺服器)
├── requirements.txt          # Python 依賴套件清單
└── README.md                 # 專案說明文件
```

## 3. 元件關係圖

以下展示使用者從瀏覽器操作時，系統內部的資料流與元件互動關係：

```mermaid
graph TD
    Browser[瀏覽器 (Browser)]
    
    subgraph Flask Application
        Route[Flask 路由 (Controller)]
        Model[資料模型 (Model)]
        Template[Jinja2 模板 (View)]
    end
    
    Database[(SQLite 資料庫)]
    
    Browser -- "1. 發送 HTTP 請求\n(例如：建立膠囊, 瀏覽列表)" --> Route
    Route -- "2. 查詢/寫入資料" --> Model
    Model -- "3. 執行 SQL 指令" --> Database
    Database -- "4. 回傳資料結果" --> Model
    Model -- "5. 將資料轉交" --> Route
    Route -- "6. 傳遞資料與狀態" --> Template
    Template -- "7. 渲染 HTML 頁面" --> Route
    Route -- "8. 回傳 HTTP 回應" --> Browser
```

## 4. 關鍵設計決策

1.  **整合式渲染 (Server-Side Rendering)**：
    *   **原因**：為了快速驗證想法與完成 MVP，我們選擇不用 React/Vue 進行前後端分離，而是利用 Jinja2 在伺服器端直接渲染畫面。這樣可以減少 API 的設計負擔，並降低開發與部署的複雜度。
2.  **檔案型資料庫 (SQLite)**：
    *   **原因**：時光膠囊 MVP 版本主要著重於功能驗證與單機/輕量運行，不需要承載高併發流量。使用 SQLite 可以免去資料庫伺服器的建置與維護成本。
3.  **時間鎖的後端驗證機制**：
    *   **原因**：為了確保「解鎖日期」的機制不被輕易破解，時間鎖的驗證必須在後端 (Flask Route) 執行。前端只負責顯示倒數計時，任何對未解鎖膠囊內容的存取請求，後端都會檢查當前時間，若未到期則拒絕回傳真實內容。
4.  **心情標籤的純文字儲存 (MVP 階段)**：
    *   **原因**：初期為了簡化資料表關聯，心情標籤 (Mood Tags) 將以逗號分隔的字串直接存入 Capsule 資料表中，而非建立獨立的 Tag 資料表。這能在不影響查詢體驗的前提下，加快開發速度。
