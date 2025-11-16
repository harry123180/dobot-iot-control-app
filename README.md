# Dobot IoT Control App

物聯網機械臂控制系統 - 整合 Dobot 4軸機械臂與 IoT 技術的研究專案

## 專案簡介

本專案是一個基於物聯網技術的 Dobot 機械臂控制系統，透過 Python Flask 後端 API 與 Dobot 機械臂通訊，並提供前端應用介面供使用者控制機械臂執行各種動作。

## 系統架構

```
┌─────────────────────────────────────────────────────────────────┐
│                        Local Network                            │
│                      (192.168.1.x 網段)                          │
│                                                                 │
│  ┌──────────────┐                    ┌─────────────────────┐  │
│  │              │   HTTP REST API    │                     │  │
│  │  前端應用     │ ─────────────────> │   Flask Server      │  │
│  │   (APP/)     │                    │   (Python)          │  │
│  │              │ <───────────────── │                     │  │
│  └──────────────┘   JSON Response    │  - API 路由         │  │
│                                       │  - 業務邏輯         │  │
│   - Web UI                            │  - Dobot 通訊封裝   │  │
│   - Mobile App                        └─────────┬───────────┘  │
│   - Desktop App                                 │              │
│                                                 │ TCP/IP       │
│                                                 │ Socket       │
│                                                 ▼              │
│                                       ┌─────────────────────┐  │
│                                       │   Dobot 機械臂       │  │
│                                       │   (4-Axis Robot)    │  │
│                                       │                     │  │
│                                       │  IP: 192.168.1.6    │  │
│                                       │  Port 29999: 控制   │  │
│                                       │  Port 30003: 運動   │  │
│                                       │  Port 30004: 回饋   │  │
│                                       └─────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 通訊架構

### 1. 前端 ↔ 後端 (REST API)
- **協定**: HTTP/HTTPS
- **格式**: JSON
- **方式**: RESTful API
- **網路**: Local Network

### 2. 後端 ↔ Dobot (TCP/IP)
- **協定**: TCP/IP Socket
- **IP位址**: 192.168.1.6 (LAN1 連接埠)
- **連接埠**:
  - `29999`: Dashboard Port (控制端口)
  - `30003`: Move Port (運動端口)
  - `30004`: Feed Port (回饋端口)

## 目錄結構

```
dobot-iot-control-app/
├── Dobot/                          # Dobot API 及範例程式
│   ├── TCP-IP-4Axis-Python-main/   # Dobot TCP/IP Python SDK
│   │   ├── dobot_api.py           # Dobot API 封裝 (核心)
│   │   ├── PythonExample.py       # API 使用範例
│   │   ├── main.py                # Demo 主程式
│   │   ├── files/                 # 警告報警配置檔案
│   │   │   ├── alarm_controller.json
│   │   │   └── alarm_servo.json
│   │   └── README.md              # Dobot API 詳細說明
│   └── DobotDocs/                 # Dobot 官方文件
│       └── TCP_IP遠端控制介面文件（4軸）.pdf
│
├── server/                         # Flask 後端伺服器 (規劃中)
│   ├── app.py                     # Flask 應用主程式
│   ├── routes/                    # API 路由
│   ├── controllers/               # 業務邏輯控制器
│   ├── services/                  # Dobot 通訊服務
│   └── requirements.txt           # Python 相依套件
│
├── APP/                            # 前端應用 (規劃中)
│   ├── web/                       # Web 應用
│   ├── mobile/                    # 行動端應用
│   └── desktop/                   # 桌面應用
│
└── README.md                       # 專案說明文件
```

## Dobot API 說明

### Dobot API 類別結構

Dobot API 提供三個主要類別來控制機械臂：

#### 1. DobotApi (基礎通訊類別)
- 功能: 封裝 TCP Socket 通訊基礎業務
- 連接埠: 29999 / 30003 / 30004
- 方法:
  - `send_data()`: 傳送資料
  - `wait_reply()`: 接收回應
  - `sendRecvMsg()`: 同步傳送接收

#### 2. DobotApiDashboard (控制端口 - 29999)
- 功能: 機器人基本控制功能
- 主要方法:
  - `EnableRobot()`: 使能機器人
  - `DisableRobot()`: 去使能機器人
  - `ClearError()`: 清除錯誤
  - `ResetRobot()`: 機器人停止
  - `SpeedFactor(speed)`: 設定全域速度比例
  - `AccJ(speed)` / `AccL(speed)`: 設定加速度
  - `DO(index, status)`: 數位輸出控制
  - `GetAngle()`: 取得關節角度
  - `GetPose()`: 取得笛卡爾位姿

#### 3. DobotApiMove (運動端口 - 30003)
- 功能: 機器人運動控制
- 主要方法:
  - `MovJ(x, y, z, r)`: 關節運動 (點到點)
  - `MovL(x, y, z, r)`: 直線運動
  - `JointMovJ(j1, j2, j3, j4)`: 關節空間運動
  - `Arc(x1, y1, z1, r1, x2, y2, z2, r2)`: 圓弧運動
  - `Circle(...)`: 整圓運動
  - `MoveJog(axis_id)`: 點動運動
  - `Sync()`: 同步等待運動完成

#### 4. Feed Port (回饋端口 - 30004)
- 功能: 即時取得機器人狀態
- 資料型別: MyType (numpy 結構化陣列)
- 包含資訊:
  - 關節角度、速度、電流
  - 笛卡爾座標
  - 使能狀態、執行狀態
  - 錯誤狀態、報警資訊

### 連線範例

```python
from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove

# Dobot 機械臂 IP (LAN1)
ip = "192.168.1.6"

# 建立三個端口連線
dashboard = DobotApiDashboard(ip, 29999)  # 控制端口
move = DobotApiMove(ip, 30003)            # 運動端口
feed = DobotApi(ip, 30004)                # 回饋端口

# 使能機器人
dashboard.EnableRobot()

# 移動到指定位置 (笛卡爾座標)
move.MovL(200, 100, 50, 0)

# 等待運動完成
move.Sync()
```

## 快速開始

### 前置需求

1. **硬體**:
   - Dobot MG400 或 M1Pro 4軸機械臂
   - 乙太網路線 (連接至 LAN1 端口)
   - 電腦 (Windows/Linux/Mac)

2. **軟體**:
   - Python 3.7+
   - numpy: `pip install numpy`

3. **網路配置**:
   - 將電腦 IP 設定為 192.168.1.x 網段 (例如: 192.168.1.100)
   - 確保能夠 ping 通 Dobot IP: `ping 192.168.1.6`

### 執行 Dobot 範例

```bash
# 1. 複製專案
git clone https://github.com/your-repo/dobot-iot-control-app.git
cd dobot-iot-control-app

# 2. 安裝相依套件
pip install numpy

# 3. 執行範例程式
cd Dobot/TCP-IP-4Axis-Python-main
python PythonExample.py
```

### 啟動 Flask 伺服器 (規劃中)

```bash
# 1. 進入伺服器目錄
cd server

# 2. 安裝相依套件
pip install -r requirements.txt

# 3. 啟動伺服器
python app.py
```

## API 設計 (規劃)

### 機器人控制 API

```
POST   /api/robot/enable          # 使能機器人
POST   /api/robot/disable         # 去使能機器人
GET    /api/robot/status          # 取得機器人狀態
POST   /api/robot/move/j          # 關節運動
POST   /api/robot/move/l          # 直線運動
POST   /api/robot/move/arc        # 圓弧運動
POST   /api/robot/stop            # 停止運動
GET    /api/robot/position        # 取得目前位置
POST   /api/robot/speed           # 設定速度
```

## 開發規劃

- [x] Dobot API 封裝與範例
- [ ] Flask 後端伺服器開發
- [ ] RESTful API 設計與實作
- [ ] 前端應用開發
- [ ] 即時狀態監控
- [ ] 安全機制與錯誤處理
- [ ] 日誌記錄與除錯工具

## 注意事項

1. **安全第一**: 執行程式前確保機械臂處於安全位置，防止碰撞
2. **網路配置**: 確保裝置在同一區域網路內 (192.168.1.x)
3. **機器人模式**: 使用前需在 DobotStudio Pro 中將機器人切換至 TCP/IP 模式
4. **控制器版本**: 需要 V1.5.6.0 及以上版本

## 技術堆疊

- **後端**: Python, Flask, Socket
- **前端**: (待定 - Web/Mobile/Desktop)
- **機器人**: Dobot MG400/M1Pro
- **通訊**: TCP/IP, REST API, JSON

## 參考文件

- [Dobot TCP/IP 控制協定文件](Dobot/DobotDocs/)
- [Dobot Python API README](Dobot/TCP-IP-4Axis-Python-main/README.md)
- [Dobot 官方 GitHub](https://github.com/Dobot-Arm/TCP-IP-4Axis-Python)

## 貢獻者

- 研究團隊成員

## 授權

本專案僅供研究和學習使用。
