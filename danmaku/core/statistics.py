"""
弹幕姬统计管理模块
负责统计弹幕、礼物、舰长等数据
"""
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import threading


@dataclass
class UserStats:
    """用户统计"""
    uid: int
    nickname: str = ""
    danmaku_count: int = 0
    gift_count: int = 0
    gift_value: float = 0.0
    first_time: datetime = field(default_factory=datetime.now)
    last_time: datetime = field(default_factory=datetime.now)


@dataclass
class RoomStats:
    """直播间统计"""
    room_id: int
    danmaku_count: int = 0
    gift_count: int = 0
    gift_value: float = 0.0
    guard_count: int = 0
    like_count: int = 0
    user_count: int = 0
    peak_online: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    last_danmaku_time: datetime = field(default_factory=datetime.now)
    
    # 时间段统计
    danmaku_per_minute: deque = field(default_factory=lambda: deque(maxlen=60))
    danmaku_per_hour: List[int] = field(default_factory=list)
    
    # 热门弹幕统计
    hot_keywords: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    top_danmaku: List[tuple] = field(default_factory=list)


class StatisticsManager:
    """统计管理器"""
    
    def __init__(self):
        self._lock = threading.Lock()
        
        # 全局统计
        self.total_danmaku = 0
        self.total_gift = 0
        self.total_gift_value = 0.0
        self.total_guard = 0
        self.total_like = 0
        self.total_user = 0
        
        # 在线人数
        self.current_online = 0
        self.peak_online = 0
        
        # 用户统计
        self.users: Dict[int, UserStats] = {}
        
        # 直播间统计
        self.rooms: Dict[int, RoomStats] = {}
        
        # 最近弹幕记录
        self.recent_danmaku = deque(maxlen=1000)
        
        # 最近礼物记录
        self.recent_gifts = deque(maxlen=500)
        
        # 启动时间
        self.start_time = datetime.now()
        
    def _get_or_create_user(self, uid: int, nickname: str = "") -> UserStats:
        """获取或创建用户统计"""
        if uid not in self.users:
            self.users[uid] = UserStats(uid=uid, nickname=nickname)
        elif nickname and not self.users[uid].nickname:
            self.users[uid].nickname = nickname
        return self.users[uid]
    
    def _get_or_create_room(self, room_id: int) -> RoomStats:
        """获取或创建直播间统计"""
        if room_id not in self.rooms:
            self.rooms[room_id] = RoomStats(room_id=room_id)
        return self.rooms[room_id]
    
    def record_danmaku(self, room_id: int, uid: int, nickname: str, text: str):
        """记录弹幕"""
        with self._lock:
            now = datetime.now()
            
            # 更新全局统计
            self.total_danmaku += 1
            
            # 更新用户统计
            user = self._get_or_create_user(uid, nickname)
            user.danmaku_count += 1
            user.last_time = now
            
            # 更新直播间统计
            room = self._get_or_create_room(room_id)
            room.danmaku_count += 1
            room.last_danmaku_time = now
            
            # 更新每分钟统计
            room.danmaku_per_minute.append((now, 1))
            
            # 记录最近弹幕
            self.recent_danmaku.append({
                'room_id': room_id,
                'uid': uid,
                'nickname': nickname,
                'text': text,
                'time': now
            })
            
            # 更新热门关键词
            self._update_hot_keywords(room, text)
    
    def _update_hot_keywords(self, room: RoomStats, text: str):
        """更新热门关键词"""
        # 简单分词，统计2-6个字的中文词组
        text = text.strip()
        if len(text) < 2:
            return
            
        # 统计连续中文字符
        keywords = []
        current = ""
        for char in text:
            if '\u4e00' <= char <= '\u9fff':  # 中文字符
                current += char
                if len(current) >= 2:
                    keywords.append(current)
            else:
                if len(current) >= 2:
                    keywords.append(current)
                current = ""
        
        if len(current) >= 2:
            keywords.append(current)
        
        # 更新计数
        for keyword in keywords:
            if len(keyword) <= 6:
                room.hot_keywords[keyword] += 1
    
    def record_gift(self, room_id: int, uid: int, nickname: str, 
                   gift_name: str, gift_count: int, gift_value: float):
        """记录礼物"""
        with self._lock:
            now = datetime.now()
            
            # 更新全局统计
            self.total_gift += gift_count
            self.total_gift_value += gift_value * gift_count
            
            # 更新用户统计
            user = self._get_or_create_user(uid, nickname)
            user.gift_count += gift_count
            user.gift_value += gift_value * gift_count
            user.last_time = now
            
            # 更新直播间统计
            room = self._get_or_create_room(room_id)
            room.gift_count += gift_count
            room.gift_value += gift_value * gift_count
            
            # 记录最近礼物
            self.recent_gifts.append({
                'room_id': room_id,
                'uid': uid,
                'nickname': nickname,
                'gift_name': gift_name,
                'gift_count': gift_count,
                'gift_value': gift_value,
                'time': now
            })
    
    def record_guard(self, room_id: int, uid: int, nickname: str, guard_type: int):
        """记录舰长"""
        with self._lock:
            now = datetime.now()
            
            # 更新全局统计
            self.total_guard += 1
            
            # 更新用户统计
            user = self._get_or_create_user(uid, nickname)
            user.last_time = now
            
            # 更新直播间统计
            room = self._get_or_create_room(room_id)
            room.guard_count += 1
    
    def record_like(self, room_id: int, count: int = 1):
        """记录点赞"""
        with self._lock:
            self.total_like += count
            
            room = self._get_or_create_room(room_id)
            room.like_count += count
    
    def update_online(self, room_id: int, online: int):
        """更新在线人数"""
        with self._lock:
            self.current_online = online
            if online > self.peak_online:
                self.peak_online = online
            
            room = self._get_or_create_room(room_id)
            if online > room.peak_online:
                room.peak_online = online
    
    def get_room_summary(self, room_id: int) -> Optional[Dict]:
        """获取直播间统计摘要"""
        with self._lock:
            room = self.rooms.get(room_id)
            if not room:
                return None
            
            # 计算弹幕速率（每分钟）
            now = datetime.now()
            one_minute_ago = now - timedelta(minutes=1)
            recent_count = sum(1 for t, _ in room.danmaku_per_minute if t > one_minute_ago)
            
            # 获取Top用户
            top_users = sorted(
                [(uid, user) for uid, user in self.users.items()],
                key=lambda x: x[1].danmaku_count,
                reverse=True
            )[:10]
            
            # 获取热门关键词
            hot_keywords = sorted(
                room.hot_keywords.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]
            
            return {
                'room_id': room_id,
                'danmaku_count': room.danmaku_count,
                'gift_count': room.gift_count,
                'gift_value': room.gift_value,
                'guard_count': room.guard_count,
                'like_count': room.like_count,
                'user_count': len(self.users),
                'peak_online': room.peak_online,
                'danmaku_per_minute': recent_count,
                'top_users': [(uid, user.nickname, user.danmaku_count) for uid, user in top_users],
                'hot_keywords': hot_keywords,
                'start_time': room.start_time,
                'last_danmaku': room.last_danmaku_time
            }
    
    def get_global_summary(self) -> Dict:
        """获取全局统计摘要"""
        with self._lock:
            uptime = datetime.now() - self.start_time
            
            return {
                'total_danmaku': self.total_danmaku,
                'total_gift': self.total_gift,
                'total_gift_value': self.total_gift_value,
                'total_guard': self.total_guard,
                'total_like': self.total_like,
                'total_user': len(self.users),
                'current_online': self.current_online,
                'peak_online': self.peak_online,
                'uptime': uptime,
                'start_time': self.start_time
            }
    
    def get_recent_danmaku(self, limit: int = 100) -> List[Dict]:
        """获取最近弹幕"""
        with self._lock:
            return list(self.recent_danmaku)[-limit:]
    
    def get_recent_gifts(self, limit: int = 50) -> List[Dict]:
        """获取最近礼物"""
        with self._lock:
            return list(self.recent_gifts)[-limit:]
    
    def clear(self):
        """清空统计数据"""
        with self._lock:
            self.total_danmaku = 0
            self.total_gift = 0
            self.total_gift_value = 0.0
            self.total_guard = 0
            self.total_like = 0
            self.total_user = 0
            self.current_online = 0
            self.peak_online = 0
            self.users.clear()
            self.rooms.clear()
            self.recent_danmaku.clear()
            self.recent_gifts.clear()
            self.start_time = datetime.now()
