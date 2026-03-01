import tkinter as tk
from tkinter import colorchooser
import asyncio
from threading import Thread
import queue
from log.log import logger
from ws.ws import BiliStreamClient

class DanmakuUI:
    def __init__(self, root):
        self.root = root
        self.root.title("弹幕姬")
        self.root.geometry("400x800")  # 竖长条形状
        self.bg_color = "#222"
        self.opacity = 0.95
        self.root.configure(bg=self.bg_color)
        self.root.wm_attributes('-alpha', self.opacity)

        self.text = tk.Text(root, height=40, width=30, bg=self.bg_color, fg="#fff", font=("Consolas", 13), borderwidth=0)
        self.text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.text.config(state=tk.DISABLED)

        self.btn_frame = tk.Frame(root, bg=self.bg_color)
        self.btn_frame.pack(fill=tk.X, padx=10, pady=5)
        self.bg_btn = tk.Button(self.btn_frame, text="背景色", command=self.change_bg,
                               bg="#fff", fg="#222", width=8, height=1, font=("Consolas", 11, "bold"))
        self.bg_btn.pack(side=tk.LEFT, padx=5)
        self.opacity_btn = tk.Button(self.btn_frame, text="透明度", command=self.change_opacity,
                                    bg="#fff", fg="#222", width=8, height=1, font=("Consolas", 11, "bold"))
        self.opacity_btn.pack(side=tk.LEFT, padx=5)
        self.danmaku_queue = queue.Queue()
        self.poll_danmaku()
        self.update_btn_bg()

    def update_btn_bg(self):
        self.btn_frame.config(bg=self.bg_color)
        self.bg_btn.config(bg="#fff", fg="#222", activebackground="#eee", activeforeground="#222")
        self.opacity_btn.config(bg="#fff", fg="#222", activebackground="#eee", activeforeground="#222")

    def change_bg(self):
        color = colorchooser.askcolor(title="选择背景色", initialcolor=self.bg_color)[1]
        if color:
            self.bg_color = color
            self.root.configure(bg=color)
            self.text.config(bg=color)
            self.update_btn_bg()

    def change_opacity(self):
        top = tk.Toplevel(self.root)
        top.title("调整透明度")
        top.geometry("250x80")
        tk.Label(top, text="透明度 (0.3~1.0)").pack(pady=5)
        scale = tk.Scale(top, from_=0.3, to=1.0, resolution=0.01, orient=tk.HORIZONTAL)
        scale.set(self.opacity)
        scale.pack(pady=5)
        def set_opacity():
            self.opacity = scale.get()
            self.root.wm_attributes('-alpha', self.opacity)
            top.destroy()
        tk.Button(top, text="确定", command=set_opacity).pack(pady=5)

    def add_danmaku(self, userid, text):
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, f"{userid}: {text}\n")
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

    def poll_danmaku(self):
        try:
            while True:
                userid, text = self.danmaku_queue.get_nowait()
                self.add_danmaku(userid, text)
        except queue.Empty:
            pass
        self.root.after(100, self.poll_danmaku)

async def danmaku_loop(ui: DanmakuUI, bsclient: BiliStreamClient):
    while True:
        msg = await bsclient.recv_danmaku()
        userid = msg.get('uid', msg.get('userid', ''))
        text = msg.get('text', '')
        ui.add_danmaku(userid, text)

async def main(ui: DanmakuUI):
    bsclient = BiliStreamClient()
    await bsclient.fetch_room_id()
    await bsclient.access_bili_websocket_html()
    await bsclient.connect_to_host()
    await danmaku_loop(ui, bsclient)

def start_tk_loop():
    root = tk.Tk()
    ui = DanmakuUI(root)
    def run_asyncio():
        async def main_with_queue():
            bsclient = BiliStreamClient()
            await bsclient.fetch_room_id()
            await bsclient.access_bili_websocket_html()
            # 后台运行 connect_to_host
            asyncio.create_task(bsclient.connect_to_host())
            while True:
                msg = await bsclient.recv_danmaku()
                # print(msg)
                username = msg.get('nickname', "Unknown User")
                text = msg.get('text', 'No msg')
                ui.danmaku_queue.put((username, text))
        asyncio.run(main_with_queue())
    Thread(target=run_asyncio, daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    start_tk_loop()