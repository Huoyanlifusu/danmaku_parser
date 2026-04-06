# B站弹幕姬 - Bilibili Danmaku

基于WebSocket通信，实时接收B站直播间弹幕的桌面应用。

## 功能特点

🎮 **核心功能**
- 实时弹幕接收与显示
- 礼物、舰长等特殊消息提示
- 弹幕统计分析（弹幕数、礼物数、舰长数等）
- 多直播间管理

⚙️ **显示设置**
- 关键词过滤与屏蔽
- 关键词高亮显示
- 礼物显示开关
- 舰长提示开关
- 点赞显示开关
- 自动滚动功能

🎨 **外观定制**
- 深色主题界面
- 透明度调节
- 背景色、文字色自定义
- 字体大小调整

📊 **数据统计**
- 实时弹幕数量统计
- 礼物统计
- 舰长统计
- 在线人数统计
- 热门关键词分析
- Top用户排行

## 安装

### 方式一：使用pip安装

```bash
pip install .
```

### 方式二：直接运行

```bash
python run_danmaku.py
```

## 使用方法

### 1. 启动弹幕姬

```bash
python run_danmaku.py
```

或

```bash
python -m danmaku.app
```

### 2. 连接直播间

1. 在房间号输入框中输入B站直播间号
2. 点击"连接"按钮
3. 等待连接成功后即可开始接收弹幕

### 3. 获取房间号

- 直播间URL中的数字ID
- 例如：`https://live.bilibili.com/22637261`
- 房间号为：`22637261`

## 目录结构

```
bili_capcmdtokb/
├── danmaku/                 # 弹幕姬主程序
│   ├── app.py              # 主程序入口
│   ├── core/               # 核心模块
│   │   ├── room_manager.py    # 直播间管理
│   │   ├── statistics.py     # 统计数据管理
│   │   └── event_handler.py  # 事件处理
│   └── ui/                 # UI界面
│       ├── danmaku_window.py   # 主窗口
│       └── settings.py        # 设置面板
├── ws/                    # WebSocket通信模块
│   ├── ws.py              # B站WebSocket客户端
│   ├── command.py         # 命令处理
│   ├── danmaku_parser.py  # 弹幕解析
│   ├── proto.py           # 协议处理
│   ├── key.py             # WBI密钥
│   └── util.py            # 工具函数
├── https/                 # HTTPS通信模块
│   ├── https.py           # HTTP请求
│   └── node.py            # 节点处理
├── log/                   # 日志模块
│   └── log.py             # 日志工具
├── demo/                  # 示例程序
│   ├── demo1.py          # 弹幕键盘控制示例
│   └── demo2.py          # 简易弹幕姬示例
└── run_danmaku.py        # 启动器
```

## 开发相关

### 项目依赖

- Python 3.9+
- aiohttp >= 3.13.3
- Brotli >= 1.2.0
- yarl >= 1.22.0
- keyboard >= 0.13.5
- requests >= 2.32.5

### 开发指南

1. **直播间管理** (`danmaku/core/room_manager.py`)
   - 支持多房间连接
   - 自动重连机制
   - 事件回调系统

2. **事件处理** (`danmaku/core/event_handler.py`)
   - 弹幕过滤
   - 礼物处理
   - 舰长处理
   - 关键词高亮

3. **统计系统** (`danmaku/core/statistics.py`)
   - 实时统计
   - 历史记录
   - Top榜单

## 示例程序

### demo1 - 弹幕键盘控制

通过发送特定弹幕控制电脑键盘，例如发送 "111" 按下E键。

### demo2 - 简易弹幕姬

基础的弹幕显示界面，包含背景色和透明度调整功能。

### danmaku - 完整弹幕姬

功能完整的弹幕姬应用，包含所有高级功能。

## 注意事项

⚠️ **免责声明**
- 本项目仅供学习交流使用
- 请勿用于任何商业用途
- 使用本项目造成的一切后果由使用者自行承担

## 参考项目

- [blivedm](https://github.com/xfgryujk/blivedm) - B站直播弹幕Python库
- [bilibili-api](https://github.com/nemo2011/bilibili-api) - B站API调用库

## 作者

Zhang Yuyang
邮箱：zhangyuyang821@163.com

## License

MIT License

## 更新日志

### v1.0.0 (2026-04-06)
- 全新重构的弹幕姬应用
- 支持实时弹幕接收
- 完整的UI界面
- 礼物、舰长提示
- 弹幕统计功能
- 关键词过滤与高亮
- 外观自定义设置
