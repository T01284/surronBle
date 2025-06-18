#!/usr/bin/env python3
"""
Surron BLE AT通讯工具
主程序入口 - 无边框现代化界面版本

依赖库:
pip install PyQt6 bleak

作者: T01284
版本: 2.1.0
"""

import sys
import signal
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor, QIcon

from main_window import MainWindow


def create_splash_screen():
    """创建启动画面"""
    # 创建启动画面图像
    pixmap = QPixmap(400, 250)
    pixmap.fill(QColor(102, 126, 234))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 绘制标题
    painter.setPen(QColor(255, 255, 255))
    font = QFont("Arial", 20, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(50, 80, "Surron BLE 工具")

    # 绘制版本
    font = QFont("Arial", 12)
    painter.setFont(font)
    painter.drawText(50, 110, "版本 2.1.0 ")

    # 绘制作者
    painter.drawText(50, 140, "开发者: T01284")

    # 绘制状态
    painter.drawText(50, 180, "正在加载组件...")

    painter.end()

    splash = QSplashScreen(pixmap)
    splash.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
    return splash


def setup_signal_handlers():
    """设置信号处理器"""

    def signal_handler(signum, frame):
        print(f"\n收到信号 {signum}，正在安全退出...")
        QApplication.quit()

    # 设置 Ctrl+C 处理
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)


def check_dependencies():
    """检查依赖库"""
    missing_deps = []

    try:
        import PyQt6
        print("✓ PyQt6 已安装")
    except ImportError:
        missing_deps.append("PyQt6")
        print("❌ PyQt6 未安装")

    try:
        import bleak
        print("✓ bleak 已安装")
    except ImportError:
        missing_deps.append("bleak")
        print("❌ bleak 未安装")

    return missing_deps


def show_dependency_error(missing_deps):
    """显示依赖库错误信息"""
    deps_str = ", ".join(missing_deps)
    error_msg = f"""
缺少必要的依赖库: {deps_str}

请安装缺少的库:
pip install {" ".join(missing_deps)}

或者安装所有依赖:
pip install PyQt6 bleak
    """

    # 如果PyQt6可用，使用消息框；否则使用print
    try:
        app = QApplication([])
        # 设置应用图标
        app.setWindowIcon(QIcon())
        QMessageBox.critical(None, "依赖错误", error_msg)
    except:
        print("=" * 50)
        print("依赖库检查失败")
        print("=" * 50)
        print(error_msg)
        print("=" * 50)


def main():
    """主函数"""
    print("=" * 60)
    print("🔧 Surron BLE AT通讯工具 v2.1.0 (现代化无边框界面)")
    print("=" * 60)

    # 检查依赖库
    print("🔍 检查依赖库...")
    missing_deps = check_dependencies()
    if missing_deps:
        show_dependency_error(missing_deps)
        return 1

    print("✅ 依赖库检查通过")

    try:
        # 创建应用程序
        app = QApplication(sys.argv)
        app.setApplicationName("Surron BLE Tool")
        app.setApplicationVersion("2.1.0")
        app.setOrganizationName("Surron")
        app.setApplicationDisplayName("Surron故障日志读取测试工具")

        # 设置应用程序样式
        app.setStyle('Fusion')  # 使用现代化样式

        # 创建启动画面
        print("🎨 创建启动画面...")
        splash = create_splash_screen()
        splash.show()
        app.processEvents()

        # 设置信号处理
        setup_signal_handlers()

        # 使用定时器处理 Ctrl+C
        timer = QTimer()
        timer.start(500)  # 每500ms检查一次
        timer.timeout.connect(lambda: None)  # 空操作，只是为了让事件循环响应信号

        print("✅ 应用程序初始化完成")

        # 模拟加载过程
        import time
        splash.showMessage("正在初始化BLE控制器...", Qt.AlignmentFlag.AlignBottom, QColor(255, 255, 255))
        app.processEvents()
        time.sleep(0.5)

        splash.showMessage("正在加载UI组件...", Qt.AlignmentFlag.AlignBottom, QColor(255, 255, 255))
        app.processEvents()
        time.sleep(0.5)

        splash.showMessage("正在应用现代化样式...", Qt.AlignmentFlag.AlignBottom, QColor(255, 255, 255))
        app.processEvents()
        time.sleep(0.5)

        # 创建主窗口
        print("🪟 创建无边框主窗口...")
        main_window = MainWindow()

        # 关闭启动画面并显示主窗口
        splash.showMessage("启动完成！", Qt.AlignmentFlag.AlignBottom, QColor(255, 255, 255))
        app.processEvents()
        time.sleep(0.3)

        splash.close()
        main_window.show()

        print("✅ 主窗口已显示")
        print("=" * 60)
        print("🚀 程序运行中... 按 Ctrl+C 退出")
        print("💡 提示: 这是无边框窗口，可以拖拽标题栏移动窗口")
        print("💡 提示: 双击标题栏可以最大化/还原窗口")

        # 运行应用程序
        result = app.exec()

        print("\n✅ 程序正常退出")
        return result

    except KeyboardInterrupt:
        print("\n⚠️ 程序被用户中断")
        return 0
    except Exception as e:
        print(f"\n❌ 程序运行时发生异常:")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        print("\n📋 详细错误信息:")
        traceback.print_exc()

        # 如果可能，显示错误对话框
        try:
            if 'app' in locals():
                QMessageBox.critical(
                    None,
                    "程序错误",
                    f"程序运行时发生错误:\n\n{type(e).__name__}: {str(e)}\n\n"
                    f"请联系开发人员 T01284"
                )
        except:
            pass

        return 1


if __name__ == "__main__":
    # 设置异常钩子
    def exception_hook(exc_type, exc_value, exc_traceback):
        """全局异常处理"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        print("\n" + "=" * 60)
        print("⚠️ 捕获到未处理的异常:")
        print("=" * 60)
        print(f"异常类型: {exc_type.__name__}")
        print(f"异常信息: {exc_value}")
        print("\n📋 调用栈:")
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print("=" * 60)

        # 尝试显示错误对话框
        try:
            app = QApplication.instance()
            if app:
                QMessageBox.critical(
                    None,
                    "严重错误",
                    f"程序发生严重错误:\n\n{exc_type.__name__}: {exc_value}\n\n"
                    f"程序将退出，请联系开发人员 T01284"
                )
        except:
            pass


    sys.excepthook = exception_hook

    # 运行主程序
    sys.exit(main())