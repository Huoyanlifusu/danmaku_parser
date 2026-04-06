"""
测试弹幕姬核心功能
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试所有模块导入"""
    print("测试模块导入...")
    
    try:
        from danmaku.app import DanmakuApp, main
        print("✓ danmaku.app 导入成功")
    except Exception as e:
        print(f"✗ danmaku.app 导入失败: {e}")
        return False
    
    try:
        from danmaku.core.room_manager import RoomManager, LiveRoom
        print("✓ danmaku.core.room_manager 导入成功")
    except Exception as e:
        print(f"✗ danmaku.core.room_manager 导入失败: {e}")
        return False
    
    try:
        from danmaku.core.statistics import StatisticsManager, UserStats, RoomStats
        print("✓ danmaku.core.statistics 导入成功")
    except Exception as e:
        print(f"✗ danmaku.core.statistics 导入失败: {e}")
        return False
    
    try:
        from danmaku.core.event_handler import EventHandler, DanmakuFilter, GiftFilter
        print("✓ danmaku.core.event_handler 导入成功")
    except Exception as e:
        print(f"✗ danmaku.core.event_handler 导入失败: {e}")
        return False
    
    try:
        from danmaku.ui.danmaku_window import DanmakuWindow
        print("✓ danmaku.ui.danmaku_window 导入成功")
    except Exception as e:
        print(f"✗ danmaku.ui.danmaku_window 导入失败: {e}")
        return False
    
    try:
        from danmaku.ui.settings import SettingsPanel, FilterSettings, HighlightSettings, AppearanceSettings
        print("✓ danmaku.ui.settings 导入成功")
    except Exception as e:
        print(f"✗ danmaku.ui.settings 导入失败: {e}")
        return False
    
    return True

def test_statistics():
    """测试统计模块"""
    print("\n测试统计模块...")
    
    try:
        from danmaku.core.statistics import StatisticsManager
        
        stats = StatisticsManager()
        
        # 测试记录弹幕
        stats.record_danmaku(12345, 10001, "测试用户", "这是一条测试弹幕")
        summary = stats.get_global_summary()
        assert summary['total_danmaku'] == 1, "弹幕统计错误"
        print("✓ 弹幕统计功能正常")
        
        # 测试记录礼物
        stats.record_gift(12345, 10001, "测试用户", "小心心", 5, 0.1)
        summary = stats.get_global_summary()
        assert summary['total_gift'] == 5, "礼物统计错误"
        print("✓ 礼物统计功能正常")
        
        # 测试记录舰长
        stats.record_guard(12345, 10002, "舰长用户", 3)
        summary = stats.get_global_summary()
        assert summary['total_guard'] == 1, "舰长统计错误"
        print("✓ 舰长统计功能正常")
        
        return True
        
    except Exception as e:
        print(f"✗ 统计模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_event_handler():
    """测试事件处理模块"""
    print("\n测试事件处理模块...")
    
    try:
        from danmaku.core.event_handler import EventHandler
        from danmaku.core.room_manager import RoomManager
        from danmaku.core.statistics import StatisticsManager
        
        room_manager = RoomManager()
        statistics = StatisticsManager()
        handler = EventHandler(room_manager, statistics)
        
        # 测试关键词过滤
        handler.add_blocked_keyword("敏感词")
        assert "敏感词" in handler.blocked_keywords, "关键词添加失败"
        print("✓ 关键词屏蔽功能正常")
        
        # 测试高亮关键词
        handler.add_highlight_keyword("重要", "red")
        assert "重要" in handler.highlight_keywords, "高亮关键词添加失败"
        print("✓ 高亮关键词功能正常")
        
        return True
        
    except Exception as e:
        print(f"✗ 事件处理模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_room_manager():
    """测试直播间管理模块"""
    print("\n测试直播间管理模块...")
    
    try:
        from danmaku.core.room_manager import RoomManager, LiveRoom
        
        manager = RoomManager()
        
        # 测试直播间对象
        room = LiveRoom(
            room_id=12345,
            short_id=1234,
            title="测试直播间",
            owner_name="测试主播",
            online=1000,
            is_live=True
        )
        
        assert room.room_id == 12345, "房间ID错误"
        assert room.title == "测试直播间", "房间标题错误"
        print("✓ 直播间对象创建正常")
        
        # 测试房间管理
        manager.rooms[12345] = room
        retrieved_room = manager.get_room(12345)
        assert retrieved_room is not None, "房间获取失败"
        assert retrieved_room.title == "测试直播间", "房间获取内容错误"
        print("✓ 房间管理功能正常")
        
        return True
        
    except Exception as e:
        print(f"✗ 直播间管理模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("=" * 50)
    print("B站弹幕姬 - 模块测试")
    print("=" * 50)
    
    all_passed = True
    
    # 测试导入
    if not test_imports():
        all_passed = False
    
    # 测试统计模块
    if not test_statistics():
        all_passed = False
    
    # 测试事件处理模块
    if not test_event_handler():
        all_passed = False
    
    # 测试直播间管理模块
    if not test_room_manager():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败，请检查错误信息")
    print("=" * 50)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
