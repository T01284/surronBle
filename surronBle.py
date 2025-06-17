import sys
import asyncio
import time
import os
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QListWidget, \
    QTextEdit, QLineEdit, QLabel, QGroupBox, QListWidgetItem, QFileDialog, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread, QTimer, Qt
from PyQt6.QtGui import QFont, QPalette
import threading

try:
    from bleak import BleakScanner, BleakClient

    BLEAK_AVAILABLE = True
except ImportError:
    print("警告: bleak库未安装，请运行: pip install bleak")
    BLEAK_AVAILABLE = False

# AT命令服务和特征UUID
AT_SERVICE_UUID = "00006E50-0000-1000-8000-00805F9B34FB"
AT_TX_CHAR_UUID = "00006E51-0000-1000-8000-00805F9B34FB"
AT_RX_CHAR_UUID = "00006E52-0000-1000-8000-00805F9B34FB"


class BLEController(QObject):
    """BLE控制器"""

    # 信号定义
    deviceFound = pyqtSignal(str, str, int)  # name, address, rssi
    scanningChanged = pyqtSignal(bool)
    connectedChanged = pyqtSignal(bool)
    statusChanged = pyqtSignal(str)
    logMessage = pyqtSignal(str, str)  # message, type

    def __init__(self):
        super().__init__()
        self._scanning = False
        self._connected = False
        self._status = "就绪"
        self.client = None
        self.loop = None
        self.devices = {}
        self._shutdown = False  # 添加关闭标志
        self.rx_char = None  # 存储RX特征对象
        self.tx_char = None  # 存储TX特征对象

        if BLEAK_AVAILABLE:
            # 启动事件循环线程
            self.loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
            self.loop_thread.start()
        else:
            self.logMessage.emit("bleak库未安装，功能受限", "error")

    def _run_event_loop(self):
        """运行异步事件循环"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        except Exception as e:
            if not self._shutdown:
                print(f"事件循环异常: {e}")

    def shutdown(self):
        """关闭控制器"""
        self._shutdown = True
        if self.loop and not self.loop.is_closed():
            # 在事件循环中执行清理
            asyncio.run_coroutine_threadsafe(self._cleanup(), self.loop)
            # 停止事件循环
            self.loop.call_soon_threadsafe(self.loop.stop)

    async def _cleanup(self):
        """异步清理资源"""
        try:
            if self.client and self._connected:
                if self.rx_char:
                    try:
                        await self.client.stop_notify(self.rx_char)
                    except Exception:
                        pass
                await self.client.disconnect()
        except Exception as e:
            print(f"清理资源时出错: {e}")
        finally:
            self.client = None
            self.rx_char = None
            self.tx_char = None

    @pyqtSlot()
    def startScan(self):
        """开始扫描"""
        if not BLEAK_AVAILABLE:
            self.logMessage.emit("bleak库未安装，无法扫描", "error")
            return

        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._scan_devices(), self.loop)

    @pyqtSlot()
    def stopScan(self):
        """停止扫描"""
        self._scanning = False
        self.scanningChanged.emit(False)

    @pyqtSlot(str)
    def connectDevice(self, address):
        """连接设备"""
        if not BLEAK_AVAILABLE:
            self.logMessage.emit("bleak库未安装，无法连接", "error")
            return

        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._connect_device(address), self.loop)

    @pyqtSlot()
    def disconnectDevice(self):
        """断开连接"""
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._disconnect_device(), self.loop)

    @pyqtSlot(str)
    def sendCommand(self, command):
        """发送AT命令"""
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._send_command(command), self.loop)

    async def _scan_devices(self):
        """异步扫描设备"""
        try:
            self._scanning = True
            self.scanningChanged.emit(True)
            self._status = "扫描中..."
            self.statusChanged.emit(self._status)
            self.logMessage.emit("开始扫描Surron设备...", "info")
            self.devices.clear()

            def detection_callback(device, advertisement_data):
                if self._scanning and not self._shutdown:
                    name = device.name if device.name else "Unknown"
                    address = device.address
                    rssi = advertisement_data.rssi

                    self.devices[address] = (name, rssi)

                    # 只发送surron设备到界面
                    if name.lower().startswith('surron-'):
                        self.deviceFound.emit(name, address, rssi)

            scanner = BleakScanner(detection_callback)
            await scanner.start()
            await asyncio.sleep(10)  # 扫描10秒
            await scanner.stop()

            if not self._shutdown:
                self._scanning = False
                self.scanningChanged.emit(False)
                device_count = len([d for d in self.devices.values() if d[0].lower().startswith('surron-')])
                self._status = f"扫描完成，发现 {device_count} 个Surron设备"
                self.statusChanged.emit(self._status)
                self.logMessage.emit(f"扫描完成，发现 {device_count} 个Surron设备", "success")

        except Exception as e:
            if not self._shutdown:
                self._scanning = False
                self.scanningChanged.emit(False)
                self._status = "扫描失败"
                self.statusChanged.emit(self._status)
                self.logMessage.emit(f"扫描失败: {str(e)}", "error")

    async def _connect_device(self, address):
        """异步连接设备"""
        try:
            if self._shutdown:
                return

            self._status = "连接中..."
            self.statusChanged.emit(self._status)
            self.logMessage.emit(f"正在连接 {address}...", "info")

            self.client = BleakClient(address)
            await self.client.connect()

            if not self.client.is_connected:
                self._status = "连接失败"
                self.statusChanged.emit(self._status)
                self.logMessage.emit("连接失败", "error")
                return

            # 检查服务
            services = await self.client.get_services()
            at_service = None

            for service in services:
                if service.uuid.upper() == AT_SERVICE_UUID.upper():
                    at_service = service
                    break

            if not at_service:
                await self.client.disconnect()
                self._status = "设备不支持AT服务"
                self.statusChanged.emit(self._status)
                self.logMessage.emit(f"设备不支持AT服务 ({AT_SERVICE_UUID})", "error")
                return

            # 检查特征
            tx_char = None
            rx_char = None

            for char in at_service.characteristics:
                if char.uuid.upper() == AT_TX_CHAR_UUID.upper():
                    tx_char = char
                    self.tx_char = char  # 保存引用
                elif char.uuid.upper() == AT_RX_CHAR_UUID.upper():
                    rx_char = char
                    self.rx_char = char  # 保存引用

            if not tx_char or not rx_char:
                await self.client.disconnect()
                self._status = "设备特征不完整"
                self.statusChanged.emit(self._status)
                self.logMessage.emit("设备缺少必要的AT特征", "error")
                return

            # 启用通知
            try:
                await self.client.start_notify(self.rx_char, self._notification_handler)
                self.logMessage.emit("通知已启用", "success")

                # 测试通知是否工作
                print(f"RX特征: {self.rx_char.uuid}, 属性: {self.rx_char.properties}")
                print(f"TX特征: {self.tx_char.uuid}, 属性: {self.tx_char.properties}")

            except Exception as e:
                self.logMessage.emit(f"启用通知失败: {e}", "error")
                # 即使通知失败也继续连接，某些设备可能不支持通知
                print(f"通知启用失败: {e}")

            if not self._shutdown:
                self._connected = True
                self.connectedChanged.emit(True)
                self._status = f"已连接到 {address}"
                self.statusChanged.emit(self._status)
                self.logMessage.emit(f"成功连接到 {address}", "success")

                # 显示设备信息
                self._log_device_info(services)

        except Exception as e:
            if not self._shutdown:
                self._status = "连接失败"
                self.statusChanged.emit(self._status)
                self.logMessage.emit(f"连接失败: {str(e)}", "error")

            # 清理客户端
            if self.client:
                try:
                    if self.client.is_connected:
                        await self.client.disconnect()
                except Exception:
                    pass
                finally:
                    self.client = None

    async def _disconnect_device(self):
        """异步断开连接"""
        try:
            if self.client:
                # 先更新连接状态，避免重复调用
                if self._connected:
                    self._connected = False
                    if not self._shutdown:
                        self.connectedChanged.emit(False)

                # 检查客户端是否还连接着
                if hasattr(self.client, 'is_connected'):
                    try:
                        is_connected = self.client.is_connected
                    except Exception:
                        is_connected = False
                else:
                    is_connected = False

                # 停止通知
                if is_connected and self.rx_char:
                    try:
                        await self.client.stop_notify(self.rx_char)
                        if not self._shutdown:
                            self.logMessage.emit("已停止通知", "info")
                    except Exception as e:
                        if not self._shutdown:
                            self.logMessage.emit(f"停止通知失败: {e}", "warning")

                # 断开连接
                if is_connected:
                    try:
                        await self.client.disconnect()
                        if not self._shutdown:
                            self.logMessage.emit("BLE连接已断开", "info")
                    except Exception as e:
                        if not self._shutdown:
                            self.logMessage.emit(f"断开连接失败: {e}", "warning")

                # 更新状态
                if not self._shutdown:
                    self._status = "已断开连接"
                    self.statusChanged.emit(self._status)
                    self.logMessage.emit("设备已断开连接", "success")

        except Exception as e:
            if not self._shutdown:
                self.logMessage.emit(f"断开连接时出现异常: {str(e)}", "error")
        finally:
            # 确保清理所有引用
            self.client = None
            self.rx_char = None
            self.tx_char = None
            # 确保状态正确
            if not self._shutdown:
                self._connected = False
                self.connectedChanged.emit(False)

    async def _send_command(self, command):
        """异步发送命令"""
        if not self.client or not self._connected:
            self.logMessage.emit("设备未连接", "error")
            return

        if not self.tx_char:
            self.logMessage.emit("TX特征不可用", "error")
            return

        try:
            # 先记录发送的命令
            display_cmd = command.strip()
            self.logMessage.emit(f"→ {display_cmd}", "sent")

            # 准备发送的数据
            if not command.endswith('\r\n'):
                if not command.endswith('\r') and not command.endswith('\n'):
                    command += '\r\n'

            data = command.encode('utf-8')
            print(f"发送数据: {data} (长度: {len(data)})")

            # 发送数据
            await self.client.write_gatt_char(self.tx_char, data)
            print(f"数据发送成功")

            # 稍微延迟，给设备响应时间
            await asyncio.sleep(0.1)

        except Exception as e:
            print(f"发送失败: {e}")
            self.logMessage.emit(f"发送失败: {str(e)}", "error")

    def _notification_handler(self, sender, data):
        """通知处理函数"""
        try:
            if self._shutdown:
                return

            # 先打印原始数据用于调试
            print(f"收到原始数据: {data} (长度: {len(data)})")

            # 尝试多种解码方式
            text = ""
            try:
                text = data.decode('utf-8', errors='ignore')
            except:
                try:
                    text = data.decode('ascii', errors='ignore')
                except:
                    # 如果解码失败，显示十六进制
                    text = data.hex()

            print(f"解码后文本: '{text}'")

            if text:
                # 处理多行数据 - 按行分割并逐行显示
                lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')

                for line in lines:
                    line = line.strip()
                    if line:  # 只显示非空行
                        self.logMessage.emit(f"← {line}", "received")

            elif len(data) > 0:
                # 如果有数据但解码为空，显示十六进制
                hex_str = ' '.join([f'{b:02X}' for b in data])
                self.logMessage.emit(f"← [HEX: {hex_str}]", "received")

        except Exception as e:
            if not self._shutdown:
                print(f"通知处理异常: {e}")
                self.logMessage.emit(f"数据处理错误: {str(e)}", "error")

    def _log_device_info(self, services):
        """记录设备信息"""

        def log_info():
            if self._shutdown:
                return

            time.sleep(0.5)
            if not self._shutdown:
                self.logMessage.emit("=== 设备信息 ===", "info")
                for service in services:
                    if self._shutdown:
                        break
                    self.logMessage.emit(f"服务: {service.uuid}", "info")
                    for char in service.characteristics:
                        if self._shutdown:
                            break
                        props = ', '.join(char.properties)
                        self.logMessage.emit(f"  特征: {char.uuid} ({props})", "info")

        threading.Thread(target=log_info, daemon=True).start()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.controller = BLEController()
        self.selected_address = ""
        self.log_content = []  # 存储日志内容
        self.setupUI()
        self.connectSignals()

    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            print("开始关闭应用...")
            # 设置关闭标志
            self.controller._shutdown = True

            # 如果有连接，先断开
            if self.controller._connected:
                # 使用同步方式强制断开
                try:
                    if self.controller.client:
                        import asyncio
                        if self.controller.loop and not self.controller.loop.is_closed():
                            future = asyncio.run_coroutine_threadsafe(
                                self.controller._disconnect_device(),
                                self.controller.loop
                            )
                            # 等待最多2秒
                            try:
                                future.result(timeout=2.0)
                            except:
                                pass
                except Exception as e:
                    print(f"强制断开连接失败: {e}")

            # 停止事件循环
            if self.controller.loop and not self.controller.loop.is_closed():
                self.controller.loop.call_soon_threadsafe(self.controller.loop.stop)

            print("应用关闭完成")
        except Exception as e:
            print(f"关闭时出错: {e}")
        finally:
            event.accept()

    def setupUI(self):
        """设置用户界面"""
        self.setWindowTitle("Surron故障日志读取测试工具")
        self.setGeometry(100, 100, 1200, 800)

        # 设置样式
        self.setStyleSheet("""
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
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 应用程序标题
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
        main_layout.addWidget(title_label)

        # 内容布局
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # 左侧面板 - 设备扫描
        left_panel = QGroupBox("设备扫描")
        left_panel.setMaximumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(12)
        left_layout.setContentsMargins(15, 25, 15, 15)

        # 扫描控制
        scan_layout = QHBoxLayout()
        self.scan_btn = QPushButton("开始扫描")
        self.stop_scan_btn = QPushButton("停止扫描")
        self.stop_scan_btn.setObjectName("stopButton")
        self.stop_scan_btn.setEnabled(False)
        scan_layout.addWidget(self.scan_btn)
        scan_layout.addWidget(self.stop_scan_btn)
        left_layout.addLayout(scan_layout)

        # 设备列表
        device_label = QLabel("发现的Surron设备 (双击连接):")
        device_label.setStyleSheet("margin-top: 5px; margin-bottom: 2px;")
        left_layout.addWidget(device_label)

        self.device_list = QListWidget()
        self.device_list.setMinimumHeight(300)
        left_layout.addWidget(self.device_list)

        # 连接控制
        connect_layout = QHBoxLayout()
        self.connect_btn = QPushButton("连接设备")
        self.connect_btn.setObjectName("connectButton")
        self.disconnect_btn = QPushButton("断开连接")
        self.disconnect_btn.setObjectName("disconnectButton")
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(False)
        connect_layout.addWidget(self.connect_btn)
        connect_layout.addWidget(self.disconnect_btn)
        left_layout.addLayout(connect_layout)

        # 连接状态
        self.status_label = QLabel("状态: 就绪")
        self.status_label.setObjectName("statusLabel")
        left_layout.addWidget(self.status_label)

        # 右侧面板 - AT通讯
        right_panel = QGroupBox("AT命令控制台")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(12)
        right_layout.setContentsMargins(15, 25, 15, 15)

        # 预设AT命令
        preset_label = QLabel("快捷命令:")
        preset_label.setStyleSheet("margin-bottom: 5px;")
        right_layout.addWidget(preset_label)

        preset_layout = QHBoxLayout()
        preset_commands = [
            ("读取5条", "AT+LOGLATEST=5"),
            ("获取状态", "AT+LOGSTATUS"),
            ("系统信息", "AT+LOGSTATS"),
            ("日志统计", "AT+LOGCOUNT"),
            ("清除日志", "AT+LOGCLEAR")
        ]

        for name, cmd in preset_commands:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, c=cmd: self.send_preset_command(c))
            preset_layout.addWidget(btn)

        right_layout.addLayout(preset_layout)

        # 命令输入
        cmd_label = QLabel("手动输入AT命令:")
        cmd_label.setStyleSheet("margin-top: 5px; margin-bottom: 2px;")
        right_layout.addWidget(cmd_label)

        cmd_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("输入AT命令...")
        self.send_btn = QPushButton("发送")
        self.send_btn.setEnabled(False)
        cmd_layout.addWidget(self.cmd_input)
        cmd_layout.addWidget(self.send_btn)
        right_layout.addLayout(cmd_layout)

        # 通讯日志
        log_label = QLabel("通讯日志:")
        log_label.setStyleSheet("margin-top: 8px; margin-bottom: 2px;")
        right_layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        right_layout.addWidget(self.log_text)

        # 控制按钮
        control_layout = QHBoxLayout()
        self.clear_log_btn = QPushButton("清除日志")
        self.save_log_btn = QPushButton("保存日志")
        self.save_log_btn.setObjectName("saveLogButton")
        control_layout.addWidget(self.clear_log_btn)
        control_layout.addWidget(self.save_log_btn)
        control_layout.addStretch()
        right_layout.addLayout(control_layout)

        # 添加面板到内容布局
        content_layout.addWidget(left_panel)
        content_layout.addWidget(right_panel)

        # 添加内容布局到主布局
        main_layout.addLayout(content_layout)

        # 底部说明文字
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
        main_layout.addWidget(footer_label)

    def connectSignals(self):
        """连接信号"""
        # 按钮信号
        self.scan_btn.clicked.connect(self.controller.startScan)
        self.stop_scan_btn.clicked.connect(self.controller.stopScan)
        self.connect_btn.clicked.connect(self.connect_device)
        self.disconnect_btn.clicked.connect(self.controller.disconnectDevice)
        self.send_btn.clicked.connect(self.send_command)
        self.cmd_input.returnPressed.connect(self.send_command)
        self.clear_log_btn.clicked.connect(self.clear_log)
        self.save_log_btn.clicked.connect(self.save_log)

        # 设备列表信号
        self.device_list.itemClicked.connect(self.on_device_selected)
        self.device_list.itemDoubleClicked.connect(self.on_device_double_clicked)

        # 控制器信号
        self.controller.deviceFound.connect(self.on_device_found)
        self.controller.scanningChanged.connect(self.on_scanning_changed)
        self.controller.connectedChanged.connect(self.on_connected_changed)
        self.controller.statusChanged.connect(self.on_status_changed)
        self.controller.logMessage.connect(self.on_log_message)

    def on_device_found(self, name, address, rssi):
        """发现设备"""
        # 检查是否已存在
        for i in range(self.device_list.count()):
            item = self.device_list.item(i)
            if item.data(1) == address:
                # 更新现有项
                item.setText(f"{name}\n{address}\nRSSI: {rssi} dBm")
                return

        # 添加新项
        item = QListWidgetItem(f"{name}\n{address}\nRSSI: {rssi} dBm")
        item.setData(1, address)  # 存储地址
        self.device_list.addItem(item)

    def on_scanning_changed(self, scanning):
        """扫描状态变化"""
        self.scan_btn.setEnabled(not scanning)
        self.stop_scan_btn.setEnabled(scanning)
        if scanning:
            self.device_list.clear()

    def on_connected_changed(self, connected):
        """连接状态变化"""
        self.connect_btn.setEnabled(not connected and self.selected_address)
        self.disconnect_btn.setEnabled(connected)
        self.send_btn.setEnabled(connected)

        # 更新状态标签样式
        if connected:
            self.status_label.setObjectName("statusConnected")
        else:
            self.status_label.setObjectName("statusLabel")
        self.status_label.setStyle(self.status_label.style())  # 刷新样式

    def on_status_changed(self, status):
        """状态变化"""
        self.status_label.setText(f"状态: {status}")

    def on_log_message(self, message, msg_type):
        """日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")

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

        self.log_text.append(html_msg)

        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_device_selected(self, item):
        """选择设备"""
        self.selected_address = item.data(1)
        self.connect_btn.setEnabled(not self.controller._connected)

    def on_device_double_clicked(self, item):
        """双击设备进行连接"""
        if not self.controller._connected:
            self.selected_address = item.data(1)
            self.connect_device()

    def connect_device(self):
        """连接设备"""
        if self.selected_address:
            self.controller.connectDevice(self.selected_address)

    def send_command(self):
        """发送命令"""
        command = self.cmd_input.text().strip()
        if command:
            self.controller.sendCommand(command)
            self.cmd_input.clear()

    def send_preset_command(self, command):
        """发送预设命令"""
        self.controller.sendCommand(command)

    def clear_log(self):
        """清除日志"""
        self.log_text.clear()
        self.log_content.clear()

    def save_log(self):
        """保存日志到文件"""
        if not self.log_content:
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

                    for log_line in self.log_content:
                        f.write(log_line + "\n")

                QMessageBox.information(self, "成功", f"日志已保存到:\n{filename}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存日志失败:\n{str(e)}")


def main():
    """主函数"""
    print("=== BLE AT通讯工具 ===")
    print("依赖库安装:")
    print("pip install PyQt6 bleak")
    print("========================")

    if not BLEAK_AVAILABLE:
        print("错误: 请先安装bleak库")
        print("运行: pip install bleak")

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    try:
        return app.exec()
    except KeyboardInterrupt:
        print("程序被用户中断")
        return 0


if __name__ == "__main__":
    sys.exit(main())