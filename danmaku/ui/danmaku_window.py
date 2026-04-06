"""
弹幕姬主界面
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import queue
import threading
from datetime import datetime
from typing import Optional
import asyncio

from log.log import logger


class DanmakuWindow:
    """弹幕姬主窗口"""
    
    def __init__(self, root: tk.Tk, app, statistics):
        self.root = root
        self.app = app
        self.statistics = statistics
        
        self.root.title("B站弹幕姬 - Bilibili Danmaku")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # 消息队列
        self.danmaku_queue = queue.Queue()
        self.gift_queue = queue.Queue()
        self.system_queue = queue.Queue()
        
        # 配置变量
        self.show_gifts = tk.BooleanVar(value=True)
        self.show_guard = tk.BooleanVar(value=True)
        self.show_like = tk.BooleanVar(value=True)
        self.auto_scroll = tk.BooleanVar(value=True)
        self.danmaku_max_lines = 500
        
        # 样式配置
        self.bg_color = "#1a1a2e"
        self.text_bg = "#16213e"
        self.accent_color = "#e94560"
        self.text_color = "#eaeaea"
        self.gift_color = "#ffc107"
        self.guard_color = "#00d4ff"
        
        self._setup_ui()
        self._setup_menus()
        
        # 启动定时任务
        self._start_update_tasks()
        
    def _setup_ui(self):
        """设置UI界面"""
        # 主容器
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 顶部标题栏
        self._create_title_bar(main_container)
        
        # 左侧面板：控制区
        left_panel = tk.Frame(main_container, bg=self.bg_color, width=250)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_panel.pack_propagate(False)
        
        self._create_room_panel(left_panel)
        self._create_control_panel(left_panel)
        self._create_statistics_panel(left_panel)
        
        # 右侧主区域
        right_panel = tk.Frame(main_container, bg=self.bg_color)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self._create_danmaku_area(right_panel)
        self._create_gift_area(right_panel)
        
    def _create_title_bar(self, parent):
        """创建标题栏"""
        title_frame = tk.Frame(parent, bg=self.accent_color, height=50)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="🎮 B站弹幕姬 - Bilibili Danmaku",
            font=("Microsoft YaHei", 16, "bold"),
            bg=self.accent_color,
            fg="white"
        )
        title_label.pack(pady=10)
        
    def _create_room_panel(self, parent):
        """创建直播间面板"""
        frame = tk.LabelFrame(
            parent, 
            text="📺 直播间",
            bg=self.bg_color,
            fg=self.text_color,
            font=("Microsoft YaHei", 10, "bold")
        )
        frame.pack(fill=tk.X, pady=5)
        
        # 房间号输入
        tk.Label(frame, text="房间号:", bg=self.bg_color, fg=self.text_color).grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.room_id_entry = tk.Entry(frame, width=15)
        self.room_id_entry.grid(row=0, column=1, padx=5, pady=5)
        self.room_id_entry.insert(0, "22637261")  # 默认房间号
        
        # 按钮区域
        btn_frame = tk.Frame(frame, bg=self.bg_color)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        self.connect_btn = tk.Button(
            btn_frame, 
            text="连接",
            command=self._connect_room,
            bg="#4CAF50",
            fg="white",
            width=8
        )
        self.connect_btn.pack(side=tk.LEFT, padx=2)
        
        disconnect_btn = tk.Button(
            btn_frame,
            text="断开",
            command=self._disconnect_room,
            bg="#f44336",
            fg="white",
            width=8
        )
        disconnect_btn.pack(side=tk.LEFT, padx=2)
        
        # 房间信息显示
        self.room_info_label = tk.Label(
            frame,
            text="未连接",
            bg=self.bg_color,
            fg=self.text_color,
            font=("Consolas", 9),
            justify=tk.LEFT,
            anchor=tk.W
        )
        self.room_info_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
    def _create_control_panel(self, parent):
        """创建控制面板"""
        frame = tk.LabelFrame(
            parent,
            text="⚙️ 显示设置",
            bg=self.bg_color,
            fg=self.text_color,
            font=("Microsoft YaHei", 10, "bold")
        )
        frame.pack(fill=tk.X, pady=5)
        
        tk.Checkbutton(
            frame,
            text="显示礼物",
            variable=self.show_gifts,
            bg=self.bg_color,
            fg=self.text_color,
            selectcolor=self.bg_color,
            command=self._update_display
        ).pack(anchor=tk.W, padx=10, pady=2)
        
        tk.Checkbutton(
            frame,
            text="显示舰长",
            variable=self.show_guard,
            bg=self.bg_color,
            fg=self.text_color,
            selectcolor=self.bg_color,
            command=self._update_display
        ).pack(anchor=tk.W, padx=10, pady=2)
        
        tk.Checkbutton(
            frame,
            text="显示点赞",
            variable=self.show_like,
            bg=self.bg_color,
            fg=self.text_color,
            selectcolor=self.bg_color,
            command=self._update_display
        ).pack(anchor=tk.W, padx=10, pady=2)
        
        tk.Checkbutton(
            frame,
            text="自动滚动",
            variable=self.auto_scroll,
            bg=self.bg_color,
            fg=self.text_color,
            selectcolor=self.bg_color,
            command=self._update_display
        ).pack(anchor=tk.W, padx=10, pady=2)
        
        # 清空按钮
        tk.Button(
            frame,
            text="清空弹幕",
            command=self._clear_danmaku,
            bg="#666",
            fg="white",
            width=10
        ).pack(pady=5)
        
    def _create_statistics_panel(self, parent):
        """创建统计面板"""
        frame = tk.LabelFrame(
            parent,
            text="📊 统计数据",
            bg=self.bg_color,
            fg=self.text_color,
            font=("Microsoft YaHei", 10, "bold")
        )
        frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 统计数据标签
        self.stats_labels = {}
        stats_items = [
            ('弹幕数', 'danmaku_count'),
            ('礼物数', 'gift_count'),
            ('舰长数', 'guard_count'),
            ('在线人数', 'online'),
            ('峰值在线', 'peak_online'),
        ]
        
        for i, (label_text, key) in enumerate(stats_items):
            tk.Label(
                frame,
                text=f"{label_text}:",
                bg=self.bg_color,
                fg=self.text_color
            ).grid(row=i, column=0, sticky=tk.W, padx=10, pady=2)
            
            self.stats_labels[key] = tk.Label(
                frame,
                text="0",
                bg=self.bg_color,
                fg=self.gift_color,
                font=("Consolas", 10, "bold")
            )
            self.stats_labels[key].grid(row=i, column=1, sticky=tk.W, padx=10, pady=2)
            
    def _create_danmaku_area(self, parent):
        """创建弹幕显示区域"""
        frame = tk.Frame(parent, bg=self.text_bg)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_frame = tk.Frame(frame, bg=self.text_bg)
        title_frame.pack(fill=tk.X)
        
        tk.Label(
            title_frame,
            text="💬 弹幕区",
            bg=self.text_bg,
            fg=self.text_color,
            font=("Microsoft YaHei", 12, "bold")
        ).pack(side=tk.LEFT, padx=10, pady=5)
        
        # 弹幕文本区域
        self.danmaku_text = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg=self.text_bg,
            fg=self.text_color,
            insertbackground=self.text_color,
            relief=tk.FLAT,
            state=tk.DISABLED
        )
        self.danmaku_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 配置标签
        self.danmaku_text.tag_configure("gift", foreground=self.gift_color)
        self.danmaku_text.tag_configure("guard", foreground=self.guard_color)
        self.danmaku_text.tag_configure("system", foreground="#888")
        self.danmaku_text.tag_configure("highlight", foreground=self.accent_color)
        
    def _create_gift_area(self, parent):
        """创建礼物显示区域"""
        frame = tk.LabelFrame(
            parent,
            text="🎁 最近礼物",
            bg=self.bg_color,
            fg=self.gift_color,
            font=("Microsoft YaHei", 10, "bold")
        )
        frame.pack(fill=tk.X, pady=5)
        
        self.gift_text = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            height=8,
            font=("Microsoft YaHei", 9),
            bg=self.text_bg,
            fg=self.gift_color,
            relief=tk.FLAT,
            state=tk.DISABLED
        )
        self.gift_text.pack(fill=tk.X, padx=5, pady=5)
        
    def _setup_menus(self):
        """设置菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="清空记录", command=self._clear_all)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="弹幕过滤", command=self._show_filter_dialog)
        settings_menu.add_command(label="关键词高亮", command=self._show_highlight_dialog)
        settings_menu.add_separator()
        settings_menu.add_command(label="外观设置", command=self._show_appearance_dialog)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)
        
    def _connect_room(self):
        """连接直播间"""
        try:
            room_id_str = self.room_id_entry.get().strip()
            if not room_id_str:
                messagebox.showwarning("警告", "请输入房间号")
                return
                
            room_id = int(room_id_str)
            
            # 更新UI
            self.connect_btn.config(state=tk.DISABLED, text="连接中...")
            self.room_info_label.config(text=f"正在连接房间 {room_id}...")
            
            # 在新线程中执行连接
            threading.Thread(target=self._async_connect, args=(room_id,), daemon=True).start()
            
        except ValueError:
            messagebox.showerror("错误", "房间号格式错误")
            self.connect_btn.config(state=tk.NORMAL, text="连接")
            
    def _async_connect(self, room_id: int):
        """异步连接"""
        try:
            # 使用app的连接方法
            self.app.connect_room(room_id)
            
        except Exception as e:
            self.root.after(0, self._on_connect_failed, str(e))
            
    def update_status(self, text: str):
        """更新状态显示"""
        try:
            self.root.after(0, lambda: self.room_info_label.config(text=text))
        except:
            pass
            
    def _on_connect_success(self, room_id: int):
        """连接成功回调"""
        self.connect_btn.config(state=tk.NORMAL, text="已连接", bg="#888")
        self._add_system_message(f"成功连接到房间 {room_id}")
        logger.pr_info(f"Connected to room {room_id}")
        
    def _on_connect_failed(self, error: str):
        """连接失败回调"""
        self.connect_btn.config(state=tk.NORMAL, text="连接", bg="#4CAF50")
        self.room_info_label.config(text=f"连接失败: {error}")
        messagebox.showerror("连接失败", error)
        logger.pr_error(f"Failed to connect: {error}")
        
    def _disconnect_room(self):
        """断开连接"""
        try:
            self.app.disconnect_room()
            self.connect_btn.config(state=tk.NORMAL, text="连接", bg="#4CAF50")
            self.room_info_label.config(text="未连接")
            self._add_system_message("已断开连接")
            
            # 清理统计数据
            self.statistics.clear()
            self._update_statistics()
            
            # 清空弹幕和礼物显示区
            self._clear_danmaku()
            self.gift_text.config(state=tk.NORMAL)
            self.gift_text.delete('1.0', tk.END)
            self.gift_text.config(state=tk.DISABLED)
            
            # 清空消息队列
            while not self.danmaku_queue.empty():
                try:
                    self.danmaku_queue.get_nowait()
                except queue.Empty:
                    break
            while not self.gift_queue.empty():
                try:
                    self.gift_queue.get_nowait()
                except queue.Empty:
                    break
        except Exception as e:
            messagebox.showwarning("警告", f"断开连接失败: {e}")
            
    def _add_danmaku(self, nickname: str, text: str, tag: str = ""):
        """添加弹幕到显示区域"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            message = f"[{timestamp}] {nickname}: {text}\n"
            
            self.danmaku_text.config(state=tk.NORMAL)
            self.danmaku_text.insert(tk.END, message, tag)
            
            # 限制行数
            if self.auto_scroll.get():
                self.danmaku_text.see(tk.END)
                
            # 检查行数
            line_count = int(self.danmaku_text.index('end-1c').split('.')[0])
            if line_count > self.danmaku_max_lines:
                self.danmaku_text.delete('1.0', '2.0')
                
            self.danmaku_text.config(state=tk.DISABLED)
            
        except Exception as e:
            logger.pr_error(f"Error adding danmaku: {e}")
            
    def _add_gift(self, nickname: str, gift_name: str, gift_count: int):
        """添加礼物到显示区域"""
        try:
            if not self.show_gifts.get():
                return
                
            timestamp = datetime.now().strftime("%H:%M:%S")
            message = f"[{timestamp}] {nickname} 送出 {gift_count}x {gift_name}\n"
            
            self.gift_text.config(state=tk.NORMAL)
            self.gift_text.insert(tk.END, message, "gift")
            self.gift_text.see(tk.END)
            self.gift_text.config(state=tk.DISABLED)
            
        except Exception as e:
            logger.pr_error(f"Error adding gift: {e}")
            
    def _add_system_message(self, message: str):
        """添加系统消息"""
        self._add_danmaku("系统", message, "system")
        
    def _on_danmaku(self, msg: dict):
        """弹幕消息回调"""
        try:
            nickname = msg.get('nickname', 'Unknown')
            text = msg.get('text', '')
            
            # 根据高亮设置标签
            tag = ""
            if msg.get('highlight'):
                tag = "highlight"
                
            # 添加到队列（线程安全）
            self.danmaku_queue.put((nickname, text, tag))
            
        except Exception as e:
            logger.pr_error(f"Error in danmaku callback: {e}")
            
    def _on_gift(self, msg: dict):
        """礼物消息回调"""
        try:
            nickname = msg.get('nickname', 'Unknown')
            gift_name = msg.get('gift_name', '')
            gift_count = msg.get('gift_count', 1)
            
            self.gift_queue.put((nickname, gift_name, gift_count))
            
        except Exception as e:
            logger.pr_error(f"Error in gift callback: {e}")
            
    def _on_guard(self, msg: dict):
        """舰长消息回调"""
        try:
            nickname = msg.get('nickname', 'Unknown')
            guard_type = msg.get('guard_type', 3)
            
            guard_names = {1: '总督', 2: '提督', 3: '舰长'}
            guard_name = guard_names.get(guard_type, '舰长')
            
            self.danmaku_queue.put((nickname, f"开通了{guard_name}", "guard"))
            
        except Exception as e:
            logger.pr_error(f"Error in guard callback: {e}")
            
    def _poll_queues(self):
        """轮询消息队列"""
        try:
            # 处理弹幕队列
            while True:
                try:
                    nickname, text, tag = self.danmaku_queue.get_nowait()
                    self._add_danmaku(nickname, text, tag)
                except queue.Empty:
                    break
                    
            # 处理礼物队列
            while True:
                try:
                    nickname, gift_name, gift_count = self.gift_queue.get_nowait()
                    self._add_gift(nickname, gift_name, gift_count)
                except queue.Empty:
                    break
                    
        except Exception as e:
            logger.pr_error(f"Error polling queues: {e}")
            
        # 更新统计
        self._update_statistics()
        
        # 继续轮询
        self.root.after(100, self._poll_queues)
        
    def _update_statistics(self):
        """更新统计数据"""
        try:
            summary = self.statistics.get_global_summary()
            
            self.stats_labels['danmaku_count'].config(text=str(summary['total_danmaku']))
            self.stats_labels['gift_count'].config(text=str(summary['total_gift']))
            self.stats_labels['guard_count'].config(text=str(summary['total_guard']))
            self.stats_labels['online'].config(text=str(summary['current_online']))
            self.stats_labels['peak_online'].config(text=str(summary['peak_online']))
            
        except Exception as e:
            logger.pr_error(f"Error updating statistics: {e}")
            
    def _update_display(self):
        """更新显示设置"""
        # 这里可以实现动态更新显示的逻辑
        pass
        
    def _clear_danmaku(self):
        """清空弹幕"""
        self.danmaku_text.config(state=tk.NORMAL)
        self.danmaku_text.delete('1.0', tk.END)
        self.danmaku_text.config(state=tk.DISABLED)
        
    def _clear_all(self):
        """清空所有"""
        if messagebox.askyesno("确认", "确定要清空所有记录吗？"):
            self._clear_danmaku()
            self.gift_text.config(state=tk.NORMAL)
            self.gift_text.delete('1.0', tk.END)
            self.gift_text.config(state=tk.DISABLED)
            self.statistics.clear()
            
    def _start_update_tasks(self):
        """启动定时更新任务"""
        self.root.after(100, self._poll_queues)
        
    def _show_filter_dialog(self):
        """显示过滤设置对话框"""
        from danmaku.ui.settings import show_settings
        show_settings(self.root, None, self)
        
    def _show_highlight_dialog(self):
        """显示高亮设置对话框"""
        from danmaku.ui.settings import show_settings
        show_settings(self.root, None, self)
        
    def _show_appearance_dialog(self):
        """显示外观设置对话框"""
        from danmaku.ui.settings import show_settings
        show_settings(self.root, None, self)
        
    def _show_help(self):
        """显示帮助"""
        help_text = """
B站弹幕姬使用说明

1. 输入直播间号，点击"连接"开始接收弹幕
2. 在设置中可以调整显示选项
3. 支持礼物、舰长等特殊消息显示
4. 统计数据会实时更新

房间号获取方式：
- 直播间URL中的数字ID
- 例如：https://live.bilibili.com/22637261
- 房间号为：22637261
        """
        messagebox.showinfo("使用说明", help_text)
        
    def _show_about(self):
        """显示关于"""
        about_text = """
B站弹幕姬 v1.0

基于WebSocket协议实时接收B站直播间弹幕

功能特点：
- 实时弹幕接收
- 礼物、舰长提示
- 弹幕统计分析
- 关键词过滤与高亮

作者：Zhang Yuyang
邮箱：zhangyuyang821@163.com
        """
        messagebox.showinfo("关于", about_text)
        
    def run(self):
        """运行主循环"""
        self.root.mainloop()
