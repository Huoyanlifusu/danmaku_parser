"""
弹幕姬事件处理模块
负责处理各种类型的消息事件
"""
from typing import Dict, Any, Callable, Optional
from log.log import logger
import re


class EventHandler:
    """事件处理器"""
    
    def __init__(self, room_manager, statistics):
        self.room_manager = room_manager
        self.statistics = statistics
        
        # 事件过滤器
        self.danmaku_filters = []
        self.gift_filters = []
        self.guard_filters = []
        
        # 关键词过滤规则
        self.blocked_keywords = set()
        self.highlight_keywords = {}
        
    def add_danmaku_filter(self, filter_func: Callable[[Dict], bool]):
        """添加弹幕过滤器"""
        self.danmaku_filters.append(filter_func)
        
    def add_gift_filter(self, filter_func: Callable[[Dict], bool]):
        """添加礼物过滤器"""
        self.gift_filters.append(filter_func)
        
    def add_guard_filter(self, filter_func: Callable[[Dict], bool]):
        """添加舰长过滤器"""
        self.guard_filters.append(filter_func)
        
    def add_blocked_keyword(self, keyword: str):
        """添加屏蔽关键词"""
        self.blocked_keywords.add(keyword)
        logger.pr_info(f"Added blocked keyword: {keyword}")
        
    def remove_blocked_keyword(self, keyword: str):
        """移除屏蔽关键词"""
        self.blocked_keywords.discard(keyword)
        
    def add_highlight_keyword(self, keyword: str, color: str = "red"):
        """添加高亮关键词"""
        self.highlight_keywords[keyword] = color
        logger.pr_info(f"Added highlight keyword: {keyword} -> {color}")
        
    def should_block_danmaku(self, text: str) -> bool:
        """检查是否应该屏蔽弹幕"""
        # 检查屏蔽关键词
        for keyword in self.blocked_keywords:
            if keyword in text:
                return True
        return False
        
    def get_highlight_color(self, text: str) -> Optional[str]:
        """获取高亮颜色"""
        for keyword, color in self.highlight_keywords.items():
            if keyword in text:
                return color
        return None
        
    def handle_danmaku(self, msg: Dict[str, Any]) -> bool:
        """处理弹幕消息"""
        try:
            # 提取弹幕信息
            uid = msg.get('uid', 0)
            nickname = msg.get('nickname', 'Unknown')
            text = msg.get('text', '')
            room_id = msg.get('room_id', 0)
            
            if not text:
                return False
                
            # 关键词过滤
            if self.should_block_danmaku(text):
                logger.pr_debug(f"Blocked danmaku from {nickname}: {text}")
                return False
                
            # 应用自定义过滤器
            for filter_func in self.danmaku_filters:
                if not filter_func(msg):
                    return False
                    
            # 记录统计
            self.statistics.record_danmaku(room_id, uid, nickname, text)
            
            # 检查高亮
            highlight_color = self.get_highlight_color(text)
            if highlight_color:
                msg['highlight'] = highlight_color
                
            logger.pr_info(f"Danmaku: [{nickname}]: {text}")
            return True
            
        except Exception as e:
            logger.pr_error(f"Error handling danmaku: {e}")
            return False
            
    def handle_gift(self, msg: Dict[str, Any]) -> bool:
        """处理礼物消息"""
        try:
            # 提取礼物信息
            uid = msg.get('uid', 0)
            nickname = msg.get('nickname', 'Unknown')
            gift_name = msg.get('gift_name', '')
            gift_count = msg.get('gift_count', 1)
            gift_value = msg.get('gift_value', 0)
            room_id = msg.get('room_id', 0)
            
            if not gift_name:
                return False
                
            # 应用自定义过滤器
            for filter_func in self.gift_filters:
                if not filter_func(msg):
                    return False
                    
            # 记录统计
            self.statistics.record_gift(
                room_id, uid, nickname, 
                gift_name, gift_count, gift_value
            )
            
            logger.pr_info(f"Gift: [{nickname}] sent {gift_count}x {gift_name} (价值:{gift_value})")
            return True
            
        except Exception as e:
            logger.pr_error(f"Error handling gift: {e}")
            return False
            
    def handle_guard(self, msg: Dict[str, Any]) -> bool:
        """处理舰长消息"""
        try:
            # 提取舰长信息
            uid = msg.get('uid', 0)
            nickname = msg.get('nickname', 'Unknown')
            guard_type = msg.get('guard_type', 0)  # 1: 总督, 2: 提督, 3: 舰长
            room_id = msg.get('room_id', 0)
            
            # 应用自定义过滤器
            for filter_func in self.guard_filters:
                if not filter_func(msg):
                    return False
                    
            # 记录统计
            self.statistics.record_guard(room_id, uid, nickname, guard_type)
            
            guard_names = {1: '总督', 2: '提督', 3: '舰长'}
            guard_name = guard_names.get(guard_type, '舰长')
            
            logger.pr_info(f"Guard: [{nickname}] 开通了 {guard_name}")
            return True
            
        except Exception as e:
            logger.pr_error(f"Error handling guard: {e}")
            return False
            
    def handle_like(self, msg: Dict[str, Any]) -> bool:
        """处理点赞消息"""
        try:
            room_id = msg.get('room_id', 0)
            like_count = msg.get('like_count', 1)
            
            self.statistics.record_like(room_id, like_count)
            return True
            
        except Exception as e:
            logger.pr_error(f"Error handling like: {e}")
            return False
            
    def handle_user(self, msg: Dict[str, Any]) -> bool:
        """处理用户进出消息"""
        try:
            room_id = msg.get('room_id', 0)
            online = msg.get('online', 0)
            
            self.statistics.update_online(room_id, online)
            return True
            
        except Exception as e:
            logger.pr_error(f"Error handling user: {e}")
            return False
            
    def handle_system(self, msg: Dict[str, Any]) -> bool:
        """处理系统消息"""
        try:
            cmd = msg.get('cmd', '')
            logger.pr_debug(f"System message: {cmd}")
            return True
            
        except Exception as e:
            logger.pr_error(f"Error handling system: {e}")
            return False
            
    def handle_message(self, msg: Dict[str, Any]):
        """统一消息处理入口"""
        cmd = msg.get('cmd', '')
        
        if cmd == 'DANMU_MSG':
            self.handle_danmaku(msg)
        elif cmd in ('SEND_GIFT', 'GIFT_STORM'):
            self.handle_gift(msg)
        elif cmd == 'GUARD_MSG':
            self.handle_guard(msg)
        elif cmd == 'LIKE_INFO_V3_CLICK':
            self.handle_like(msg)
        elif cmd in ('INTERACT_WORD', 'ROOM_REAL_TIME_MESSAGE_UPDATE'):
            self.handle_user(msg)
        elif cmd in ('LIVE', 'PREPARING', 'CUT_OFF'):
            self.handle_system(msg)
        else:
            self.handle_system(msg)


class DanmakuFilter:
    """弹幕过滤器工具类"""
    
    @staticmethod
    def keyword_filter(keywords: list) -> Callable[[Dict], bool]:
        """关键词过滤器"""
        def filter_func(msg: Dict) -> bool:
            text = msg.get('text', '')
            return any(kw in text for kw in keywords)
        return filter_func
        
    @staticmethod
    def user_filter(uids: set) -> Callable[[Dict], bool]:
        """用户过滤器（只显示指定用户）"""
        def filter_func(msg: Dict) -> bool:
            uid = msg.get('uid', 0)
            return uid in uids
        return filter_func
        
    @staticmethod
    def length_filter(min_length: int = 0, max_length: int = 100) -> Callable[[Dict], bool]:
        """长度过滤器"""
        def filter_func(msg: Dict) -> bool:
            text = msg.get('text', '')
            return min_length <= len(text) <= max_length
        return filter_func
        
    @staticmethod
    def regex_filter(pattern: str) -> Callable[[Dict], bool]:
        """正则表达式过滤器"""
        regex = re.compile(pattern)
        def filter_func(msg: Dict) -> bool:
            text = msg.get('text', '')
            return bool(regex.search(text))
        return filter_func


class GiftFilter:
    """礼物过滤器工具类"""
    
    @staticmethod
    def min_value_filter(min_value: float) -> Callable[[Dict], bool]:
        """最小价值过滤器"""
        def filter_func(msg: Dict) -> bool:
            value = msg.get('gift_value', 0)
            return value >= min_value
        return filter_func
        
    @staticmethod
    def name_filter(names: list) -> Callable[[Dict], bool]:
        """礼物名称过滤器"""
        def filter_func(msg: Dict) -> bool:
            name = msg.get('gift_name', '')
            return name in names
        return filter_func
        
    @staticmethod
    def min_count_filter(min_count: int) -> Callable[[Dict], bool]:
        """最小数量过滤器"""
        def filter_func(msg: Dict) -> bool:
            count = msg.get('gift_count', 1)
            return count >= min_count
        return filter_func
