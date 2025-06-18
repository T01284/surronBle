#!/usr/bin/env python3
"""
Surron BLE AT通讯工具
主程序入口

依赖库:
pip install PyQt6 bleak

作者: T01284
版本: 2.0.0
"""

import sys
import signal
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

from main_window import MainWindow


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
    except ImportError:
        missing_deps.append("PyQt6")

    try:
        import bleak
    except ImportError:
        missing_deps.append("bleak")

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
        QMessageBox.critical(None, "依赖错误", error_msg)
    except:
        print("=" * 50)
        print("依赖库检查失败")
        print("=" * 50)
        print(error_msg)
        print("=" * 50)


def main():
    """主函数"""
    print("=" * 50)
    print("Surron BLE AT通讯工具 v2.0.0")
    print("=" * 50)

    # 检查依赖库
    missing_deps = check_dependencies()
    if missing_deps:
        show_dependency_error(missing_deps)
        return 1

    print("✓ 依赖库检查通过")

    try:
        # 创建应用程序
        app = QApplication(sys.argv)
        app.setApplicationName("Surron BLE Tool")
        app.setApplicationVersion("2.0.0")
        app.setOrganizationName("Surron")

        # 设置信号处理
        setup_signal_handlers()

        # 使用定时器处理 Ctrl+C
        timer = QTimer()
        timer.start(500)  # 每500ms检查一次
        timer.timeout.connect(lambda: None)  # 空操作，只是为了让事件循环响应信号

        print("✓ 应用程序初始化完成")

        # 创建主窗口
        main_window = MainWindow()
        main_window.show()

        print("✓ 主窗口已显示")
        print("=" * 50)
        print("程序运行中... 按 Ctrl+C 退出")

        # 运行应用程序
        result = app.exec()

        print("\n程序正常退出")
        return result

    except KeyboardInterrupt:
        print("\n程序被用户中断")
        return 0
    except Exception as e:
        print(f"\n程序运行时发生异常:")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        print("\n详细错误信息:")
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

        print("\n" + "=" * 50)
        print("捕获到未处理的异常:")
        print("=" * 50)
        print(f"异常类型: {exc_type.__name__}")
        print(f"异常信息: {exc_value}")
        print("\n调用栈:")
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print("=" * 50)

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