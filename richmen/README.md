# 🎲 大富翁 (RichMen) — 网络多人联机版

一款基于 Python 的联网多人大富翁游戏，支持 2–8 人在局域网或公网中实时对战。

## 功能特性

- **完整大富翁规则** — 40 格经典棋盘，8 色地产组（棕、浅蓝、粉、橙、红、黄、绿、深蓝）
- **房屋 & 酒店** — 同色组全资后方可建房，最多 4 栋房屋升级为酒店
- **机会 & 公益金** — 32 张卡片，包含进监狱、出狱卡、收钱、赔钱等事件
- **拍卖系统** — 放弃购买地块时自动进入公开拍卖
- **监狱系统** — 掷出双数出狱 / 缴纳 $50 保释金 / 使用出狱卡
- **抵押系统** — 可抵押地产换取资金，赎回需支付本金额
- **联网对战** — 基于 Python asyncio 的异步 TCP 服务器，支持 Windows / macOS / Linux
- **中文界面** — 完整中文翻译的 Pygame 图形界面

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务器（任选一台机器）

```bash
python run_server.py 0.0.0.0 8765
```

默认监听 `0.0.0.0:8765`，可指定 IP 和端口。

### 3. 启动客户端（每人运行一个窗口）

```bash
python run_client.py <服务器IP> 8765 <你的名字>
```

示例：

```bash
python run_client.py 192.168.1.100 8765 小明
```

## 游戏操作

| 按键 | 功能 |
|------|------|
| `D` | 掷骰子 |
| `E` | 结束回合 |
| `B` | 购买地产（提示时） |
| `N` | 跳过/不购买 |
| `Enter` | 打开聊天输入框 |
| `Esc` | 关闭聊天 / 关闭卡片弹窗 |

## 技术栈

- **Python 3.10+**
- **Pygame** — 图形界面渲染
- **asyncio** — 异步网络通信
- **TCP + JSON** — 自定义文本协议

## 项目结构

```
richmen/
├── common/             # 公共模块
│   ├── constants.py    # 棋盘布局、卡片定义、价格数据
│   └── protocol.py     # 网络消息类型与编解码
├── server/             # 服务器端
│   ├── board.py        # 棋盘状态管理
│   ├── player.py       # 玩家数据结构
│   ├── game_logic.py   # 核心游戏引擎（规则、移动、租金、建造等）
│   └── game_server.py  # 异步网络服务器（连接管理、消息分发）
├── client/             # 客户端
│   ├── game_client.py  # 网络客户端层
│   └── gui.py          # Pygame 图形界面（棋盘渲染、交互、聊天）
├── run_server.py       # 服务器入口
├── run_client.py       # 客户端入口
├── requirements.txt    # Python 依赖
└── README.md           # 本文件
```

## 自定义

可修改 `common/constants.py` 中的以下参数：

- `START_MONEY` — 初始资金（默认 $1500）
- `PASS_GO_MONEY` — 经过 GO 的奖励（默认 $200）
- `JAIL_FINE` — 保释金（默认 $50）
- `MAX_PLAYERS` — 最大玩家数（默认 8）
- 棋盘数据 `BOARD_TILES` — 自定义地块名称、价格、租金

## License

MIT
