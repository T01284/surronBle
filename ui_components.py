from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
                             QListWidget, QTextEdit, QLineEdit, QLabel, QGroupBox,
                             QListWidgetItem)
from PyQt6.QtCore import Qt


def get_app_stylesheet():
    """获取应用程序样式表"""
    return """
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #667eea, stop:1 #764ba2);
        }
        QGroupBox {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 15px;
            margin: 5px;
            padding-top: 10px;
            font-size: 14px;
            font-weight: bold;
            color: #333;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 15px;
            top: 8px;
            padding: 5px 8px;
            background: white;
            color: #667eea;
            font-size: 16px;
            font-weight: bold;
            border-radius: 5px;
        }
        QPushButton {
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: bold;
            min-height: 25px;
        }
        QPushButton:hover {
            background: #5a67d8;
        }
        QPushButton:pressed {
            background: #4c51bf;
        }
        QPushButton:disabled {
            background: #ccc;
            color: #666;
        }
        QPushButton#stopButton {
            background: #f56565;
        }
        QPushButton#stopButton:hover {
            background: #e53e3e;
        }
        QPushButton#connectButton {
            background: #48bb78;
        }
        QPushButton#connectButton:hover {
            background: #38a169;
        }
        QPushButton#disconnectButton {
            background: #f56565;
        }
        QPushButton#disconnectButton:hover {
            background: #e53e3e;
        }
        QPushButton#saveLogButton {
            background: #38b2ac;
        }
        QPushButton#saveLogButton:hover {
            background: #319795;
        }
        QListWidget {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 5px;
            font-size: 12px;
        }
        QListWidget::item {
            background: transparent;
            border-radius: 5px;
            padding: 6px;
            margin: 1px;
            border: 1px solid transparent;
            color: #2d3748;
        }
        QListWidget::item:hover {
            background: #e9ecef;
            border: 1px solid #667eea;
        }
        QListWidget::item:selected {
            background: rgba(102, 126, 234, 0.15);
            border: 2px solid #667eea;
            font-weight: bold;
        }
        QTextEdit {
            background: #1a1a1a;
            color: #ffffff;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 10px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
        }
        QLineEdit {
            background: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            padding: 8px;
            font-size: 14px;
        }
        QLineEdit:focus {
            border-color: #667eea;
        }
        QLabel#statusLabel {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 8px;
            padding: 8px 12px;
            color: #721c24;
            font-weight: bold;
            font-size: 13px;
        }
        QLabel#statusConnected {
            background: #d4edda;
            border-color: #c3e6cb;
            color: #155724;
        }
        QLabel {
            color: #333;
            font-size: 13px;
            font-weight: bold;
            margin: 2px 0;
            background: transparent;
        }
    """


def create_title_label():
    """创建标题标签"""
    title_label = QLabel("Surron故障日志读取测试工具")
    title_label.setStyleSheet("""
        QLabel {
            background: rgba(255, 255, 255, 0.95);
            color: #333;
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            padding: 15px;
            border-radius: 12px;
            border: 2px solid #667eea;
            margin-bottom: 10px;
        }
    """)
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return title_label


def create_footer_label():
    """创建底部说明标签"""
    footer_label = QLabel("本工具为内部测试使用，如果有任何问题请联系T01284")
    footer_label.setStyleSheet("""
        QLabel {
            background: rgba(255, 255, 255, 0.9);
            color: #666;
            font-size: 12px;
            font-weight: normal;
            text-align: center;
            padding: 8px 15px;
            border-radius: 8px;
            border: 1px solid #ddd;
            margin-top: 10px;
        }
    """)
    footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return footer_label


def create_left_panel():
    """创建左侧设备扫描面板"""
    left_panel = QGroupBox("设备扫描")
    left_panel.setMaximumWidth(350)
    left_layout = QVBoxLayout(left_panel)
    left_layout.setSpacing(12)
    left_layout.setContentsMargins(15, 25, 15, 15)

    # 扫描控制按钮
    scan_layout = QHBoxLayout()
    scan_btn = QPushButton("开始扫描")
    stop_scan_btn = QPushButton("停止扫描")
    stop_scan_btn.setObjectName("stopButton")
    stop_scan_btn.setEnabled(False)
    scan_layout.addWidget(scan_btn)
    scan_layout.addWidget(stop_scan_btn)
    left_layout.addLayout(scan_layout)

    # 设备列表标签
    device_label = QLabel("发现的Surron设备 (双击连接):")
    device_label.setStyleSheet("margin-top: 5px; margin-bottom: 2px;")
    left_layout.addWidget(device_label)

    # 设备列表
    device_list = QListWidget()
    device_list.setMinimumHeight(300)
    left_layout.addWidget(device_list)

    # 连接控制按钮
    connect_layout = QHBoxLayout()
    connect_btn = QPushButton("连接设备")
    connect_btn.setObjectName("connectButton")
    disconnect_btn = QPushButton("断开连接")
    disconnect_btn.setObjectName("disconnectButton")
    connect_btn.setEnabled(False)
    disconnect_btn.setEnabled(False)
    connect_layout.addWidget(connect_btn)
    connect_layout.addWidget(disconnect_btn)
    left_layout.addLayout(connect_layout)

    # 状态标签
    status_label = QLabel("状态: 就绪")
    status_label.setObjectName("statusLabel")
    left_layout.addWidget(status_label)

    return left_panel, {
        'scan_btn': scan_btn,
        'stop_scan_btn': stop_scan_btn,
        'device_list': device_list,
        'connect_btn': connect_btn,
        'disconnect_btn': disconnect_btn,
        'status_label': status_label
    }


def create_right_panel():
    """创建右侧AT命令控制台面板"""
    right_panel = QGroupBox("AT命令控制台")
    right_layout = QVBoxLayout(right_panel)
    right_layout.setSpacing(12)
    right_layout.setContentsMargins(15, 25, 15, 15)

    # 预设命令标签
    preset_label = QLabel("快捷命令:")
    preset_label.setStyleSheet("margin-bottom: 5px;")
    right_layout.addWidget(preset_label)

    # 预设命令按钮
    preset_layout = QHBoxLayout()
    preset_commands = [
        ("读取5条", "AT+LOGLATEST=5"),
        ("获取状态", "AT+LOGSTATUS"),
        ("系统信息", "AT+LOGSTATS"),
        ("日志统计", "AT+LOGCOUNT"),
        ("清除日志", "AT+LOGCLEAR")
    ]

    preset_buttons = []
    for name, cmd in preset_commands:
        btn = QPushButton(name)
        btn.setProperty('command', cmd)  # 存储命令
        preset_layout.addWidget(btn)
        preset_buttons.append(btn)

    right_layout.addLayout(preset_layout)

    # 手动命令输入标签
    cmd_label = QLabel("手动输入AT命令:")
    cmd_label.setStyleSheet("margin-top: 5px; margin-bottom: 2px;")
    right_layout.addWidget(cmd_label)

    # 命令输入框和发送按钮
    cmd_layout = QHBoxLayout()
    cmd_input = QLineEdit()
    cmd_input.setPlaceholderText("输入AT命令...")
    send_btn = QPushButton("发送")
    send_btn.setEnabled(False)
    cmd_layout.addWidget(cmd_input)
    cmd_layout.addWidget(send_btn)
    right_layout.addLayout(cmd_layout)

    # 通讯日志标签
    log_label = QLabel("通讯日志:")
    log_label.setStyleSheet("margin-top: 8px; margin-bottom: 2px;")
    right_layout.addWidget(log_label)

    # 日志显示区域
    log_text = QTextEdit()
    log_text.setReadOnly(True)
    right_layout.addWidget(log_text)

    # 控制按钮
    control_layout = QHBoxLayout()
    clear_log_btn = QPushButton("清除日志")
    save_log_btn = QPushButton("保存日志")
    save_log_btn.setObjectName("saveLogButton")
    control_layout.addWidget(clear_log_btn)
    control_layout.addWidget(save_log_btn)
    control_layout.addStretch()
    right_layout.addLayout(control_layout)

    return right_panel, {
        'preset_buttons': preset_buttons,
        'cmd_input': cmd_input,
        'send_btn': send_btn,
        'log_text': log_text,
        'clear_log_btn': clear_log_btn,
        'save_log_btn': save_log_btn
    }


class DeviceListWidget(QListWidget):
    """自定义设备列表控件"""

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(300)

    def add_device(self, name, address, rssi):
        """添加设备到列表"""
        # 检查是否已存在
        for i in range(self.count()):
            item = self.item(i)
            if item.data(1) == address:
                # 更新现有项
                item.setText(f"{name}\n{address}\nRSSI: {rssi} dBm")
                return

        # 添加新项
        item = QListWidgetItem(f"{name}\n{address}\nRSSI: {rssi} dBm")
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

    def add_log_message(self, message, msg_type, timestamp):
        """添加日志消息"""
        # 根据类型设置颜色
        color_map = {
            "error": "#ff6b6b",
            "success": "#51cf66",
            "warning": "#ffd43b",
            "sent": "#74c0fc",
            "received": "#69db7c",
            "info": "#ffffff"
        }

        color = color_map.get(msg_type, "#ffffff")
        html_msg = f'<span style="color: {color};">[{timestamp}] {message}</span>'

        # 存储纯文本版本用于保存
        plain_msg = f"[{timestamp}] {message}"
        self.log_content.append(plain_msg)

        self.append(html_msg)

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