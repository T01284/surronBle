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
        self._shutdown = False
        self.rx_char = None
        self.tx_char = None
        self._scanner = None
        self._disconnect_lock = threading.Lock()  # 添加断开连接锁

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
                        future.result(timeout=5.0)  # 增加到5秒超时
                    except Exception as e:
                        print(f"异步清理失败: {e}")
                        # 如果异步清理失败，尝试同步清理
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
                # 确保所有引用都被清理
                self._cleanup_sync()
                print("BLE控制器关闭完成")

    async def _cleanup_async(self):
        """异步清理资源"""
        try:
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
            print("同步清理完成")
        except Exception as e:
            print(f"同步清理失败: {e}")

    def startScan(self):
        """开始扫描设备"""
        if not BLEAK_AVAILABLE or self._shutdown:
            self.logMessage.emit("无法扫描设备", "error")
            return

        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._scan_devices(), self.loop)

    def stopScan(self):
        """停止扫描设备"""
        self._scanning = False
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._stop_scanning(), self.loop)

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

    async def _scan_devices(self):
        """异步扫描设备实现"""
        if self._scanning or self._shutdown:
            return

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

            self._scanner = BleakScanner(detection_callback)
            await self._scanner.start()

            # 扫描10秒
            scan_time = 0
            while scan_time < 10 and self._scanning and not self._shutdown:
                await asyncio.sleep(0.1)
                scan_time += 0.1

            await self._scanner.stop()
            self._scanner = None

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
        finally:
            self._scanner = None

    async def _stop_scanning(self):
        """停止扫描的异步实现"""
        try:
            if self._scanner:
                await self._scanner.stop()
                self._scanner = None
            self.scanningChanged.emit(False)
        except Exception as e:
            print(f"停止扫描失败: {e}")

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
                self._status = f"已连接到 {address}"
                self.statusChanged.emit(self._status)
                self.logMessage.emit(f"成功连接到 {address}", "success")

                # 记录设备信息
                services = await self.client.get_services()
                self._log_device_info(services)

        except Exception as e:
            if not self._shutdown:
                self._status = "连接失败"
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
            # 某些设备可能不支持通知，继续连接

    async def _disconnect_device(self):
        """安全断开设备连接"""
        # 使用锁防止重复断开，但要小心死锁
        if not self._disconnect_lock.acquire(blocking=False):
            # 如果无法获取锁，说明正在进行断开操作
            print("断开连接操作正在进行中...")
            return

        try:
            if not self._connected and not self.client:
                return

            # 立即更新状态
            was_connected = self._connected
            self._connected = False

            if was_connected and not self._shutdown:
                self.connectedChanged.emit(False)

            if self.client:
                try:
                    # 检查连接状态，添加异常处理
                    is_connected = False
                    try:
                        is_connected = getattr(self.client, 'is_connected', False)
                        if callable(is_connected):
                            is_connected = is_connected()
                    except Exception as e:
                        print(f"检查连接状态失败: {e}")
                        is_connected = False

                    # 停止通知
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

                    # 断开连接
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
                self._status = "已断开连接"
                self.statusChanged.emit(self._status)
                self.logMessage.emit("设备已断开连接", "success")

        except Exception as e:
            if not self._shutdown:
                self.logMessage.emit(f"断开连接异常: {str(e)}", "error")
                print(f"断开连接异常: {e}")
        finally:
            # 确保清理完成
            try:
                await self._cleanup_connection()
            except:
                pass
            # 释放锁
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
            # 记录发送的命令
            display_cmd = command.strip()
            self.logMessage.emit(f"→ {display_cmd}", "sent")

            # 准备数据
            if not command.endswith('\r\n'):
                if not command.endswith('\r') and not command.endswith('\n'):
                    command += '\r\n'

            data = command.encode('utf-8')

            # 发送数据
            await asyncio.wait_for(
                self.client.write_gatt_char(self.tx_char, data),
                timeout=5.0
            )

            # 给设备响应时间
            await asyncio.sleep(0.1)

        except Exception as e:
            if not self._shutdown:
                self.logMessage.emit(f"发送失败: {str(e)}", "error")

    def _notification_handler(self, sender, data):
        """BLE通知处理函数"""
        if self._shutdown:
            return

        try:
            # 解码数据
            text = ""
            try:
                text = data.decode('utf-8', errors='ignore')
            except:
                try:
                    text = data.decode('ascii', errors='ignore')
                except:
                    text = data.hex()

            if text:
                # 处理多行数据
                lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
                for line in lines:
                    line = line.strip()
                    if line:
                        self.logMessage.emit(f"← {line}", "received")
            elif len(data) > 0:
                # 显示十六进制数据
                hex_str = ' '.join([f'{b:02X}' for b in data])
                self.logMessage.emit(f"← [HEX: {hex_str}]", "received")

        except Exception as e:
            if not self._shutdown:
                print(f"通知处理异常: {e}")

    def _log_device_info(self, services):
        """异步记录设备信息"""

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