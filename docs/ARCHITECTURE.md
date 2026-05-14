# GeoDrop 系統架構設計 (Architecture)

## 1. 技術架構說明

本專案採用經典的伺服器渲染（Server-Side Rendering, SSR）架構，不進行前後端分離，以求快速驗證想法並簡化部署。

### 選用技術與原因
- **後端框架：Python + Flask**
  - **原因**：輕量級、彈性高，適合快速建立 MVP，且 Python 有豐富的數學與地理運算函式庫，有利於後續演算法擴充。
- **模板引擎：Jinja2**
  - **原因**：Flask 內建，能快速將後端資料注入 HTML 頁面中渲染給前端，降低開發成本。
- **資料庫：SQLite**
  - **原因**：無需額外架設資料庫伺服器，檔案型資料庫即可滿足初期開發與 MVP 的儲存需求。
- **前端技術：HTML5 / CSS / Vanilla JS**
  - **原因**：使用原生 JavaScript 呼叫 HTML5 Geolocation API 來取得 GPS 定位，並透過簡單的 AJAX/Fetch 與後端進行經緯度資料驗證。

### Flask MVC 模式說明
- **Model（模型）**：負責與 SQLite 溝通，定義 `User`、`Package` (包裹)、`UnlockRecord` (解鎖紀錄) 等資料表結構與存取邏輯。
- **View（視圖）**：在此架構下為 Jinja2 Templates，負責將 HTML 呈現給使用者介面。
- **Controller（控制器）**：Flask 的 Routes，負責接收前端請求、呼叫 Model 處理業務邏輯（如判斷是否在 50 公尺內），最後將結果傳給 Jinja2 渲染畫面。

---

## 2. 專案資料夾結構

以下為 GeoDrop 專案的目錄結構規劃：

```text
time5.demo/
│
├── app/                      # Flask 應用主目錄
│   ├── __init__.py           # 建立 Flask App 實例與初始化
│   ├── models/               # 資料庫模型 (Model)
│   │   └── database.py       # 存放 User, Package, Record 等資料定義
│   ├── routes/               # Flask 路由 (Controller)
│   │   ├── main.py           # 主頁面、地圖相關路由
│   │   └── user.py           # 用戶登入、個人紀錄路由
│   ├── static/               # 靜態資源檔案
│   │   ├── css/
│   │   │   └── style.css     # 全域樣式與地圖樣式
│   │   └── js/
│   │       └── map.js        # 處理 HTML5 GPS 定位與地圖互動邏輯
│   └── templates/            # Jinja2 HTML 模板 (View)
│       ├── base.html         # 共用版型 (Header/Footer)
│       ├── index.html        # 首頁與地圖主畫面
│       ├── unlock.html       # 解鎖成功與包裹內容畫面
│       └── profile.html      # 個人歷史紀錄畫面
│
├── instance/                 # 存放不進版控的執行實例檔案
│   └── database.db           # SQLite 資料庫檔案
│
├── docs/                     # 專案文件
│   ├── PRD.md                # 產品需求文件
│   └── ARCHITECTURE.md       # 系統架構文件
│
├── .gitignore                # Git 忽略設定
├── requirements.txt          # Python 依賴套件清單
└── app.py                    # 專案啟動入口 (Entry Point)
```

---

## 3. 元件關係圖

以下圖示說明使用者（瀏覽器）如何與系統元件互動：

```mermaid
flowchart TD
    Browser[瀏覽器 (HTML/JS)]
    
    subgraph Server [Flask 伺服器]
        Route[Flask Route (Controller)]
        Model[資料庫模型 (Model)]
        Template[Jinja2 模板 (View)]
    end
    
    Database[(SQLite 資料庫)]
    
    Browser -- 1. HTTP Request (例如帶有 GPS 座標的解鎖請求) --> Route
    Route -- 2. 查詢/驗證包裹資料 --> Model
    Model -- 3. SQL 查詢 --> Database
    Database -- 4. 回傳資料 --> Model
    Model -- 5. 業務邏輯判斷 (距離計算) --> Route
    Route -- 6. 注入資料並渲染 --> Template
    Template -- 7. 產生最終 HTML --> Route
    Route -- 8. HTTP Response --> Browser
    Browser -- 9. 呼叫 HTML5 Geolocation API --> Browser
```

---

## 4. 關鍵設計決策

1. **GPS 圍欄偵測在後端驗證 (Server-side Verification)**
   - **決定**：前端 JS 負責持續取得使用者 GPS 並顯示在地圖上，但當使用者點擊「解鎖」時，前端必須將經緯度發送至後端，由後端計算距離是否小於 50 公尺來決定是否解鎖成功。
   - **原因**：若全由前端判斷，有心人士容易透過修改 JS 程式碼來作弊。後端驗證能確保解鎖邏輯的安全與公平性。

2. **隨機遞送演算法的觸發時機**
   - **決定**：MVP 階段採用「背景定時生成」或「管理員手動生成」批次處理，先在資料庫預先產生一批包裹，而非每次使用者開啟 App 時才即時計算生成。
   - **原因**：即時計算會大幅增加伺服器回應時間；預先生成可讓使用者查詢時只進行簡單的「地理範圍查詢（Bounding Box）」，提升地圖讀取效能。

3. **使用原生 Geolocation API 取代地圖 SDK 的強依賴**
   - **決定**：核心依賴於瀏覽器原生的 `navigator.geolocation` 取得經緯度，並透過簡單的 HTML DOM 顯示距離或結合輕量級開源地圖 (如 Leaflet.js)，而非強制綁定 Google Maps 商業 API。
   - **原因**：減少 MVP 開發初期的 API 費用成本，並確保系統核心邏輯（經緯度距離計算：Haversine 公式）獨立於第三方地圖圖資服務之外。
