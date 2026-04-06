# B站弹幕姬使用说明

## 快速开始

### 1. 安装依赖

确保已安装所有必要的依赖包：

```bash
pip install aiohttp Brotli yarl keyboard requests
```

### 2. 运行弹幕姬

有多种方式启动弹幕姬：

**方式一：直接运行**
```bash
cd bili_capcmdtokb
python run_danmaku.py
```

**方式二：使用模块运行**
```bash
cd bili_capcmdtokb
python -m danmaku.app
```

**方式三：测试模式**
```bash
cd bili_capcmdtokb
python test_danmaku.py
```

### 3. 测试所有功能

运行测试脚本验证所有模块功能：

```bash
python test_danmaku.py
```

## 功能使用

### 连接直播间

1. 启动弹幕姬后，会看到主界面
2. 在左侧"直播间"面板的"房间号"输入框中输入B站直播间号
3. 点击"连接"按钮
4. 等待连接成功后，弹幕会实时显示在右侧弹幕区域

**获取房间号方法：**
- 直播间URL中的数字ID
- 例如：`https://live.bilibili.com/22637261`
- 房间号为：`22637261`

### 显示设置

在左侧"显示设置"面板中，可以控制：

- ☑️ 显示礼物 - 是否显示礼物消息
- ☑️ 显示舰长 - 是否显示舰长开通消息
- ☑️ 显示点赞 - 是否显示点赞消息
- ☑️ 自动滚动 - 弹幕是否自动滚动到最新

### 统计数据

实时显示以下统计数据：

- 📝 弹幕数 - 当前会话接收的弹幕总数
- 🎁 礼物数 - 收到的礼物总数
- 🚀 舰长数 - 开通的舰长总数
- 👥 在线人数 - 当前在线人数
- 📈 峰值在线 - 历史最高在线人数

### 设置功能

点击菜单栏"设置"可以打开设置对话框：

#### 弹幕过滤

- 添加/移除屏蔽关键词
- 屏蔽短弹幕（少于4字）
- 屏蔽重复弹幕

#### 关键词高亮

- 添加/移除高亮关键词
- 为不同关键词设置不同颜色

#### 外观设置

- 修改背景色和文字色
- 调整窗口透明度
- 修改弹幕字体大小

### 菜单功能

- **文件** → 清空记录：清空所有弹幕和统计数据
- **文件** → 退出：关闭弹幕姬
- **设置** → 弹幕过滤：打开过滤设置
- **设置** → 关键词高亮：打开高亮设置
- **设置** → 外观设置：打开外观设置
- **帮助** → 使用说明：查看使用帮助
- **帮助** → 关于：查看版本信息

## 高级功能

### 事件回调系统

弹幕姬使用事件回调系统处理各种消息：

```python
from danmaku.core.event_handler import EventHandler, DanmakuFilter

# 创建处理器
handler = EventHandler(room_manager, statistics)

# 添加自定义弹幕过滤器
handler.add_danmaku_filter(DanmakuFilter.keyword_filter(["敏感词"]))

# 添加高亮关键词
handler.add_highlight_keyword("重要消息", "red")
```

### 统计系统

```python
from danmaku.core.statistics import StatisticsManager

# 创建统计管理器
stats = StatisticsManager()

# 记录弹幕
stats.record_danmaku(room_id, uid, nickname, text)

# 获取统计摘要
summary = stats.get_global_summary()
print(f"弹幕数: {summary['total_danmaku']}")
```

### 直播间管理

```python
from danmaku.core.room_manager import RoomManager

# 创建房间管理器
manager = RoomManager()

# 添加并连接房间
await manager.add_room(22637261)
await manager.connect_room(22637261)

# 注册事件回调
manager.register_callback('danmaku', your_callback_function)
```

## 项目结构

```
bili_capcmdtokb/
├── danmaku/                 # 弹幕姬主程序 (AI generated)
│   ├── __init__.py
│   ├── app.py              # 主程序入口
│   ├── core/               # 核心模块
│   │   ├── __init__.py
│   │   ├── room_manager.py    # 直播间管理
│   │   ├── statistics.py       # 统计数据管理
│   │   └── event_handler.py    # 事件处理
│   └── ui/                 # UI界面
│       ├── __init__.py
│       ├── danmaku_window.py   # 主窗口
│       └── settings.py         # 设置面板
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
├── demo1.py              # 弹幕键盘控制示例
├── run_danmaku.py        # 启动器 (AI generated)
├── test_danmaku.py       # 测试脚本 (AI generated)
└── Readme.md             # 项目说明 (AI generated)
```

## 常见问题

### Q: 连接失败怎么办？

A: 检查以下几点：
1. 网络连接是否正常
2. 房间号是否正确
3. 直播间是否在直播中
4. 查看日志文件 `bili_capcmdtokb_info.log` 获取详细错误信息

### Q: 如何查看日志？

A: 日志文件位于项目根目录：
```
bili_capcmdtokb/bili_capcmdtokb_info.log
```

### Q: 如何修改默认房间号？

A: 编辑 `danmaku/ui/danmaku_window.py`，找到：
```python
self.room_id_entry.insert(0, "22637261")  # 默认房间号
```
将 `22637261` 改为你想要的房间号。

### Q: 弹幕显示不完整？

A: 可能是弹幕解析的问题，弹幕姬会自动限制显示的弹幕数量（默认500行），旧弹幕会自动清除。可以在设置中调整。

## 开发者指南

### 添加新的事件类型

在 `event_handler.py` 中添加新的处理方法：

```python
def handle_custom_event(self, msg: Dict[str, Any]) -> bool:
    """处理自定义事件"""
    # 处理逻辑
    return True
```

然后在 `handle_message` 中添加：

```python
elif cmd == 'CUSTOM_EVENT':
    self.handle_custom_event(msg)
```

### 添加新的统计项

在 `statistics.py` 中的 `StatisticsManager` 类添加新方法：

```python
def record_custom_stat(self, value):
    """记录自定义统计"""
    with self._lock:
        self.custom_stats += value
```

## 技术支持

- 邮箱：zhangyuyang821@163.com
- GitHub Issues: https://github.com/Huoyanlifusu/bili_livestream_danmaku_parser/issues

## 更新日志

### v0.5.0 (2026-04-06)
- ✨ 全新重构的弹幕姬应用
- 🎮 支持实时弹幕接收
- 🎨 完整的UI界面
- 🎁 礼物、舰长提示
- 📊 弹幕统计功能
- 🔍 关键词过滤与高亮
- 🎨 外观自定义设置
