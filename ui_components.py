from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
                             QListWidget, QTextEdit, QLineEdit, QLabel, QGroupBox,
                             QListWidgetItem)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextOption


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
            color: #2d3748;
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
    title_label = QLabel("Surron故障日志读取测试工具 - 持续扫描模式")
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
    footer_label = QLabel("✨ 本程序仅限内部测试使用! | 如有问题请联系T01284")
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
    """创建左侧设备扫描面板 - 已过时，保留兼容性"""
    # 这个函数保留是为了向后兼容，实际使用中应该使用main_window中的自定义面板
    pass


def create_right_panel():
    """创建右侧AT命令控制台面板 - 已过时，保留兼容性"""
    # 这个函数保留是为了向后兼容，实际使用中应该使用main_window中的自定义面板
    pass


class DeviceListWidget(QListWidget):
    """自定义设备列表控件 - 支持设备添加和移除"""

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(300)
        self.device_items = {}  # 存储 address -> QListWidgetItem 的映射

    def add_device(self, name, address, rssi):
        """添加设备到列表"""
        # 检查是否已存在
        if address in self.device_items:
            # 更新现有项
            item = self.device_items[address]
            item.setText(f"📱 {name}\n📍 {address}\n📶 RSSI: {rssi} dBm")
            return

        # 添加新项
        item = QListWidgetItem(f"📱 {name}\n📍 {address}\n📶 RSSI: {rssi} dBm")
        item.setData(1, address)  # 存储地址
        self.addItem(item)
        self.device_items[address] = item

    def remove_device(self, address):
        """从列表中移除设备"""
        if address in self.device_items:
            item = self.device_items[address]
            row = self.row(item)
            if row != -1:
                self.takeItem(row)
            del self.device_items[address]

    def get_selected_address(self):
        """获取选中设备的地址"""
        current_item = self.currentItem()
        if current_item:
            return current_item.data(1)
        return None

    def clear(self):
        """重写clear方法，同时清理映射"""
        super().clear()
        self.device_items.clear()


class LogTextEdit(QTextEdit):
    """自定义日志文本控件 - 支持自动换行"""

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
                line-height: 1.5;
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

        # 启用自动换行
        self.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

    def add_log_message(self, message, msg_type, timestamp):
        """添加日志消息 - 支持自动换行"""
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

        # 处理长消息的换行显示
        formatted_message = self._format_long_message(message)

        # 创建HTML格式的消息
        html_msg = f'''
        <div style="margin: 3px 0; padding: 6px 10px; border-left: 4px solid {config['color']}; background: rgba(255,255,255,0.03); border-radius: 4px;">
            <div style="margin-bottom: 2px;">
                <span style="color: #888; font-size: 11px; font-family: monospace;">[{timestamp}]</span>
                <span style="color: {config['color']}; margin: 0 6px; font-size: 14px;">{config['icon']}</span>
            </div>
            <div style="color: {config['color']}; word-wrap: break-word; white-space: pre-wrap; font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 13px; line-height: 1.4;">
                {formatted_message}
            </div>
        </div>
        '''

        # 存储纯文本版本用于保存
        plain_msg = f"[{timestamp}] {message}"
        self.log_content.append(plain_msg)

        # 插入HTML内容
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertHtml(html_msg)

        # 自动滚动到底部
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _format_long_message(self, message):
        """格式化长消息，适当换行和美化显示"""
        if not message:
            return message

        # 转义HTML特殊字符
        import html
        message = html.escape(message)

        # 处理特别长的消息（超过100个字符）
        if len(message) > 100:
            # 在合适的位置插入换行
            formatted_lines = []
            current_line = ""

            # 按空格分割，但保持完整性
            words = message.split(' ')

            for word in words:
                # 如果当前行加上新词超过100字符，就换行
                if len(current_line + ' ' + word) > 100 and current_line:
                    formatted_lines.append(current_line.strip())
                    current_line = word
                else:
                    if current_line:
                        current_line += ' ' + word
                    else:
                        current_line = word

                # 如果单个词就很长，强制在合适位置换行
                if len(current_line) > 120:
                    # 寻找合适的分割点（逗号、分号、等号等）
                    split_chars = [',', ';', '=', ':', '-', '_']
                    best_split = -1

                    for i in range(80, min(len(current_line), 120)):
                        if current_line[i] in split_chars:
                            best_split = i + 1
                            break

                    if best_split > 0:
                        formatted_lines.append(current_line[:best_split])
                        current_line = current_line[best_split:]

            # 添加最后一行
            if current_line:
                formatted_lines.append(current_line.strip())

            return '\n'.join(formatted_lines)

        return message

    def clear_log(self):
        """清除日志"""
        self.clear()
        self.log_content.clear()

    def get_log_content(self):
        """获取日志内容"""
        return self.log_content.copy()

    def append_plain_text(self, text):
        """添加纯文本（保持向后兼容）"""
        # 移动到末尾并添加文本
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text + '\n')

        # 自动滚动到底部
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())