"""
弹幕姬主程序
结合完整UI和简化版的弹幕消费逻辑
"""
import asyncio
import tkinter as tk
from tkinter import ttk
import sys
import os
from threading import Thread
from queue import Queue

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from danmaku.ui.danmaku_window import DanmakuWindow
from danmaku.core.statistics import StatisticsManager
from log.log import logger
from ws.ws import BiliStreamClient


class DanmakuApp:
    """弹幕姬应用主类"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.statistics = StatisticsManager()
        self.ui = DanmakuWindow(self.root, self, self.statistics)
        self.is_running = False
        self.bsclient = None
        self.loop = None
        self.thread = None
        self._connect_task = None
        self._consume_task = None
        
    def start(self):
        """启动弹幕姬"""
        logger.pr_info("弹幕姬启动中...")
        self.is_running = True
        
        # 启动异步线程
        self.loop = asyncio.new_event_loop()
        self.thread = Thread(target=self._run_async, daemon=True)
        self.thread.start()
        
        # 启动UI主循环
        self.ui.run()
        
    def _run_async(self):
        """运行异步循环"""
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_forever()
        except Exception as e:
            logger.pr_error(f"Async loop error: {e}")
            
    async def _connect_and_listen(self, room_id: int):
        """连接并监听弹幕"""
        self.bsclient = BiliStreamClient(room_id)
        
        # 获取房间信息
        await self.bsclient.fetch_room_id()
        if self.bsclient.room_id == 0 or self.bsclient.room_id == -1:
            self.ui.update_status("获取房间ID失败")
            self.ui._on_connect_failed("获取房间ID失败")
            logger.pr_error("Failed to fetch valid room_id")
            return
            
        self.ui.update_status(f"房间ID: {self.bsclient.room_id}")
        logger.pr_info(f"Room ID: {self.bsclient.room_id}")
        
        # 获取WebSocket信息
        await self.bsclient.access_bili_websocket_html()
        if not self.bsclient.token or not self.bsclient.hosts:
            self.ui.update_status("获取WebSocket信息失败")
            self.ui._on_connect_failed("获取WebSocket信息失败")
            logger.pr_error("Failed to access BiliBili WebSocket info")
            return
            
        self.ui.update_status("正在连接...")
        
        # 启动弹幕消费任务
        self._consume_task = asyncio.create_task(self._consume_danmaku())
        
        # 连接WebSocket
        try:
            # 显示正在连接的状态
            self.ui.update_status("正在连接...")
            
            # 创建连接任务（不等待完成）
            self._connect_task = asyncio.create_task(self.bsclient.connect_to_host())
            connect_task = self._connect_task
            
            # 短暂等待，确保连接开始
            await asyncio.sleep(0.5)
            
            # 检查连接是否还在进行中（说明连接成功了）
            if not connect_task.done():
                self.ui.update_status("连接成功！")
                self.ui._on_connect_success(room_id)
                # 在弹幕区显示连接成功消息（使用队列确保线程安全）
                self.ui.danmaku_queue.put(("系统", f"已成功连接到房间 {room_id}", "system"))
            else:
                # 连接已经结束，说明失败了
                try:
                    connect_task.result()
                except Exception as e:
                    self.ui.update_status(f"连接失败: {e}")
                    self.ui._on_connect_failed(str(e))
                    self.ui.danmaku_queue.put(("系统", f"连接失败: {e}", "system"))
                    logger.pr_error(f"Failed to connect to WebSocket: {e}")
                    
        except Exception as e:
            self.ui.update_status(f"连接失败: {e}")
            self.ui._on_connect_failed(str(e))
            self.ui.danmaku_queue.put(("系统", f"连接失败: {e}", "system"))
            logger.pr_error(f"Failed to connect to WebSocket: {e}")
            
    async def _consume_danmaku(self):
        """消费弹幕"""
        self.ui.update_status("已连接，正在接收弹幕...")
        
        try:
            while True:
                try:
                    # 从弹幕队列中获取弹幕
                    msg = await asyncio.wait_for(self.bsclient.recv_danmaku(), timeout=1.0)
                    
                    msg_type = msg.get('type', 'danmaku')
                    
                    # 处理心跳回复（在线人数/人气值）
                    if msg_type == 'heartbeat':
                        popularity = msg.get('popularity', 0)
                        self.statistics.update_online(self.bsclient.room_id, popularity)
                        continue
                    
                    # 获取弹幕信息
                    nickname = msg.get('nickname', 'Unknown')
                    text = msg.get('text', '')
                    uid = msg.get('uid', 0)
                    
                    if text:
                        # 添加到队列供UI消费（包含tag参数）
                        self.ui.danmaku_queue.put((nickname, text, ""))
                        logger.pr_info(f"弹幕: {nickname}: {text}")
                        
                        # 更新统计
                        self.statistics.record_danmaku(
                            self.bsclient.room_id, uid, nickname, text
                        )
                        
                except asyncio.TimeoutError:
                    # 超时，继续等待
                    continue
                except Exception as e:
                    logger.pr_error(f"Error consuming danmaku: {e}")
                    # 不要break，继续尝试消费下一条
                    continue
                    
        except asyncio.CancelledError:
            logger.pr_info("Danmaku consumer cancelled")
        except Exception as e:
            logger.pr_error(f"Danmaku consumer error: {e}")
            
    def connect_room(self, room_id: int):
        """连接房间"""
        if self.loop and self.is_running:
            asyncio.run_coroutine_threadsafe(
                self._connect_and_listen(room_id),
                self.loop
            )
            
    def disconnect_room(self):
        """断开连接"""
        if self.bsclient:
            asyncio.run_coroutine_threadsafe(
                self._do_disconnect(),
                self.loop
            )
            
    async def _do_disconnect(self):
        """执行断开连接的异步操作"""
        # 取消消费任务
        if self._consume_task and not self._consume_task.done():
            self._consume_task.cancel()
            self._consume_task = None
            
        # 关闭客户端（会设置_closed标志，使connect_to_host退出循环）
        if self.bsclient:
            await self.bsclient.close()
            
        # 取消连接任务
        if self._connect_task and not self._connect_task.done():
            self._connect_task.cancel()
            self._connect_task = None
            
        self.bsclient = None
        self.ui.update_status("已断开连接")
            
    def stop(self):
        """停止弹幕姬"""
        logger.pr_info("弹幕姬关闭中...")
        self.is_running = False
        if self.bsclient:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._do_disconnect(),
                    self.loop
                )
                future.result(timeout=3)  # 等待最多3秒
            except Exception:
                pass
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        

def main():
    """主入口"""
    try:
        app = DanmakuApp()
        app.start()
    except KeyboardInterrupt:
        logger.pr_info("收到中断信号，正在关闭...")
    except Exception as e:
        logger.pr_error(f"弹幕姬异常退出: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.pr_info("弹幕姬已关闭")


if __name__ == "__main__":
    main()
