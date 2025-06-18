from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QProgressBar, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QMovie


class ConnectionDialog(QDialog):
    """连接/断开连接的模态等待对话框"""

    # 信号定义
    cancelRequested = pyqtSignal()

    def __init__(self, parent=None, operation_type="connect", device_name="", device_address=""):
        super().__init__(parent)
        self.operation_type = operation_type  # "connect", "disconnect", "reconnect"
        self.device_name = device_name
        self.device_address = device_address
        self.is_cancelled = False

        self.setupUI()
        self.setupTimer()

    def setupUI(self):
        """设置用户界面"""
        self.setFixedSize(400, 200)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建对话框框架
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #667eea;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            }
        """)

        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(30, 30, 30, 30)
        frame_layout.setSpacing(20)

        # 标题
        title_text = self._get_title_text()
        title_label = QLabel(title_text)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2d3748;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                margin-bottom: 10px;
            }
        """)
        frame_layout.addWidget(title_label)

        # 设备信息（如果有）
        if self.device_name and self.operation_type != "disconnect":
            device_info = QLabel(f"设备: {self.device_name}")
            device_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            device_info.setStyleSheet("""
                QLabel {
                    color: #4a5568;
                    font-size: 14px;
                    background: transparent;
                    margin-bottom: 5px;
                }
            """)
            frame_layout.addWidget(device_info)

            address_info = QLabel(f"地址: {self.device_address}")
            address_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            address_info.setStyleSheet("""
                QLabel {
                    color: #718096;
                    font-size: 12px;
                    background: transparent;
                    margin-bottom: 10px;
                }
            """)
            frame_layout.addWidget(address_info)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 无限进度条
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                background: #f7fafc;
                height: 20px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 6px;
            }
        """)
        frame_layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel(self._get_status_text())
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #667eea;
                font-size: 14px;
                background: transparent;
                margin-top: 5px;
            }
        """)
        frame_layout.addWidget(self.status_label)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 取消按钮（仅在连接时显示）
        if self.operation_type == "connect" or self.operation_type == "reconnect":
            self.cancel_btn = QPushButton("取消")
            self.cancel_btn.setStyleSheet("""
                QPushButton {
                    background: #e53e3e;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 20px;
                    font-size: 14px;
                    font-weight: bold;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background: #c53030;
                }
                QPushButton:pressed {
                    background: #9c2626;
                }
            """)
            self.cancel_btn.clicked.connect(self.cancel_operation)
            button_layout.addWidget(self.cancel_btn)

        button_layout.addStretch()
        frame_layout.addLayout(button_layout)

        main_layout.addWidget(frame)

        # 居中显示
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)

    def setupTimer(self):
        """设置超时定时器"""
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.handle_timeout)

        # 设置超时时间
        if self.operation_type == "connect" or self.operation_type == "reconnect":
            self.timeout_timer.start(15000)  # 15秒超时
        else:  # disconnect
            self.timeout_timer.start(5000)  # 5秒超时

    def _get_title_text(self):
        """获取标题文本"""
        if self.operation_type == "connect":
            return "🔗 正在连接设备..."
        elif self.operation_type == "disconnect":
            return "🔌 正在断开连接..."
        elif self.operation_type == "reconnect":
            return "🔄 正在切换设备..."
        else:
            return "正在处理..."

    def _get_status_text(self):
        """获取状态文本"""
        if self.operation_type == "connect":
            return "请等待设备连接完成"
        elif self.operation_type == "disconnect":
            return "请等待设备断开连接"
        elif self.operation_type == "reconnect":
            return "正在断开当前设备并连接新设备"
        else:
            return "正在处理中..."

    def update_status(self, message):
        """更新状态信息"""
        self.status_label.setText(message)

    def cancel_operation(self):
        """取消操作"""
        self.is_cancelled = True
        self.cancelRequested.emit()
        self.reject()

    def handle_timeout(self):
        """处理超时"""
        if self.operation_type == "connect" or self.operation_type == "reconnect":
            self.update_status("连接超时，请重试")
        else:
            self.update_status("断开连接超时")

        # 2秒后自动关闭
        QTimer.singleShot(2000, self.reject)

    def connection_success(self):
        """连接成功"""
        self.timeout_timer.stop()
        if self.operation_type == "connect":
            self.update_status("✅ 设备连接成功！")
        elif self.operation_type == "reconnect":
            self.update_status("✅ 设备切换成功！")

        # 1秒后自动关闭
        QTimer.singleShot(1000, self.accept)

    def connection_failed(self, error_message=""):
        """连接失败"""
        self.timeout_timer.stop()
        if self.operation_type == "connect":
            self.update_status(f"❌ 连接失败: {error_message}")
        elif self.operation_type == "disconnect":
            self.update_status(f"❌ 断开失败: {error_message}")
        elif self.operation_type == "reconnect":
            self.update_status(f"❌ 切换失败: {error_message}")

        # 3秒后自动关闭
        QTimer.singleShot(3000, self.reject)

    def disconnection_success(self):
        """断开连接成功"""
        self.timeout_timer.stop()
        self.update_status("✅ 设备已断开连接！")

        # 1秒后自动关闭
        QTimer.singleShot(1000, self.accept)

    def keyPressEvent(self, event):
        """键盘事件处理 - 禁用ESC键关闭"""
        if event.key() == Qt.Key.Key_Escape:
            return  # 忽略ESC键
        super().keyPressEvent(event)

    def closeEvent(self, event):
        """关闭事件处理"""
        if hasattr(self, 'timeout_timer'):
            self.timeout_timer.stop()
        super().closeEvent(event)