import asyncio
import threading
import time
from PyQt6.QtCore import QObject, pyqtSignal

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
    """BLE控制器 - 负责蓝牙低功耗设备的扫描、连接和通讯"""

    # 信号定义
    deviceFound = pyqtSignal(str, str, int)  # name, address, rssi
    deviceLost = pyqtSignal(str)  # address - 设备离线信号
    scanningChanged = pyqtSignal(bool)
    connectedChanged = pyqtSignal(bool)
    statusChanged = pyqtSignal(str)
    logMessage = pyqtSignal(str, str)  # message, type

    def __init__(self):
        super().__init__()
        self._scanning = False
        self._continuous_scanning = False
        self._connected = False
        self._status = "就绪"
        self.client = None
        self.loop = None
        self.devices = {}
        self.device_last_seen = {}  # 记录设备最后被发现的时间
        self._shutdown = False
        self.rx_char = None
        self.tx_char = None
        self._scanner = None
        self._disconnect_lock = threading.Lock()
        self._scan_task = None
        self._cleanup_task = None

        if BLEAK_AVAILABLE:
            self._start_event_loop()
        else:
            self.logMessage.emit("bleak库未安装，功能受限", "error")

    def _start_event_loop(self):
        """启动异步事件循环"""
        try:
            self.loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
            self.loop_thread.start()
            # 等待循环启动
            time.sleep(0.1)
            # 启动持续扫描
            self.startContinuousScanning()
        except Exception as e:
            print(f"启动事件循环失败: {e}")

    def _run_event_loop(self):
        """运行异步事件循环"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        except Exception as e:
            if not self._shutdown:
                print(f"事件循环异常: {e}")
        finally:
            print("事件循环已停止")

    def shutdown(self):
        """安全关闭控制器"""
        if self._shutdown:
            return

        print("开始关闭BLE控制器...")
        self._shutdown = True
        self._continuous_scanning = False

        # 使用锁确保断开连接的原子性
        with self._disconnect_lock:
            try:
                # 停止扫描
                self._scanning = False

                # 断开连接
                if self.loop and not self.loop.is_closed():
                    try:
                        # 在事件循环中执行清理，设置超时
                        future = asyncio.run_coroutine_threadsafe(
                            self._cleanup_async(), self.loop
                        )
                        future.result(timeout=5.0)
                    except Exception as e:
                        print(f"异步清理失败: {e}")
                        self._cleanup_sync()

                    # 停止事件循环
                    try:
                        if not self.loop.is_closed():
                            self.loop.call_soon_threadsafe(self.loop.stop)
                    except Exception as e:
                        print(f"停止事件循环失败: {e}")

            except Exception as e:
                print(f"关闭控制器时出错: {e}")
            finally:
                self._cleanup_sync()
                print("BLE控制器关闭完成")

    async def _cleanup_async(self):
        """异步清理资源"""
        try:
            # 取消持续扫描任务
            if self._scan_task:
                self._scan_task.cancel()
                try:
                    await self._scan_task
                except asyncio.CancelledError:
                    pass
                self._scan_task = None

            # 取消清理任务
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
                self._cleanup_task = None

            # 停止扫描
            if self._scanner:
                try:
                    await self._scanner.stop()
                except Exception as e:
                    print(f"停止扫描器失败: {e}")
                finally:
                    self._scanner = None

            # 断开BLE连接
            if self.client:
                try:
                    if hasattr(self.client, 'is_connected') and self.client.is_connected:
                        # 停止通知
                        if self.rx_char:
                            try:
                                await asyncio.wait_for(
                                    self.client.stop_notify(self.rx_char),
                                    timeout=2.0
                                )
                            except Exception as e:
                                print(f"停止通知失败: {e}")

                        # 断开连接
                        await asyncio.wait_for(
                            self.client.disconnect(),
                            timeout=2.0
                        )
                        print("BLE连接已断开")
                except Exception as e:
                    print(f"断开BLE连接失败: {e}")
                finally:
                    self.client = None

        except Exception as e:
            print(f"异步清理资源时出错: {e}")

    def _cleanup_sync(self):
        """同步清理资源"""
        try:
            self.client = None
            self.rx_char = None
            self.tx_char = None
            self._scanner = None
            self._connected = False
            self._scanning = False
            self._continuous_scanning = False
            self._scan_task = None
            self._cleanup_task = None
            print("同步清理完成")
        except Exception as e:
            print(f"同步清理失败: {e}")

    def startContinuousScanning(self):
        """开始持续扫描"""
        if not BLEAK_AVAILABLE or self._shutdown or self._continuous_scanning:
            return

        self._continuous_scanning = True
        if self.loop and not self.loop.is_closed():
            self._scan_task = asyncio.run_coroutine_threadsafe(
                self._continuous_scan_loop(), self.loop
            )
            self._cleanup_task = asyncio.run_coroutine_threadsafe(
                self._device_cleanup_loop(), self.loop
            )

    def stopContinuousScanning(self):
        """停止持续扫描"""
        self._continuous_scanning = False
        self._scanning = False

    def connectDevice(self, address):
        """连接指定地址的设备"""
        if not BLEAK_AVAILABLE or self._shutdown:
            self.logMessage.emit("无法连接设备", "error")
            return

        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._connect_device(address), self.loop)

    def disconnectDevice(self):
        """断开当前连接"""
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._disconnect_device(), self.loop)

    def sendCommand(self, command):
        """发送AT命令"""
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._send_command(command), self.loop)

    async def _continuous_scan_loop(self):
        """持续扫描循环"""
        self.logMessage.emit("开始持续扫描设备...", "info")
        self._status = "持续扫描中..."
        self.statusChanged.emit(self._status)

        while self._continuous_scanning and not self._shutdown:
            try:
                if not self._scanning:
                    await self._start_single_scan()

                # 短暂等待后继续下一轮扫描
                await asyncio.sleep(1.0)

            except Exception as e:
                if not self._shutdown:
                    print(f"持续扫描异常: {e}")
                    await asyncio.sleep(5.0)  # 出错时等待更长时间

        if not self._shutdown:
            self.logMessage.emit("持续扫描已停止", "info")

    async def _start_single_scan(self):
        """执行单次扫描"""
        if self._scanning or self._shutdown:
            return

        try:
            self._scanning = True
            self.scanningChanged.emit(True)

            def detection_callback(device, advertisement_data):
                if not self._shutdown:
                    name = device.name if device.name else "Unknown"
                    address = device.address
                    rssi = advertisement_data.rssi
                    current_time = time.time()

                    # 更新设备信息
                    self.devices[address] = (name, rssi)
                    self.device_last_seen[address] = current_time

                    # 只发送surron设备到界面
                    if name.lower().startswith('surron-'):
                        self.deviceFound.emit(name, address, rssi)

            self._scanner = BleakScanner(detection_callback)
            await self._scanner.start()

            # 扫描3秒
            scan_time = 0
            while scan_time < 3.0 and self._scanning and not self._shutdown:
                await asyncio.sleep(0.1)
                scan_time += 0.1

            await self._scanner.stop()
            self._scanner = None

        except Exception as e:
            if not self._shutdown:
                print(f"单次扫描失败: {e}")
        finally:
            self._scanning = False
            self.scanningChanged.emit(False)

    async def _device_cleanup_loop(self):
        """设备清理循环 - 移除长时间未见的设备"""
        while self._continuous_scanning and not self._shutdown:
            try:
                current_time = time.time()
                devices_to_remove = []

                # 检查哪些设备超过30秒未见
                for address, last_seen in self.device_last_seen.items():
                    if current_time - last_seen > 30.0:  # 30秒超时
                        devices_to_remove.append(address)

                # 移除超时的设备
                for address in devices_to_remove:
                    if address in self.devices:
                        device_name = self.devices[address][0]
                        if device_name.lower().startswith('surron-'):
                            self.deviceLost.emit(address)
                        del self.devices[address]
                    if address in self.device_last_seen:
                        del self.device_last_seen[address]

                # 每5秒检查一次
                await asyncio.sleep(5.0)

            except Exception as e:
                if not self._shutdown:
                    print(f"设备清理异常: {e}")
                await asyncio.sleep(5.0)

    async def _connect_device(self, address):
        """异步连接设备实现"""
        if self._shutdown or self._connected:
            return

        try:
            self._status = "连接中..."
            self.statusChanged.emit(self._status)
            self.logMessage.emit(f"正在连接 {address}...", "info")

            # 创建客户端并连接
            self.client = BleakClient(address)
            await asyncio.wait_for(self.client.connect(), timeout=10.0)

            if not self.client.is_connected:
                raise Exception("连接失败")

            # 验证服务和特征
            if not await self._verify_services():
                await self.client.disconnect()
                return

            # 启用通知
            await self._setup_notifications()

            if not self._shutdown:
                self._connected = True
                self.connectedChanged.emit(True)
                device_name = self.devices.get(address, ("Unknown", 0))[0]
                self._status = f"已连接到 {device_name} ({address})"
                self.statusChanged.emit(self._status)
                self.logMessage.emit(f"成功连接到 {device_name}", "success")

                # 记录设备信息
                services = await self.client.get_services()
                self._log_device_info(services)

        except Exception as e:
            if not self._shutdown:
                self._status = "连接失败，继续扫描中..."
                self.statusChanged.emit(self._status)
                self.logMessage.emit(f"连接失败: {str(e)}", "error")
            await self._cleanup_connection()

    async def _verify_services(self):
        """验证设备服务和特征"""
        try:
            services = await self.client.get_services()
            at_service = None

            for service in services:
                if service.uuid.upper() == AT_SERVICE_UUID.upper():
                    at_service = service
                    break

            if not at_service:
                self.logMessage.emit(f"设备不支持AT服务 ({AT_SERVICE_UUID})", "error")
                return False

            # 检查特征
            self.tx_char = None
            self.rx_char = None

            for char in at_service.characteristics:
                if char.uuid.upper() == AT_TX_CHAR_UUID.upper():
                    self.tx_char = char
                elif char.uuid.upper() == AT_RX_CHAR_UUID.upper():
                    self.rx_char = char

            if not self.tx_char or not self.rx_char:
                self.logMessage.emit("设备缺少必要的AT特征", "error")
                return False

            return True

        except Exception as e:
            self.logMessage.emit(f"验证服务失败: {e}", "error")
            return False

    async def _setup_notifications(self):
        """设置通知"""
        try:
            if self.rx_char:
                await self.client.start_notify(self.rx_char, self._notification_handler)
                self.logMessage.emit("通知已启用", "success")
        except Exception as e:
            self.logMessage.emit(f"启用通知失败: {e}", "warning")

    async def _disconnect_device(self):
        """安全断开设备连接"""
        if not self._disconnect_lock.acquire(blocking=False):
            print("断开连接操作正在进行中...")
            return

        try:
            if not self._connected and not self.client:
                return

            was_connected = self._connected
            self._connected = False

            if was_connected and not self._shutdown:
                self.connectedChanged.emit(False)

            if self.client:
                try:
                    is_connected = False
                    try:
                        is_connected = getattr(self.client, 'is_connected', False)
                        if callable(is_connected):
                            is_connected = is_connected()
                    except Exception as e:
                        print(f"检查连接状态失败: {e}")
                        is_connected = False

                    if is_connected and self.rx_char:
                        try:
                            await asyncio.wait_for(
                                self.client.stop_notify(self.rx_char),
                                timeout=2.0
                            )
                            if not self._shutdown:
                                self.logMessage.emit("已停止通知", "info")
                        except Exception as e:
                            if not self._shutdown:
                                print(f"停止通知失败: {e}")

                    if is_connected:
                        try:
                            await asyncio.wait_for(
                                self.client.disconnect(),
                                timeout=3.0
                            )
                            if not self._shutdown:
                                self.logMessage.emit("BLE连接已断开", "info")
                        except Exception as e:
                            if not self._shutdown:
                                print(f"断开连接失败: {e}")

                except Exception as e:
                    if not self._shutdown:
                        print(f"断开连接过程中出错: {e}")
                finally:
                    await self._cleanup_connection()

            if not self._shutdown:
                self._status = "已断开连接，继续扫描中..."
                self.statusChanged.emit(self._status)
                self.logMessage.emit("设备已断开连接", "success")

        except Exception as e:
            if not self._shutdown:
                self.logMessage.emit(f"断开连接异常: {str(e)}", "error")
                print(f"断开连接异常: {e}")
        finally:
            try:
                await self._cleanup_connection()
            except:
                pass
            self._disconnect_lock.release()

    async def _cleanup_connection(self):
        """清理连接相关资源"""
        try:
            self.client = None
            self.rx_char = None
            self.tx_char = None
            self._connected = False
        except Exception as e:
            print(f"清理连接资源失败: {e}")

    async def _send_command(self, command):
        """异步发送命令实现"""
        if not self.client or not self._connected or self._shutdown:
            self.logMessage.emit("设备未连接", "error")
            return

        if not self.tx_char:
            self.logMessage.emit("TX特征不可用", "error")
            return

        try:
            display_cmd = command.strip()
            self.logMessage.emit(f"→ {display_cmd}", "sent")

            if not command.endswith('\r\n'):
                if not command.endswith('\r') and not command.endswith('\n'):
                    command += '\r\n'

            data = command.encode('utf-8')

            await asyncio.wait_for(
                self.client.write_gatt_char(self.tx_char, data),
                timeout=5.0
            )

            await asyncio.sleep(0.1)

        except Exception as e:
            if not self._shutdown:
                self.logMessage.emit(f"发送失败: {str(e)}", "error")

    def _notification_handler(self, sender, data):
        """BLE通知处理函数"""
        if self._shutdown:
            return

        try:
            text = ""
            try:
                text = data.decode('utf-8', errors='ignore')
            except:
                try:
                    text = data.decode('ascii', errors='ignore')
                except:
                    text = data.hex()

            if text:
                lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
                for line in lines:
                    line = line.strip()
                    if line:
                        self.logMessage.emit(f"← {line}", "received")
            elif len(data) > 0:
                hex_str = ' '.join([f'{b:02X}' for b in data])
                self.logMessage.emit(f"← [HEX: {hex_str}]", "received")

        except Exception as e:
            if not self._shutdown:
                print(f"通知处理异常: {e}")

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