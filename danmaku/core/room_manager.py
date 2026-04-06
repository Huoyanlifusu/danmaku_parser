"""
直播间管理模块
管理多个直播间的连接和弹幕接收
"""
import asyncio
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
import aiohttp
from log.log import logger


@dataclass
class LiveRoom:
    """直播间数据类"""
    room_id: int
    short_id: int = 0
    title: str = ""
    owner_name: str = ""
    online: int = 0
    is_live: bool = False
    is_connected: bool = False
    client: Optional[Any] = None


class RoomManager:
    """直播间管理器"""
    
    def __init__(self):
        self.rooms: Dict[int, LiveRoom] = {}
        self.active_room_id: Optional[int] = None
        self._callbacks: Dict[str, list] = {
            'danmaku': [],      # 弹幕回调
            'gift': [],         # 礼物回调
            'scout': [],        # 舰长回调
            'like': [],         # 点赞回调
            'user': [],         # 用户进出回调
            'system': [],       # 系统消息回调
        }
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
        
    def register_callback(self, event_type: str, callback: Callable):
        """注册事件回调"""
        if event_type in self._callbacks:
            self._callbacks[event_type].append(callback)
            logger.pr_debug(f"Registered callback for event: {event_type}")
        else:
            logger.pr_error(f"Unknown event type: {event_type}")
            
    def unregister_callback(self, event_type: str, callback: Callable):
        """注销事件回调"""
        if event_type in self._callbacks and callback in self._callbacks[event_type]:
            self._callbacks[event_type].remove(callback)
            
    async def trigger_callback(self, event_type: str, data: Any):
        """触发事件回调"""
        if event_type in self._callbacks:
            for callback in self._callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.pr_error(f"Callback error for {event_type}: {e}")
                    
    async def get_room_info(self, room_id: int) -> Optional[LiveRoom]:
        """获取直播间信息"""
        try:
            import requests
            from ws.util import HEADERS
            from ws.key import _WbiSigner
            import weakref
            
            # 使用同步requests来保持与原始代码一致
            url = "https://api.live.bilibili.com/room/v1/Room/get_info"
            params = {'room_id': room_id}
            
            response = requests.get(url=url, params=params, headers=HEADERS, timeout=10)
            
            if response.status_code != 200:
                logger.pr_error(f"HTTP request failed with status code {response.status_code}")
                return None
            
            data = response.json()
            
            if data.get('code', -1) != 0:
                logger.pr_error(f"API returned error: {data.get('message', 'Unknown error')}")
                return None
            
            room_data = data.get('data', {})
            if not room_data:
                logger.pr_error("API returned empty data")
                return None
            
            # 创建房间对象
            room = LiveRoom(
                room_id=room_data.get('room_id', room_id),
                short_id=room_data.get('short_id', 0),
                title=room_data.get('title', ''),
                owner_name=str(room_data.get('uid', '')),  # 使用uid作为owner标识
                online=room_data.get('online', 0),
                is_live=room_data.get('live_status', 0) == 1
            )
            
            self.rooms[room_id] = room
            logger.pr_info(f"Successfully fetched room info: {room.title}")
            return room
            
        except Exception as e:
            logger.pr_error(f"Error getting room info: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    async def add_room(self, room_id: int) -> bool:
        """添加直播间"""
        room = await self.get_room_info(room_id)
        if room:
            logger.pr_info(f"Added room: {room_id} - {room.title}")
            return True
        return False
        
    def remove_room(self, room_id: int):
        """移除直播间"""
        if room_id in self.rooms:
            del self.rooms[room_id]
            if self.active_room_id == room_id:
                self.active_room_id = None
            logger.pr_info(f"Removed room: {room_id}")
            
    def get_room(self, room_id: int) -> Optional[LiveRoom]:
        """获取直播间对象"""
        return self.rooms.get(room_id)
        
    def set_active_room(self, room_id: int):
        """设置当前活跃直播间"""
        if room_id in self.rooms:
            self.active_room_id = room_id
            logger.pr_info(f"Set active room: {room_id}")
            
    def get_active_room(self) -> Optional[LiveRoom]:
        """获取当前活跃直播间"""
        if self.active_room_id:
            return self.rooms.get(self.active_room_id)
        return None
        
    async def connect_room(self, room_id: int, sessdata: str = "") -> bool:
        """连接到直播间WebSocket"""
        room = self.rooms.get(room_id)
        if not room:
            room = await self.get_room_info(room_id)
            if not room:
                return False
                
        try:
            # 优先使用blivedm库
            try:
                from danmaku.core.blivedm_client import BlivedmClient
                
                blivedm_client = BlivedmClient(room_id, sessdata)
                
                # 设置回调
                callbacks = {
                    'danmaku': self._on_danmaku_callback,
                    'gift': self._on_gift_callback,
                    'guard': self._on_guard_callback,
                }
                
                # 保存client引用
                room.client = blivedm_client
                room.is_connected = True
                
                # 启动blivedm客户端
                await blivedm_client.start(callbacks)
                asyncio.create_task(blivedm_client.run())
                
                logger.pr_info(f"Connected to room {room_id} using blivedm")
                return True
                
            except ImportError:
                logger.pr_debug("blivedm not available, falling back to ws")
                
                # 回退到原始BiliStreamClient
                from ws.ws import BiliStreamClient
                
                client = BiliStreamClient(room_id)
                
                # 保存client引用
                room.client = client
                
                # 启动连接
                asyncio.create_task(self._run_room_client(room_id, client))
                logger.pr_info(f"Connected to room {room_id} using ws")
                return True
                
        except Exception as e:
            logger.pr_error(f"Failed to connect room {room_id}: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    async def _on_danmaku_callback(self, msg: dict):
        """弹幕回调"""
        await self.trigger_callback('danmaku', msg)
        
    async def _on_gift_callback(self, msg: dict):
        """礼物回调"""
        await self.trigger_callback('gift', msg)
        
    async def _on_guard_callback(self, msg: dict):
        """舰长回调"""
        await self.trigger_callback('guard', msg)
            
    async def _run_room_client(self, room_id: int, client):
        """运行房间客户端"""
        try:
            await client.fetch_room_id()
            await client.access_bili_websocket_html()
            
            # 保存client引用
            room = self.rooms.get(room_id)
            if room:
                room.client = client
                room.is_connected = True
            
            # 启动弹幕消费任务
            consume_task = asyncio.create_task(self._consume_danmaku(room_id, client))
            
            # 连接到WebSocket
            await client.connect_to_host()
            
        except Exception as e:
            logger.pr_error(f"Room client error for {room_id}: {e}")
            room = self.rooms.get(room_id)
            if room:
                room.is_connected = False
                
    async def _consume_danmaku(self, room_id: int, client):
        """消费弹幕队列"""
        try:
            while True:
                try:
                    # 从BiliStreamClient的弹幕队列中获取弹幕
                    msg = await asyncio.wait_for(client.recv_danmaku(), timeout=1.0)
                    
                    # 添加房间ID
                    msg['room_id'] = room_id
                    
                    # 触发弹幕回调
                    await self.trigger_callback('danmaku', msg)
                    
                except asyncio.TimeoutError:
                    # 超时，继续等待
                    continue
                except Exception as e:
                    logger.pr_error(f"Error consuming danmaku: {e}")
                    break
                    
        except asyncio.CancelledError:
            logger.pr_info(f"Danmaku consumer cancelled for room {room_id}")
        except Exception as e:
            logger.pr_error(f"Danmaku consumer error for room {room_id}: {e}")
                
    def disconnect_room(self, room_id: int):
        """断开直播间连接"""
        room = self.rooms.get(room_id)
        if room and room.client:
            asyncio.create_task(room.client.close())
            room.is_connected = False
            logger.pr_info(f"Disconnected room: {room_id}")
            
    def disconnect_all(self):
        """断开所有连接"""
        for room_id in list(self.rooms.keys()):
            self.disconnect_room(room_id)
        logger.pr_info("Disconnected all rooms")
        
    async def close(self):
        """关闭管理器"""
        self.disconnect_all()
        if self._session and not self._session.closed:
            await self._session.close()
