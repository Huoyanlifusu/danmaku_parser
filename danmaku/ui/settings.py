"""
弹幕姬设置面板
"""
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
from typing import Callable, Optional


class SettingsPanel:
    """设置面板基类"""
    
    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.settings = {}
        
    def create_entry(self, label: str, key: str, default: str = "", width: int = 30):
        """创建输入框设置项"""
        frame = tk.Frame(self.parent)
        frame.pack(fill=tk.X, pady=2)
        
        tk.Label(frame, text=label, width=15, anchor=tk.W).pack(side=tk.LEFT)
        entry = tk.Entry(frame, width=width)
        entry.pack(side=tk.LEFT, padx=5)
        entry.insert(0, default)
        
        self.settings[key] = entry
        return entry
        
    def create_checkbox(self, label: str, key: str, default: bool = True):
        """创建复选框设置项"""
        var = tk.BooleanVar(value=default)
        tk.Checkbutton(
            self.parent,
            text=label,
            variable=var,
            command=lambda: self._on_setting_change(key, var.get())
        ).pack(anchor=tk.W, padx=10, pady=2)
        
        self.settings[key] = var
        return var
        
    def create_slider(self, label: str, key: str, from_: float, to: float, default: float, resolution: float = 0.1):
        """创建滑块设置项"""
        frame = tk.Frame(self.parent)
        frame.pack(fill=tk.X, pady=2)
        
        var = tk.DoubleVar(value=default)
        
        tk.Label(frame, text=label, width=15, anchor=tk.W).pack(side=tk.LEFT)
        
        scale = ttk.Scale(
            frame,
            from_=from_,
            to=to,
            orient=tk.HORIZONTAL,
            variable=var,
            command=lambda v: self._on_setting_change(key, float(v))
        )
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        value_label = tk.Label(frame, text=str(default), width=10)
        value_label.pack(side=tk.LEFT)
        
        self.settings[key] = var
        return var
        
    def _on_setting_change(self, key: str, value):
        """设置项改变时的回调"""
        pass
        
    def get_setting(self, key: str, default=None):
        """获取设置值"""
        return self.settings.get(key, default)
        
    def set_setting(self, key: str, value):
        """设置值"""
        if key in self.settings:
            setting = self.settings[key]
            if isinstance(setting, (tk.BooleanVar, tk.IntVar, tk.DoubleVar, tk.StringVar)):
                setting.set(value)
            elif isinstance(setting, tk.Entry):
                setting.delete(0, tk.END)
                setting.insert(0, value)


class FilterSettings(SettingsPanel):
    """弹幕过滤设置"""
    
    def __init__(self, parent: tk.Widget, event_handler):
        super().__init__(parent)
        self.event_handler = event_handler
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI"""
        # 标题
        title = tk.Label(
            self.parent,
            text="弹幕过滤设置",
            font=("Microsoft YaHei", 12, "bold")
        )
        title.pack(pady=10)
        
        # 屏蔽关键词
        block_frame = tk.LabelFrame(self.parent, text="屏蔽关键词")
        block_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.blocked_listbox = tk.Listbox(block_frame, height=10)
        self.blocked_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加关键词
        add_frame = tk.Frame(block_frame)
        add_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.keyword_entry = tk.Entry(add_frame)
        self.keyword_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        tk.Button(
            add_frame,
            text="添加",
            command=self._add_blocked_keyword
        ).pack(side=tk.LEFT)
        
        tk.Button(
            block_frame,
            text="移除选中",
            command=self._remove_blocked_keyword
        ).pack(pady=5)
        
        # 过滤选项
        options_frame = tk.LabelFrame(self.parent, text="过滤选项")
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.block_short = tk.BooleanVar(value=False)
        tk.Checkbutton(
            options_frame,
            text="屏蔽短弹幕（少于4字）",
            variable=self.block_short
        ).pack(anchor=tk.W, padx=10, pady=2)
        
        self.block_duplicates = tk.BooleanVar(value=False)
        tk.Checkbutton(
            options_frame,
            text="屏蔽重复弹幕",
            variable=self.block_duplicates
        ).pack(anchor=tk.W, padx=10, pady=2)
        
    def _add_blocked_keyword(self):
        """添加屏蔽关键词"""
        keyword = self.keyword_entry.get().strip()
        if keyword:
            self.event_handler.add_blocked_keyword(keyword)
            self.blocked_listbox.insert(tk.END, keyword)
            self.keyword_entry.delete(0, tk.END)
            
    def _remove_blocked_keyword(self):
        """移除屏蔽关键词"""
        selection = self.blocked_listbox.curselection()
        if selection:
            keyword = self.blocked_listbox.get(selection[0])
            self.event_handler.remove_blocked_keyword(keyword)
            self.blocked_listbox.delete(selection[0])


class HighlightSettings(SettingsPanel):
    """高亮关键词设置"""
    
    def __init__(self, parent: tk.Widget, event_handler):
        super().__init__(parent)
        self.event_handler = event_handler
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI"""
        # 标题
        title = tk.Label(
            self.parent,
            text="关键词高亮设置",
            font=("Microsoft YaHei", 12, "bold")
        )
        title.pack(pady=10)
        
        # 高亮关键词列表
        list_frame = tk.LabelFrame(self.parent, text="高亮关键词")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 表头
        header_frame = tk.Frame(list_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(header_frame, text="关键词", width=20).pack(side=tk.LEFT)
        tk.Label(header_frame, text="颜色", width=15).pack(side=tk.LEFT)
        
        # 列表
        self.highlight_listbox = tk.Listbox(list_frame, height=10)
        self.highlight_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加高亮
        add_frame = tk.Frame(list_frame)
        add_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.keyword_entry = tk.Entry(add_frame, width=20)
        self.keyword_entry.pack(side=tk.LEFT, padx=5)
        
        # 颜色选择
        self.color_var = tk.StringVar(value="#ff0000")
        color_btn = tk.Button(
            add_frame,
            text="选择颜色",
            command=self._choose_color
        )
        color_btn.pack(side=tk.LEFT, padx=5)
        
        self.color_preview = tk.Label(
            add_frame,
            text="    ",
            bg=self.color_var.get(),
            width=5
        )
        self.color_preview.pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            add_frame,
            text="添加",
            command=self._add_highlight
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            list_frame,
            text="移除选中",
            command=self._remove_highlight
        ).pack(pady=5)
        
    def _choose_color(self):
        """选择颜色"""
        color = colorchooser.askcolor(title="选择高亮颜色", initialcolor=self.color_var.get())
        if color[1]:
            self.color_var.set(color[1])
            self.color_preview.config(bg=color[1])
            
    def _add_highlight(self):
        """添加高亮关键词"""
        keyword = self.keyword_entry.get().strip()
        if keyword:
            color = self.color_var.get()
            self.event_handler.add_highlight_keyword(keyword, color)
            self.highlight_listbox.insert(tk.END, f"{keyword} ({color})")
            self.keyword_entry.delete(0, tk.END)
            
    def _remove_highlight(self):
        """移除高亮关键词"""
        selection = self.highlight_listbox.curselection()
        if selection:
            item = self.highlight_listbox.get(selection[0])
            keyword = item.split(" (")[0]
            # 从event_handler中移除
            self.highlight_listbox.delete(selection[0])


class AppearanceSettings(SettingsPanel):
    """外观设置"""
    
    def __init__(self, parent: tk.Widget, window):
        super().__init__(parent)
        self.window = window
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI"""
        # 标题
        title = tk.Label(
            self.parent,
            text="外观设置",
            font=("Microsoft YaHei", 12, "bold")
        )
        title.pack(pady=10)
        
        # 颜色设置
        colors_frame = tk.LabelFrame(self.parent, text="颜色设置")
        colors_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 背景色
        bg_frame = tk.Frame(colors_frame)
        bg_frame.pack(fill=tk.X, pady=5, padx=10)
        
        tk.Label(bg_frame, text="背景色:", width=10).pack(side=tk.LEFT)
        
        self.bg_color_btn = tk.Button(
            bg_frame,
            text="选择",
            command=lambda: self._choose_color("bg")
        )
        self.bg_color_btn.pack(side=tk.LEFT, padx=5)
        
        self.bg_color_label = tk.Label(bg_frame, text=self.window.bg_color, width=15)
        self.bg_color_label.pack(side=tk.LEFT)
        
        # 文字色
        text_frame = tk.Frame(colors_frame)
        text_frame.pack(fill=tk.X, pady=5, padx=10)
        
        tk.Label(text_frame, text="文字色:", width=10).pack(side=tk.LEFT)
        
        self.text_color_btn = tk.Button(
            text_frame,
            text="选择",
            command=lambda: self._choose_color("text")
        )
        self.text_color_btn.pack(side=tk.LEFT, padx=5)
        
        self.text_color_label = tk.Label(text_frame, text=self.window.text_color, width=15)
        self.text_color_label.pack(side=tk.LEFT)
        
        # 透明度
        opacity_frame = tk.Frame(colors_frame)
        opacity_frame.pack(fill=tk.X, pady=5, padx=10)
        
        tk.Label(opacity_frame, text="透明度:", width=10).pack(side=tk.LEFT)
        
        self.opacity_scale = ttk.Scale(
            opacity_frame,
            from_=0.3,
            to=1.0,
            orient=tk.HORIZONTAL,
            command=self._on_opacity_change
        )
        self.opacity_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.opacity_label = tk.Label(opacity_frame, text="100%", width=10)
        self.opacity_label.pack(side=tk.LEFT)
        
        # 字体设置
        font_frame = tk.LabelFrame(self.parent, text="字体设置")
        font_frame.pack(fill=tk.X, padx=10, pady=5)
        
        font_label_frame = tk.Frame(font_frame)
        font_label_frame.pack(fill=tk.X, pady=5, padx=10)
        
        tk.Label(font_label_frame, text="弹幕字体:", width=10).pack(side=tk.LEFT)
        
        self.font_size_var = tk.IntVar(value=11)
        tk.Spinbox(
            font_label_frame,
            from_=8,
            to=24,
            textvariable=self.font_size_var,
            width=5,
            command=self._on_font_change
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Label(font_label_frame, text="号").pack(side=tk.LEFT)
        
        # 应用按钮
        tk.Button(
            self.parent,
            text="应用设置",
            command=self._apply_settings,
            bg="#4CAF50",
            fg="white",
            width=15
        ).pack(pady=10)
        
    def _choose_color(self, color_type: str):
        """选择颜色"""
        if color_type == "bg":
            current = self.window.bg_color
        else:
            current = self.window.text_color
            
        color = colorchooser.askcolor(title=f"选择{color_type}颜色", initialcolor=current)
        if color[1]:
            if color_type == "bg":
                self.window.bg_color = color[1]
                self.bg_color_label.config(text=color[1])
            else:
                self.window.text_color = color[1]
                self.text_color_label.config(text=color[1])
                
    def _on_opacity_change(self, value):
        """透明度改变"""
        opacity = float(value)
        self.window.root.wm_attributes('-alpha', opacity)
        self.opacity_label.config(text=f"{int(opacity * 100)}%")
        
    def _on_font_change(self):
        """字体大小改变"""
        size = self.font_size_var.get()
        self.window.danmaku_text.config(font=("Consolas", size))
        
    def _apply_settings(self):
        """应用设置"""
        messagebox.showinfo("提示", "设置已应用！")


class SettingsDialog:
    """设置对话框"""
    
    def __init__(self, parent: tk.Tk, event_handler, window):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("设置")
        self.dialog.geometry("500x600")
        self.dialog.resizable(False, False)
        
        # 创建Notebook
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建各个设置页面
        self.filter_page = tk.Frame(self.notebook)
        self.notebook.add(self.filter_page, text="弹幕过滤")
        
        self.highlight_page = tk.Frame(self.notebook)
        self.notebook.add(self.highlight_page, text="关键词高亮")
        
        self.appearance_page = tk.Frame(self.notebook)
        self.notebook.add(self.appearance_page, text="外观设置")
        
        # 初始化各个设置面板
        FilterSettings(self.filter_page, event_handler)
        HighlightSettings(self.highlight_page, event_handler)
        AppearanceSettings(self.appearance_page, window)
        
        # 关闭按钮
        tk.Button(
            self.dialog,
            text="关闭",
            command=self.dialog.destroy,
            width=15
        ).pack(pady=10)


def show_settings(parent: tk.Tk, event_handler, window):
    """显示设置对话框"""
    SettingsDialog(parent, event_handler, window)
