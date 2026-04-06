"""
B站弹幕姬启动器
使用完整版的弹幕姬UI
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from danmaku.app import main

if __name__ == "__main__":
    main()
