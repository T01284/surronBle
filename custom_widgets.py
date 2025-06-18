from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QLabel, QListWidget, QTextEdit, QListWidgetItem, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QIcon, QPainterPath


class WindowControlButton(QPushButton):
    """自定义窗口控制按钮"""

    def __init__(self, button_type="close"):
        super().__init__()
        self.button_type = button_type
        self.setFixedSize(46, 32)
        self.setStyleSheet(self._get_button_style())

    def _get_button_style(self):
        """获取按钮样式"""
        base_style = """
            QPushButton {
                border: none;
                background: transparent;
                color: #e2e8f0;
                font-size: 14px;
                font-weight: 500;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.08);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.12);
            }
        """

        if self.button_type == "close":
            return base_style + """
                QPushButton:hover {
                    background: #e53e3e;
                    color: white;
                }
                QPushButton:pressed {
                    background: #c53030;
                }
            """
        elif self.button_type == "maximize":
            return base_style + """
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.12);
                }
            """
        else:  # minimize
            return base_style + """
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.12);
                }
            """

    def paintEvent(self, event):
        """绘制按钮图标"""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 设置画笔
        pen = QPen(QColor(226, 232, 240), 1.8)  # 更细更优雅的线条
        painter.setPen(pen)

        # 获取绘制区域
        rect = self.rect()
        center_x = rect.width() // 2
        center_y = rect.height() // 2

        if self.button_type == "close":
            # 绘制 X - 更精细的设计
            painter.drawLine(center_x - 5, center_y - 5, center_x + 5, center_y + 5)
            painter.drawLine(center_x - 5, center_y + 5, center_x + 5, center_y - 5)

        elif self.button_type == "maximize":
            # 绘制最大化图标（方框） - 更小更精致
            painter.drawRect(center_x - 5, center_y - 5, 10, 10)

        elif self.button_type == "minimize":
            # 绘制最小化图标（横线） - 更短更居中
            painter.drawLine(center_x - 5, center_y, center_x + 5, center_y)


class TitleBar(QWidget):
    """自定义标题栏"""

    # 信号定义
    closeClicked = pyqtSignal()
    maximizeClicked = pyqtSignal()
    minimizeClicked = pyqtSignal()

    def __init__(self, title="Surron故障日志读取测试工具"):
        super().__init__()
        self.title = title
        self.setFixedHeight(50)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2d3748, stop:0.5 #4a5568, stop:1 #2d3748);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
        """)

        self.setupUI()

        # 用于窗口拖拽
        self.drag_position = QPoint()

    def setupUI(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 0, 0)
        layout.setSpacing(0)

        # 应用图标和标题
        icon_label = QLabel("🔧")
        icon_label.setStyleSheet("""
            QLabel {
                color: #e2e8f0;
                font-size: 18px;
                padding-right: 10px;
                background: transparent;
            }
        """)

        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            QLabel {
                color: #f7fafc;
                font-size: 15px;
                font-weight: 600;
                background: transparent;
                letter-spacing: 0.5px;
            }
        """)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addStretch()

        # 窗口控制按钮
        self.minimize_btn = WindowControlButton("minimize")
        self.maximize_btn = WindowControlButton("maximize")
        self.close_btn = WindowControlButton("close")

        # 连接信号
        self.minimize_btn.clicked.connect(self.minimizeClicked.emit)
        self.maximize_btn.clicked.connect(self.maximizeClicked.emit)
        self.close_btn.clicked.connect(self.closeClicked.emit)

        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.maximize_btn)
        layout.addWidget(self.close_btn)

    def mousePressEvent(self, event):
        """鼠标按下事件 - 开始拖拽"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖拽窗口"""
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            self.window().move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        """双击标题栏最大化/还原"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.maximizeClicked.emit()


class CustomFrame(QFrame):
    """自定义边框"""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #cbd5e0;
                border-radius: 12px;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            }
        """)


class AnimatedButton(QPushButton):
    """带动画效果的按钮"""

    def __init__(self, text=""):
        super().__init__(text)
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def enterEvent(self, event):
        """鼠标进入事件"""
        super().enterEvent(event)
        # 可以添加悬停动画效果

    def leaveEvent(self, event):
        """鼠标离开事件"""
        super().leaveEvent(event)
        # 可以添加离开动画效果


class StatusIndicator(QWidget):
    """状态指示器"""

    def __init__(self):
        super().__init__()
        self.setFixedSize(12, 12)
        self.status = "disconnected"  # connected, connecting, disconnected, error

    def set_status(self, status):
        """设置状态"""
        self.status = status
        self.update()

    def paintEvent(self, event):
        """绘制状态指示器"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 根据状态设置颜色
        color_map = {
            "connected": QColor(46, 204, 113),  # 绿色
            "connecting": QColor(241, 196, 15),  # 黄色
            "disconnected": QColor(149, 165, 166),  # 灰色
            "error": QColor(231, 76, 60)  # 红色
        }

        color = color_map.get(self.status, QColor(149, 165, 166))
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)

        # 绘制圆形指示器
        painter.drawEllipse(1, 1, 10, 10)

        # 添加高光效果
        if self.status == "connected":
            painter.setBrush(QColor(255, 255, 255, 100))
            painter.drawEllipse(2, 2, 4, 4)


class DeviceListWidget(QListWidget):
    """自定义设备列表控件"""

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(300)
        self.setStyleSheet("""
            QListWidget {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 5px;
                font-size: 12px;
                outline: none;
            }
            QListWidget::item {
                background: white;
                border-radius: 6px;
                padding: 8px;
                margin: 2px;
                border: 1px solid #e9ecef;
            }
            QListWidget::item:hover {
                background: #f1f3f4;
                border: 1px solid #667eea;
                transform: translateY(-1px);
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(102, 126, 234, 0.1), stop:1 rgba(102, 126, 234, 0.05));
                border: 2px solid #667eea;
                font-weight: bold;
                color: #333;
            }
        """)

    def add_device(self, name, address, rssi):
        """添加设备到列表"""
        # 检查是否已存在
        for i in range(self.count()):
            item = self.item(i)
            if item.data(1) == address:
                # 更新现有项
                item.setText(f"📱 {name}\n📍 {address}\n📶 RSSI: {rssi} dBm")
                return

        # 添加新项
        item = QListWidgetItem(f"📱 {name}\n📍 {address}\n📶 RSSI: {rssi} dBm")
        item.setData(1, address)  # 存储地址
        self.addItem(item)

    def get_selected_address(self):
        """获取选中设备的地址"""
        current_item = self.currentItem()
        if current_item:
            return current_item.data(1)
        return None


class LogTextEdit(QTextEdit):
    """自定义日志文本控件"""

    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.log_content = []  # 存储纯文本日志
        self.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e;
                color: #ffffff;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.4;
                selection-background-color: #3390ff;
                selection-color: white;
            }
            QScrollBar:vertical {
                background: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def add_log_message(self, message, msg_type, timestamp):
        """添加日志消息"""
        # 根据类型设置颜色和图标
        type_config = {
            "error": {"color": "#ff6b6b", "icon": "❌"},
            "success": {"color": "#51cf66", "icon": "✅"},
            "warning": {"color": "#ffd43b", "icon": "⚠️"},
            "sent": {"color": "#74c0fc", "icon": "📤"},
            "received": {"color": "#69db7c", "icon": "📥"},
            "info": {"color": "#91a7ff", "icon": "ℹ️"}
        }

        config = type_config.get(msg_type, {"color": "#ffffff", "icon": "📝"})

        # 创建HTML格式的消息
        html_msg = f'''
        <div style="margin: 2px 0; padding: 4px 8px; border-left: 3px solid {config['color']}; background: rgba(255,255,255,0.02);">
            <span style="color: #888; font-size: 11px;">[{timestamp}]</span>
            <span style="color: {config['color']}; margin: 0 4px;">{config['icon']}</span>
            <span style="color: {config['color']};">{message}</span>
        </div>
        '''

        # 存储纯文本版本用于保存
        plain_msg = f"[{timestamp}] {message}"
        self.log_content.append(plain_msg)

        self.insertHtml(html_msg)

        # 自动滚动到底部
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_log(self):
        """清除日志"""
        self.clear()
        self.log_content.clear()

    def get_log_content(self):
        """获取日志内容"""
        return self.log_content.copy()


class GlowEffect(QWidget):
    """发光效果控件"""

    def __init__(self, color=QColor(102, 126, 234), radius=20):
        super().__init__()
        self.glow_color = color
        self.glow_radius = radius
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        """绘制发光效果"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 创建发光路径
        path = QPainterPath()
        path.addRoundedRect(self.rect(), self.glow_radius, self.glow_radius)

        # 绘制发光效果
        for i in range(self.glow_radius):
            alpha = 255 - (i * 255 // self.glow_radius)
            color = QColor(self.glow_color)
            color.setAlpha(alpha // 8)  # 降低透明度使效果更柔和


class HelpDialog(QWidget):
    """自定义帮助对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(600, 700)
        self.setupUI()

        # 居中显示
        if parent:
            parent_rect = parent.geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)

    def setupUI(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # 创建对话框框架
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #cbd5e0;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            }
        """)

        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # 标题栏
        title_bar = QWidget()
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a5568, stop:1 #2d3748);
                border-top-left-radius: 15px;
                border-top-right-radius: 15px;
            }
        """)
        title_bar.setFixedHeight(50)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 10, 0)

        title_label = QLabel("❓ 帮助信息")
        title_label.setStyleSheet("""
            QLabel {
                color: #f7fafc;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
            }
        """)

        close_btn = WindowControlButton("close")
        close_btn.clicked.connect(self.close)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)

        frame_layout.addWidget(title_bar)

        # 内容区域
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background: white;
                border-bottom-left-radius: 15px;
                border-bottom-right-radius: 15px;
            }
        """)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(25, 25, 25, 25)

        # 帮助内容
        help_content = self.create_help_content()
        content_layout.addWidget(help_content)

        frame_layout.addWidget(content_widget)
        layout.addWidget(frame)

    def create_help_content(self):
        """创建帮助内容"""
        scroll_area = QWidget()
        scroll_layout = QVBoxLayout(scroll_area)

        help_text = """
<div style="font-family: Arial, sans-serif; line-height: 1.6; color: #2d3748;">

<h2 style="color: #4a5568; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">
🔧 Surron BLE AT通讯工具 v2.1.0
</h2>

<h3 style="color: #2d3748; margin-top: 25px;">🚀 快速开始</h3>
<ol style="padding-left: 20px;">
<li><b>设备扫描</b>: 点击 "🔍 开始扫描" 搜索附近的Surron设备</li>
<li><b>选择设备</b>: 在列表中单击选择设备，或双击直接连接</li>
<li><b>建立连接</b>: 点击 "🔗 连接设备" 或双击设备建立连接</li>
<li><b>发送命令</b>: 使用快捷按钮或手动输入AT命令</li>
</ol>

<h3 style="color: #2d3748; margin-top: 25px;">📊 状态指示</h3>
<ul style="padding-left: 20px;">
<li><b style="color: #e53e3e;">🔴 红色</b>: 错误状态</li>
<li><b style="color: #d69e2e;">🟡 黄色</b>: 连接中/扫描中</li>
<li><b style="color: #38a169;">🟢 绿色</b>: 已连接</li>
<li><b style="color: #a0aec0;">⚪ 灰色</b>: 断开连接</li>
</ul>

<h3 style="color: #2d3748; margin-top: 25px;">⚡ 快捷命令</h3>
<div style="background: #f7fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #4a5568;">
<ul style="margin: 0; padding-left: 20px;">
<li><b>📋 读取5条</b>: AT+LOGLATEST=5</li>
<li><b>📊 获取状态</b>: AT+LOGSTATUS</li>
<li><b>🔧 系统信息</b>: AT+LOGSTATS</li>
<li><b>📈 日志统计</b>: AT+LOGCOUNT</li>
<li><b>🗑️ 清除日志</b>: AT+LOGCLEAR</li>
</ul>
</div>

<h3 style="color: #2d3748; margin-top: 25px;">🪟 窗口操作</h3>
<ul style="padding-left: 20px;">
<li><b>移动窗口</b>: 拖拽标题栏</li>
<li><b>最大化/还原</b>: 双击标题栏或点击最大化按钮</li>
<li><b>最小化</b>: 点击最小化按钮</li>
<li><b>关闭程序</b>: 点击关闭按钮</li>
</ul>

<h3 style="color: #2d3748; margin-top: 25px;">💡 使用技巧</h3>
<div style="background: #edf2f7; padding: 15px; border-radius: 8px;">
<ul style="margin: 0; padding-left: 20px;">
<li>设备列表显示RSSI信号强度，选择信号强的设备</li>
<li>日志区域支持彩色显示，方便区分不同类型的消息</li>
<li>可以使用 Enter 键快速发送命令</li>
<li>长时间无响应时，尝试重新连接设备</li>
</ul>
</div>

<h3 style="color: #2d3748; margin-top: 25px;">🆘 故障排除</h3>
<ul style="padding-left: 20px;">
<li><b>扫描不到设备</b>: 确保设备已开机且在附近</li>
<li><b>连接失败</b>: 检查设备是否被其他程序占用</li>
<li><b>命令无响应</b>: 检查设备连接状态，必要时重新连接</li>
</ul>

<div style="text-align: center; margin-top: 30px; padding: 15px; background: #f0fff4; border-radius: 8px; border: 1px solid #9ae6b4;">
<p style="margin: 0; color: #2d3748;"><b>开发者</b>: T01284 | <b>版本</b>: 2.1.0</p>
</div>

</div>
        """

        from PyQt6.QtWidgets import QTextEdit
        text_edit = QTextEdit()
        text_edit.setHtml(help_text)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                border: none;
                background: transparent;
                font-size: 13px;
            }
            QScrollBar:vertical {
                background: #f7fafc;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e0;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0aec0;
            }
        """)

        scroll_layout.addWidget(text_edit)
        return scroll_area

    def mousePressEvent(self, event):
        """鼠标按下事件 - 开始拖拽"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖拽窗口"""
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()