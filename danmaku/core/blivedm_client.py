"""
基于blivedm的弹幕客户端
提供更可靠的弹幕接收功能
"""
import asyncio
import http.cookies
from typing import Optional
import aiohttp
import blivedm
import blivedm.models.web as web_models
from log.log import logger


class BlivedmClient:
    """基于blivedm的弹幕客户端"""
    
    def __init__(self, room_id: int, sessdata: str = ""):
        self.room_id = room_id
        self.sessdata = sessdata
        self.session: Optional[aiohttp.ClientSession] = None
        self.client: Optional[blivedm.BLiveClient] = None
        self.handler: Optional[DanmakuHandler] = None
        self._is_running = False
        
    def init_session(self):
        """初始化会话"""
        cookies = http.cookies.SimpleCookie()
        if self.sessdata:
            cookies['SESSDATA'] = self.sessdata
            cookies['SESSDATA']['domain'] = 'bilibili.com'
        
        self.session = aiohttp.ClientSession()
        if self.sessdata:
            self.session.cookie_jar.update_cookies(cookies)
            
    async def start(self, callbacks: dict):
        """启动客户端"""
        if not self.session:
            self.init_session()
            
        self.client = blivedm.BLiveClient(self.room_id, session=self.session)
        self.handler = DanmakuHandler(callbacks)
        self.client.set_handler(self.handler)
        
        self._is_running = True
        self.client.start()
        
        logger.pr_info(f"Blivedm client started for room {self.room_id}")
        
    async def run(self):
        """运行客户端"""
        if not self.client:
            logger.pr_error("Client not initialized")
            return
            
        try:
            await self.client.join()
        except Exception as e:
            logger.pr_error(f"Error in blivedm client: {e}")
        finally:
            self._is_running = False
            
    def stop(self):
        """停止客户端"""
        if self.client and self._is_running:
            self.client.stop()
            logger.pr_info(f"Blivedm client stopped for room {self.room_id}")
            
    async def close(self):
        """关闭客户端"""
        self.stop()
        if self.session:
            await self.session.close()
            self.session = None
            

class DanmakuHandler(blivedm.BaseHandler):
    """弹幕处理Handler"""
    
    def __init__(self, callbacks: dict):
        super().__init__()
        self.callbacks = callbacks
        
    def _on_heartbeat(self, client: blivedm.BLiveClient, message: web_models.HeartbeatMessage):
        """心跳消息"""
        logger.pr_debug(f"[{client.room_id}] Heartbeat")
        
    def _on_danmaku(self, client: blivedm.BLiveClient, message: web_models.DanmakuMessage):
        """弹幕消息"""
        try:
            danmaku_data = {
                'uid': message.uid,
                'nickname': message.uname,
                'text': message.msg,
                'room_id': client.room_id,
                'timestamp': message.timestamp if hasattr(message, 'timestamp') else 0
            }
            
            # 触发回调
            if 'danmaku' in self.callbacks:
                callback = self.callbacks['danmaku']
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(danmaku_data))
                else:
                    callback(danmaku_data)
                    
            logger.pr_info(f"Danmaku: {message.uname}: {message.msg}")
            
        except Exception as e:
            logger.pr_error(f"Error handling danmaku: {e}")
            
    def _on_gift(self, client: blivedm.BLiveClient, message: web_models.GiftMessage):
        """礼物消息"""
        try:
            gift_data = {
                'uid': message.uid,
                'nickname': message.uname,
                'gift_name': message.gift_name,
                'gift_count': message.num,
                'gift_value': message.total_coin / 100,  # 瓜子数转换为B币
                'room_id': client.room_id
            }
            
            # 触发回调
            if 'gift' in self.callbacks:
                callback = self.callbacks['gift']
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(gift_data))
                else:
                    callback(gift_data)
                    
            logger.pr_info(f"Gift: {message.uname} sent {message.gift_name}x{message.num}")
            
        except Exception as e:
            logger.pr_error(f"Error handling gift: {e}")
            
    def _on_user_toast_v2(self, client: blivedm.BLiveClient, message: web_models.UserToastV2Message):
        """舰长消息"""
        try:
            if message.source != 2:  # 过滤非直播间的消息
                guard_data = {
                    'uid': message.uid,
                    'nickname': message.username,
                    'guard_type': message.guard_level,
                    'room_id': client.room_id
                }
                
                # 触发回调
                if 'guard' in self.callbacks:
                    callback = self.callbacks['guard']
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(guard_data))
                    else:
                        callback(guard_data)
                        
                logger.pr_info(f"Guard: {message.username} upgraded to level {message.guard_level}")
                
        except Exception as e:
            logger.pr_error(f"Error handling guard: {e}")
            
    def _on_super_chat(self, client: blivedm.BLiveClient, message: web_models.SuperChatMessage):
        """醒目留言"""
        try:
            sc_data = {
                'uid': message.uid,
                'nickname': message.uname,
                'text': message.message,
                'price': message.price,
                'room_id': client.room_id
            }
            
            # 触发回调
            if 'super_chat' in self.callbacks:
                callback = self.callbacks['super_chat']
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(sc_data))
                else:
                    callback(sc_data)
                    
            logger.pr_info(f"Super Chat: {message.uname} (¥{message.price}): {message.message}")
            
        except Exception as e:
            logger.pr_error(f"Error handling super chat: {e}")
