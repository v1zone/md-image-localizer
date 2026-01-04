"""
MD Image Localizer - 主入口
将 Markdown 文件中的在线图片本地化
"""
import sys
import os

# 确保可以导入 src 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gui import ImageLocalizerGUI


def main():
    """主函数"""
    app = ImageLocalizerGUI()
    app.run()


if __name__ == "__main__":
    main()
