"""有方機器人 NeZha（哪吒）總線驅動板 I2C 驅動。

協定來源：`vendor/yourfun-nezha/sdk/` 的原廠 STM32／Arduino 驅動庫，
完整說明見 `docs/hardware/nezha-i2c-protocol.md`。

驅動板是 I2C slave，7-bit 位址 `0x40`（原廠 `NEZHA_ADDR 0x80` 是 8-bit 寫入位址）。
所有指令都先寫命令暫存器 `0x00`，需要帶參數的再補一個資料 frame ——
這個「兩次傳輸」的順序是照原廠實作複製的，不要自作聰明合併成一次。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from smbus2 import SMBus

DEFAULT_ADDRESS = 0x40
DEFAULT_BUS = 1

# 命令暫存器：所有指令都先寫進這裡
REG_COMMAND = 0x00

CMD_MOTOR_INIT = 0x01
CMD_MOTOR_SET = (0x05, 0x09, 0x0D, 0x11)
CMD_ENCODER_INIT = (0x15, 0x18, 0x1B, 0x1E)
CMD_ENCODER_READ = (0x16, 0x19, 0x1C, 0x1F)
CMD_SERVO_INIT = (0x21, 0x24, 0x27, 0x2A)
CMD_SERVO_SET = (0x22, 0x25, 0x28, 0x2B)
CMD_RESET = 0xFF

CMD_LED = {
    # 名稱: (開, 關, 翻轉)
    "head": (0x2D, 0x2E, 0x2F),
    "tail_left": (0x30, 0x31, 0x32),
    "tail_right": (0x33, 0x34, 0x35),
    "ambient": (0x36, 0x37, 0x38),
}

MAX_SPEED = 1000
SERVO_PWM_MIN = 50
SERVO_PWM_MAX = 250

# 原廠標註「不可去掉」的上電延時
RESET_DELAY_S = 0.1
INIT_DELAY_S = 0.5

# 手冊 P.13 說 motor_a 是正轉，原廠程式碼註解說 motor_b 是正轉 —— 兩邊互相矛盾。
# 實測後把這個常數調成正確的值即可，其餘程式不用改。
# 詳見 docs/hardware/nezha-i2c-protocol.md「正反轉的矛盾」。
FORWARD_IS_MOTOR_A = True


class NeZhaError(RuntimeError):
    """與驅動板通訊失敗。"""


class NeZha:
    """NeZha 驅動板：4 顆馬達、4 個舵機、4 組燈、4 路編碼器。

    馬達與舵機的編號 `n` 都是 **1–4**，對應板子上絲印的 `M1`–`M4` 與 `S1`–`S4`。

    >>> with NeZha() as board:
    ...     board.motor(1, 300)
    ...     time.sleep(1)
    ...     board.stop()
    """

    def __init__(
        self,
        bus: int | SMBus = DEFAULT_BUS,
        address: int = DEFAULT_ADDRESS,
        *,
        init_motors: bool = True,
    ) -> None:
        if isinstance(bus, int):
            try:
                from smbus2 import SMBus
            except ImportError as exc:  # pragma: no cover - 只在非 Pi 環境觸發
                raise NeZhaError(
                    "需要 smbus2。在樹莓派上執行 `uv sync`，或傳入自備的 SMBus 物件。"
                ) from exc
            self._bus = SMBus(bus)
            self._owns_bus = True
        else:
            self._bus = bus
            self._owns_bus = False

        self.address = address
        time.sleep(INIT_DELAY_S)
        self.reset()
        if init_motors:
            self.init_motors()

    # ------------------------------------------------------------------ 低階
    def _command(self, command: int) -> None:
        """寫命令暫存器。對應原廠 `NeZha_WriteCommand()`。"""
        try:
            self._bus.write_byte_data(self.address, REG_COMMAND, command)
        except OSError as exc:
            raise NeZhaError(
                f"寫入指令 0x{command:02X} 失敗（位址 0x{self.address:02X}）。"
                " 檢查接線、供電，以及 I2C 速率是否超過 200kHz。"
            ) from exc

    def _command_with_data(self, command: int, data: list[int]) -> None:
        """先寫命令暫存器，再送資料 frame —— 原廠就是這樣分兩次送。"""
        self._command(command)
        try:
            self._bus.write_i2c_block_data(self.address, command, data)
        except OSError as exc:
            raise NeZhaError(f"送出指令 0x{command:02X} 的資料失敗。") from exc

    @staticmethod
    def _split_u16(value: int) -> list[int]:
        return [(value >> 8) & 0xFF, value & 0xFF]

    @staticmethod
    def _check_channel(n: int) -> int:
        if n not in (1, 2, 3, 4):
            raise ValueError(f"通道必須是 1–4，收到 {n}")
        return n - 1

    # ------------------------------------------------------------------ 基本
    def reset(self) -> None:
        self._command(CMD_RESET)
        time.sleep(RESET_DELAY_S)

    def init_motors(self) -> None:
        self._command(CMD_MOTOR_INIT)

    def close(self) -> None:
        """停掉所有馬達再關閉 bus。"""
        try:
            self.stop()
        finally:
            if self._owns_bus:
                self._bus.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # ------------------------------------------------------------------ 馬達
    def motor(self, n: int, speed: int) -> None:
        """設定 `Mn` 的速度。

        `speed` 範圍 −1000 到 1000，正值正轉、負值反轉、0 停止。
        絕對值即為 PWM 占空比的千分比（1000 = 100%）。
        """
        idx = self._check_channel(n)
        if not -MAX_SPEED <= speed <= MAX_SPEED:
            raise ValueError(f"速度必須在 −{MAX_SPEED}–{MAX_SPEED} 之間，收到 {speed}")

        # motor_a 與 motor_b 不可同時有值，原廠手冊列為無效組合
        forward, reverse = (abs(speed), 0) if speed >= 0 else (0, abs(speed))
        a, b = (forward, reverse) if FORWARD_IS_MOTOR_A else (reverse, forward)
        self._command_with_data(CMD_MOTOR_SET[idx], self._split_u16(a) + self._split_u16(b))

    def motors(self, m1: int, m2: int, m3: int, m4: int) -> None:
        """一次設定四顆馬達。"""
        for n, speed in enumerate((m1, m2, m3, m4), start=1):
            self.motor(n, speed)

    def stop(self) -> None:
        """四顆馬達全停。"""
        self.motors(0, 0, 0, 0)

    # ---------------------------------------------------------------- 編碼器
    def init_encoder(self, n: int) -> None:
        self._command(CMD_ENCODER_INIT[self._check_channel(n)])

    def encoder(self, n: int) -> int:
        """讀 `Mn` 的編碼器轉速。

        回傳有號 16-bit 值，正負代表轉向。採樣週期固定 20ms（韌體寫死，不可改）。
        用之前必須先呼叫一次 `init_encoder(n)`。
        """
        idx = self._check_channel(n)
        try:
            hi, lo = self._bus.read_i2c_block_data(self.address, CMD_ENCODER_READ[idx], 2)
        except OSError as exc:
            raise NeZhaError(f"讀取 M{n} 編碼器失敗。") from exc
        return int.from_bytes(bytes((hi, lo)), "big", signed=True)

    # ------------------------------------------------------------------ 舵機
    def init_servo(self, n: int) -> None:
        """初始化 `Sn`。每個舵機接口用之前都要單獨初始化一次。"""
        self._command(CMD_SERVO_INIT[self._check_channel(n)])

    def servo_pwm(self, n: int, pwm: int) -> None:
        """直接設定 `Sn` 的 PWM 值，範圍 50–250。"""
        idx = self._check_channel(n)
        if not SERVO_PWM_MIN <= pwm <= SERVO_PWM_MAX:
            raise ValueError(f"舵機 PWM 必須在 {SERVO_PWM_MIN}–{SERVO_PWM_MAX} 之間，收到 {pwm}")
        self._command_with_data(CMD_SERVO_SET[idx], self._split_u16(pwm))

    def servo(self, n: int, angle: float) -> None:
        """把 `Sn` 轉到指定角度（0–180°，對應 180° 模擬舵機）。"""
        if not 0 <= angle <= 180:
            raise ValueError(f"角度必須在 0–180 之間，收到 {angle}")
        span = SERVO_PWM_MAX - SERVO_PWM_MIN
        self.servo_pwm(n, round(SERVO_PWM_MIN + angle / 180 * span))

    # -------------------------------------------------------------------- 燈
    def led(self, name: str, state: bool | None) -> None:
        """控制板載燈。`state` 為 None 表示翻轉目前狀態。

        `name` 可用：`head`、`tail_left`、`tail_right`、`ambient`。
        """
        if name not in CMD_LED:
            raise ValueError(f"未知的燈 {name!r}，可用：{', '.join(CMD_LED)}")
        on, off, toggle = CMD_LED[name]
        self._command(toggle if state is None else (on if state else off))
