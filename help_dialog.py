from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QFrame)
from PyQt6.QtCore import Qt


class HelpDialog(QDialog):
    """AT命令帮助对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AT命令参考手册")
        self.setFixedSize(1000, 750)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.setupUI()

        # 居中显示
        if parent:
            parent_rect = parent.geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)

    def setupUI(self):
        """设置用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 标题栏
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
        """)
        title_frame.setFixedHeight(60)

        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(25, 0, 25, 0)

        # 标题文本
        title_label = QLabel("📋 AT命令参考手册")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }
        """)

        # 版本信息
        version_label = QLabel("v2.1.0")
        version_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 14px;
                background: transparent;
            }
        """)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(version_label)

        main_layout.addWidget(title_frame)

        # 内容区域
        content_widget = QFrame()
        content_widget.setStyleSheet("""
            QFrame {
                background: white;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
        """)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(15)

        # AT命令帮助内容
        help_text = """AT命令完整参考列表

═══════════════════════════════════════════════════════════════════════════════════════════════

📋 支持的AT命令格式：

1. 帮助命令
   AT+LOGHELP
   返回：所有支持的命令列表

2. 状态查询
   AT+LOGSTATUS
   返回：日志系统初始化状态

3. 统计信息
   AT+LOGSTATS
   返回：日志条数、存储使用情况等

4. 日志条数
   AT+LOGCOUNT
   返回：当前日志总条数

5. 读取所有日志
   AT+LOGREADALL
   返回：所有日志条目（分批发送）

6. 读取最新N条日志
   AT+LOGLATEST=<count>
   示例：AT+LOGLATEST=10
   返回：最新的10条日志

7. 按序列号范围读取
   AT+LOGRANGE=<start_seq>,<end_seq>
   示例：AT+LOGRANGE=100,200
   返回：序列号100-200的日志

8. 按时间范围读取
   AT+LOGTIME=<start_time>,<end_time>
   示例：AT+LOGTIME=1000,2000
   返回：时间戳1000-2000的日志

9. 按错误码读取
   AT+LOGERROR=<error_code_hex>,<match_bytes>
   示例：AT+LOGERROR=100200000001,2
   返回：匹配前2字节的所有日志

10. 完整性检查
    AT+LOGCHECK
    返回：检查结果

11. 清空所有日志
    AT+LOGCLEAR
    返回：清空结果（危险操作）

12. 插入错误日志(指定时间)
    AT+LOGINSERT=<error_code_hex>,<year>,<month>,<day>,<hour>,<minute>,<second>
    示例：AT+LOGINSERT=100200000001,2025,6,11,14,30,15
    返回：插入结果

13. 插入错误日志(当前时间)
    AT+LOGINSERTNOW=<error_code_hex>
    示例：AT+LOGINSERTNOW=100200000001
    返回：插入结果

═══════════════════════════════════════════════════════════════════════════════════════════════

📤 响应格式：
• 成功：+LOGOK: <data>
• 错误：+LOGERROR: <error_message>
• 数据：+LOGDATA: <log_entry>

═══════════════════════════════════════════════════════════════════════════════════════════════

📊 日志条目格式（新格式）：
<total_count>,<current_index>,<timestamp>,<error_code_hex>,<checksum>

日志条目示例：
5,1,1717830615,100200000001,A5B3
5,2,1717830620,200300000002,C7D1
5,3,1717830625,300400000003,E9F2
5,4,1717830630,400500000004,1A2B
5,5,1717830635,500600000005,3C4D

═══════════════════════════════════════════════════════════════════════════════════════════════

📝 格式详细说明：
• 错误码格式：12字符十六进制字符串（6字节）
• 时间戳：Unix时间戳（秒）
• 校验和：2字节十六进制校验码
• 总数量：当前查询返回的日志总条数
• 当前索引：当前日志条目在结果集中的位置

═══════════════════════════════════════════════════════════════════════════════════════════════

⚠️ 重要提示：
• AT+LOGCLEAR 命令会永久删除所有日志数据，使用前请确认
• 插入命令仅用于测试目的，请勿在生产环境中使用
• 时间戳必须为有效的Unix时间戳格式
• 错误码必须为完整的12位十六进制字符串
• 范围查询时，起始值不能大于结束值
• 匹配字节数不能超过错误码的总字节数（最大6字节）

═══════════════════════════════════════════════════════════════════════════════════════════════"""

        # 创建文本显示区域
        text_edit = QTextEdit()
        text_edit.setPlainText(help_text)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 14px;
                line-height: 1.7;
                background: #fafbfc;
                color: #1a202c;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 20px;
                selection-background-color: #667eea;
                selection-color: white;
            }
            QScrollBar:vertical {
                background: #f1f3f4;
                width: 14px;
                border-radius: 7px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #c1c7d0;
                border-radius: 7px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #9aa0a6;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        content_layout.addWidget(text_edit)

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 15, 0, 0)

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #667eea;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 40px;
                font-size: 15px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background: #5a67d8;
            }
            QPushButton:pressed {
                background: #4c51bf;
            }
        """)
        close_btn.clicked.connect(self.close)

        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addStretch()

        content_layout.addLayout(button_layout)
        main_layout.addWidget(content_widget)

        # 设置整体样式
        self.setStyleSheet("""
            QDialog {
                background: white;
            }
        """)