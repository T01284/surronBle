import os
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
                             QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSlot

from ble_controller import BLEController
from ui_components import (get_app_stylesheet, create_title_label, create_footer_label,
                           create_left_panel, create_right_panel, DeviceListWidget,
                           LogTextEdit)

# 尝试导入帮助对话框
try:
    from help_dialog import HelpDialog
except ImportError:
    HelpDialog = None


class MainWindow(QMainWindow):
    """主窗口类 - 负责UI组装和事件处理"""

    def __init__(self):
        super().__init__()
        self.controller = BLEController()
        self.selected_address = ""
        self.setupUI()
        self.connectSignals()

    def closeEvent(self, event):
        """窗口关闭事件 - 安全关闭应用"""
        try:
            print("开始安全关闭应用...")

            # 关闭BLE控制器
            self.controller.shutdown()

            print("应用关闭完成")
        except Exception as e:
            print(f"关闭时出错: {e}")
        finally:
            event.accept()

    def setupUI(self):
        """设置用户界面"""
        self.setWindowTitle("Surron故障日志读取测试工具")
        self.setGeometry(100, 100, 1200, 800)

        # 应用样式
        self.setStyleSheet(get_app_stylesheet())

        # 创建中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 添加标题
        title_label = create_title_label()
        main_layout.addWidget(title_label)

        # 内容布局
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # 创建左侧面板（设备管理）
        left_panel, self.left_widgets = self._create_left_panel_custom()

        # 创建右侧面板（AT命令控制台）
        right_panel, self.right_widgets = self._create_right_panel_custom()

        # 添加面板到内容布局
        content_layout.addWidget(left_panel)
        content_layout.addWidget(right_panel)

        # 添加内容布局到主布局
        main_layout.addLayout(content_layout)

        # 添加底部说明
        footer_label = create_footer_label()
        main_layout.addWidget(footer_label)

        # 初始化控件引用
        self._init_widget_refs()

    def _create_left_panel_custom(self):
        """创建自定义左侧面板 - 移除扫描按钮"""
        from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QLabel

        left_panel = QGroupBox("设备管理")
        left_panel.setMaximumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(12)
        left_layout.setContentsMargins(15, 25, 15, 15)

        # 扫描状态标签
        scan_status_label = QLabel("🔍 正在后台扫描设备...")
        scan_status_label.setObjectName("scanStatusLabel")
        scan_status_label.setStyleSheet("""
            QLabel#scanStatusLabel {
                background: #e6f3ff;
                border: 1px solid #4a90e2;
                border-radius: 8px;
                padding: 8px 12px;
                color: #2c5aa0;
                font-weight: bold;
                font-size: 13px;
                margin-bottom: 5px;
            }
        """)
        left_layout.addWidget(scan_status_label)

        # 设备列表标签
        device_label = QLabel("发现的Surron设备 (双击连接):")
        device_label.setStyleSheet("margin-top: 5px; margin-bottom: 2px;")
        left_layout.addWidget(device_label)

        # 自定义设备列表
        self.device_list = DeviceListWidget()
        left_layout.addWidget(self.device_list)

        # 连接控制按钮
        connect_layout = QHBoxLayout()
        connect_btn = QPushButton("🔗 连接设备")
        connect_btn.setObjectName("connectButton")
        disconnect_btn = QPushButton("🔌 断开连接")
        disconnect_btn.setObjectName("disconnectButton")
        connect_btn.setEnabled(False)
        disconnect_btn.setEnabled(False)
        connect_layout.addWidget(connect_btn)
        connect_layout.addWidget(disconnect_btn)
        left_layout.addLayout(connect_layout)

        # 状态标签
        status_label = QLabel("状态: 系统初始化中...")
        status_label.setObjectName("statusLabel")
        left_layout.addWidget(status_label)

        return left_panel, {
            'scan_status_label': scan_status_label,
            'device_list': self.device_list,
            'connect_btn': connect_btn,
            'disconnect_btn': disconnect_btn,
            'status_label': status_label
        }

    def _create_right_panel_custom(self):
        """创建自定义右侧面板"""
        from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit

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
            ("📋 读取5条", "AT+LOGLATEST=5"),
            ("📊 获取状态", "AT+LOGSTATUS"),
            ("🔧 系统信息", "AT+LOGSTATS"),
            ("📈 日志统计", "AT+LOGCOUNT"),
            ("🗑️ 清除日志", "AT+LOGCLEAR")
        ]

        preset_buttons = []
        for name, cmd in preset_commands:
            btn = QPushButton(name)
            btn.setProperty('command', cmd)
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
        send_btn = QPushButton("📤 发送")
        send_btn.setEnabled(False)
        cmd_layout.addWidget(cmd_input)
        cmd_layout.addWidget(send_btn)
        right_layout.addLayout(cmd_layout)

        # 通讯日志标签
        log_label = QLabel("通讯日志:")
        log_label.setStyleSheet("margin-top: 8px; margin-bottom: 2px;")
        right_layout.addWidget(log_label)

        # 自定义日志显示区域
        self.log_text = LogTextEdit()
        right_layout.addWidget(self.log_text)

        # 控制按钮 - 添加帮助按钮
        control_layout = QHBoxLayout()
        clear_log_btn = QPushButton("🧹 清除日志")
        save_log_btn = QPushButton("💾 保存日志")
        save_log_btn.setObjectName("saveLogButton")
        help_btn = QPushButton("❓ 帮助")
        help_btn.setObjectName("helpButton")
        
        # 设置帮助按钮样式
        help_btn.setStyleSheet("""
            QPushButton#helpButton {
                background: #9f7aea;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                min-height: 25px;
            }
            QPushButton#helpButton:hover {
                background: #805ad5;
            }
            QPushButton#helpButton:pressed {
                background: #6b46c1;
            }
        """)
        
        control_layout.addWidget(clear_log_btn)
        control_layout.addWidget(save_log_btn)
        control_layout.addStretch()  # 在帮助按钮前添加弹性空间，使其靠右显示
        control_layout.addWidget(help_btn)
        right_layout.addLayout(control_layout)

        return right_panel, {
            'preset_buttons': preset_buttons,
            'cmd_input': cmd_input,
            'send_btn': send_btn,
            'log_text': self.log_text,
            'clear_log_btn': clear_log_btn,
            'save_log_btn': save_log_btn,
            'help_btn': help_btn  # 添加帮助按钮到返回字典
        }

    def _init_widget_refs(self):
        """初始化控件引用"""
        # 左侧控件
        self.scan_status_label = self.left_widgets['scan_status_label']
        self.connect_btn = self.left_widgets['connect_btn']
        self.disconnect_btn = self.left_widgets['disconnect_btn']
        self.status_label = self.left_widgets['status_label']

        # 右侧控件
        self.preset_buttons = self.right_widgets['preset_buttons']
        self.cmd_input = self.right_widgets['cmd_input']
        self.send_btn = self.right_widgets['send_btn']
        self.clear_log_btn = self.right_widgets['clear_log_btn']
        self.save_log_btn = self.right_widgets['save_log_btn']
        self.help_btn = self.right_widgets['help_btn']  # 添加帮助按钮引用

    def connectSignals(self):
        """连接信号和槽"""
        # 左侧面板信号 - 移除扫描按钮相关信号
        self.connect_btn.clicked.connect(self.connect_device)
        self.disconnect_btn.clicked.connect(self.controller.disconnectDevice)

        # 设备列表信号
        self.device_list.itemClicked.connect(self.on_device_selected)
        self.device_list.itemDoubleClicked.connect(self.on_device_double_clicked)

        # 右侧面板信号
        for btn in self.preset_buttons:
            btn.clicked.connect(lambda checked, b=btn: self.send_preset_command(b))

        self.send_btn.clicked.connect(self.send_command)
        self.cmd_input.returnPressed.connect(self.send_command)
        self.clear_log_btn.clicked.connect(self.clear_log)
        self.save_log_btn.clicked.connect(self.save_log)
        self.help_btn.clicked.connect(self.show_help)  # 连接帮助按钮信号

        # BLE控制器信号
        self.controller.deviceFound.connect(self.on_device_found)
        self.controller.deviceLost.connect(self.on_device_lost)  # 新增设备丢失信号
        self.controller.scanningChanged.connect(self.on_scanning_changed)
        self.controller.connectedChanged.connect(self.on_connected_changed)
        self.controller.statusChanged.connect(self.on_status_changed)
        self.controller.logMessage.connect(self.on_log_message)

    # 槽函数实现
    @pyqtSlot(str, str, int)
    def on_device_found(self, name, address, rssi):
        """发现设备槽函数"""
        self.device_list.add_device(name, address, rssi)

    @pyqtSlot(str)
    def on_device_lost(self, address):
        """设备丢失槽函数"""
        self.device_list.remove_device(address)

    @pyqtSlot(bool)
    def on_scanning_changed(self, scanning):
        """扫描状态变化槽函数"""
        if scanning:
            self.scan_status_label.setText("🔍 正在扫描设备...")
            self.scan_status_label.setStyleSheet("""
                QLabel#scanStatusLabel {
                    background: #fff3cd;
                    border: 1px solid #ffc107;
                    border-radius: 8px;
                    padding: 8px 12px;
                    color: #856404;
                    font-weight: bold;
                    font-size: 13px;
                    margin-bottom: 5px;
                }
            """)
        else:
            self.scan_status_label.setText("⏸️ 扫描暂停")
            self.scan_status_label.setStyleSheet("""
                QLabel#scanStatusLabel {
                    background: #e6f3ff;
                    border: 1px solid #4a90e2;
                    border-radius: 8px;
                    padding: 8px 12px;
                    color: #2c5aa0;
                    font-weight: bold;
                    font-size: 13px;
                    margin-bottom: 5px;
                }
            """)

    @pyqtSlot(bool)
    def on_connected_changed(self, connected):
        """连接状态变化槽函数"""
        self.connect_btn.setEnabled(not connected and bool(self.selected_address))
        self.disconnect_btn.setEnabled(connected)
        self.send_btn.setEnabled(connected)

        # 更新状态标签样式
        if connected:
            self.status_label.setObjectName("statusConnected")
        else:
            self.status_label.setObjectName("statusLabel")
        self.status_label.setStyle(self.status_label.style())  # 刷新样式

    @pyqtSlot(str)
    def on_status_changed(self, status):
        """状态变化槽函数"""
        self.status_label.setText(f"状态: {status}")

    @pyqtSlot(str, str)
    def on_log_message(self, message, msg_type):
        """日志消息槽函数"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.add_log_message(message, msg_type, timestamp)

    def on_device_selected(self, item):
        """设备选择事件"""
        self.selected_address = item.data(1)
        self.connect_btn.setEnabled(not self.controller._connected)

    def on_device_double_clicked(self, item):
        """设备双击事件"""
        if not self.controller._connected:
            self.selected_address = item.data(1)
            self.connect_device()

    def connect_device(self):
        """连接设备"""
        if self.selected_address:
            self.controller.connectDevice(self.selected_address)
        else:
            # 尝试从设备列表获取选中的地址
            selected_address = self.device_list.get_selected_address()
            if selected_address:
                self.selected_address = selected_address
                self.controller.connectDevice(self.selected_address)
            else:
                QMessageBox.warning(self, "警告", "请先选择要连接的设备")

    def send_command(self):
        """发送手动输入的命令"""
        command = self.cmd_input.text().strip()
        if command:
            self.controller.sendCommand(command)
            self.cmd_input.clear()

    def send_preset_command(self, button):
        """发送预设命令"""
        command = button.property('command')
        if command:
            self.controller.sendCommand(command)

    def clear_log(self):
        """清除日志"""
        self.log_text.clear_log()

    def show_help(self):
        """显示帮助对话框"""
        help_text = """AT命令参考手册

═══════════════════════════════════════════════════════════════

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

═══════════════════════════════════════════════════════════════

📤 响应格式：
• 成功：+LOGOK: <data>
• 错误：+LOGERROR: <error_message>
• 数据：+LOGDATA: <log_entry>

📊 日志条目格式（新格式）：
<total_count>,<current_index>,<timestamp>,<error_code_hex>,<checksum>

示例：
5,1,1717830615,100200000001,A5B3
5,2,1717830620,200300000002,C7D1
5,3,1717830625,300400000003,E9F2
5,4,1717830630,400500000004,1A2B
5,5,1717830635,500600000005,3C4D

📝 格式说明：
• 错误码格式：12字符十六进制字符串（6字节）
• 时间戳：Unix时间戳（秒）

═══════════════════════════════════════════════════════════════"""

        # 创建消息框并设置详细内容
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("AT命令参考手册")
        msg_box.setText("📋 Surron设备AT命令完整列表")
        msg_box.setDetailedText(help_text)
        msg_box.setIcon(QMessageBox.Icon.Information)
        
        # 设置按钮文本
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.button(QMessageBox.StandardButton.Ok).setText("关闭")
        
        # 设置消息框样式 - 改善文本颜色清晰度
        msg_box.setStyleSheet("""
            QMessageBox {
                background: white;
                font-size: 14px;
                min-width: 600px;
            }
            QMessageBox QLabel {
                color: #1a202c;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
            }
            QMessageBox QPushButton {
                background: #667eea;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 25px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            QMessageBox QPushButton:hover {
                background: #5a67d8;
            }
            QTextEdit {
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.6;
                background: #f8f9fa;
                color: #2d3748;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 15px;
                selection-background-color: #667eea;
                selection-color: white;
            }
        """)
        
        # 设置对话框大小
        msg_box.resize(700, 500)
        
        # 显示对话框
        msg_box.exec()

    def save_log(self):
        """保存日志到文件"""
        log_content = self.log_text.get_log_content()

        if not log_content:
            QMessageBox.information(self, "提示", "没有日志内容可保存")
            return

        # 生成默认文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"BLE_AT_Log_{timestamp}.txt"

        # 打开保存对话框
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "保存日志文件",
            default_filename,
            "文本文件 (*.txt);;所有文件 (*)"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=== BLE AT通讯日志 ===\n")
                    f.write(f"保存时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")

                    for log_line in log_content:
                        f.write(log_line + "\n")

                QMessageBox.information(self, "成功", f"日志已保存到:\n{filename}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存日志失败:\n{str(e)}")