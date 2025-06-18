import os
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
                             QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSlot

from ble_controller import BLEController
from ui_components import (get_app_stylesheet, create_title_label, create_footer_label,
                           create_left_panel, create_right_panel, DeviceListWidget,
                           LogTextEdit)


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

        # 创建左侧面板（设备扫描）
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
        """创建自定义左侧面板"""
        from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QLabel

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

        # 自定义设备列表
        self.device_list = DeviceListWidget()
        left_layout.addWidget(self.device_list)

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
            ("读取5条", "AT+LOGLATEST=5"),
            ("获取状态", "AT+LOGSTATUS"),
            ("系统信息", "AT+LOGSTATS"),
            ("日志统计", "AT+LOGCOUNT"),
            ("清除日志", "AT+LOGCLEAR")
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
        send_btn = QPushButton("发送")
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
            'log_text': self.log_text,
            'clear_log_btn': clear_log_btn,
            'save_log_btn': save_log_btn
        }

    def _init_widget_refs(self):
        """初始化控件引用"""
        # 左侧控件
        self.scan_btn = self.left_widgets['scan_btn']
        self.stop_scan_btn = self.left_widgets['stop_scan_btn']
        self.connect_btn = self.left_widgets['connect_btn']
        self.disconnect_btn = self.left_widgets['disconnect_btn']
        self.status_label = self.left_widgets['status_label']

        # 右侧控件
        self.preset_buttons = self.right_widgets['preset_buttons']
        self.cmd_input = self.right_widgets['cmd_input']
        self.send_btn = self.right_widgets['send_btn']
        self.clear_log_btn = self.right_widgets['clear_log_btn']
        self.save_log_btn = self.right_widgets['save_log_btn']

    def connectSignals(self):
        """连接信号和槽"""
        # 左侧面板信号
        self.scan_btn.clicked.connect(self.controller.startScan)
        self.stop_scan_btn.clicked.connect(self.controller.stopScan)
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

        # BLE控制器信号
        self.controller.deviceFound.connect(self.on_device_found)
        self.controller.scanningChanged.connect(self.on_scanning_changed)
        self.controller.connectedChanged.connect(self.on_connected_changed)
        self.controller.statusChanged.connect(self.on_status_changed)
        self.controller.logMessage.connect(self.on_log_message)

    # 槽函数实现
    @pyqtSlot(str, str, int)
    def on_device_found(self, name, address, rssi):
        """发现设备槽函数"""
        self.device_list.add_device(name, address, rssi)

    @pyqtSlot(bool)
    def on_scanning_changed(self, scanning):
        """扫描状态变化槽函数"""
        self.scan_btn.setEnabled(not scanning)
        self.stop_scan_btn.setEnabled(scanning)
        if scanning:
            self.device_list.clear()

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