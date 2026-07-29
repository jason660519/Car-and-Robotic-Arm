# Robotic Arm Servo Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a simple, interactive, and conservative check for robotic-arm servos on NeZha channels `S2`, `S3`, and `S4`.

**Architecture:** Extend `NeZha.close()` with an opt-out for its normal wheel-stop writes so a servo-only example can close the owned I2C bus without sending wheel commands. Keep all operator interaction in `examples/04_servo_check.py`, with a small injectable runner so automated tests can verify the exact channel and angle sequence without touching hardware.

**Tech Stack:** Python 3.11+, `smbus2`, `pytest`, `ruff`, `uv`

## Global Constraints

- The exact servo channel order is `2, 3, 4`.
- The exact angle sequence per channel is `90, 80, 100, 90`.
- Require Enter before every angle change.
- Require the exact startup confirmation `yes` before constructing `NeZha`.
- Do not invoke wheel-motor control from the servo-check script.
- Do not claim that exiting Python removes servo holding torque.
- Real hardware execution remains an operator action.
- Do not commit or push; the user has not authorized Git mutations.

---

### Task 1: Allow Servo-Only Bus Cleanup

**Files:**
- Modify: `src/carbot/nezha.py`
- Modify: `tests/test_nezha.py`

**Interfaces:**
- Consumes: existing `NeZha.close()` and `NeZha.__exit__()`
- Produces: `NeZha.close(*, stop_motors: bool = True) -> None`

- [ ] **Step 1: Add a failing test for cleanup without wheel commands**

Add this test beside the existing close/context-manager tests in `tests/test_nezha.py`:

```python
def test_close_can_skip_motor_stop(bus: FakeBus):
    board = NeZha(bus, init_motors=False)
    bus.calls.clear()

    board.close(stop_motors=False)

    assert bus.calls == []
```

The borrowed `FakeBus` remains open by design, and the empty call list proves that cleanup sent no
wheel command.

- [ ] **Step 2: Run the focused test and confirm the API is missing**

Run:

```bash
uv run pytest tests/test_nezha.py::test_close_can_skip_motor_stop -v
```

Expected: FAIL with `TypeError: NeZha.close() got an unexpected keyword argument 'stop_motors'`.

- [ ] **Step 3: Implement the optional wheel-stop behavior**

Replace `NeZha.close()` in `src/carbot/nezha.py` with:

```python
def close(self, *, stop_motors: bool = True) -> None:
    """Close the bus, optionally stopping all wheel motors first."""
    try:
        if stop_motors:
            self.stop()
    finally:
        if self._owns_bus:
            self._bus.close()
```

Keep `__exit__()` unchanged so all existing context-manager users retain fail-safe wheel stopping.

- [ ] **Step 4: Run the close-behavior tests**

Run:

```bash
uv run pytest tests/test_nezha.py -k "close or context_manager" -v
```

Expected: the new opt-out test passes, and existing default/context-manager stop tests still pass.

---

### Task 2: Add the Interactive Servo Check

**Files:**
- Create: `examples/04_servo_check.py`
- Create: `tests/test_servo_check.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: `NeZha(init_motors=False)`, `NeZha.init_servo(n)`, `NeZha.servo(n, angle)`, and `NeZha.close(stop_motors=False)`
- Produces:
  - `SERVO_CHANNELS: tuple[int, ...] = (2, 3, 4)`
  - `TEST_ANGLES: tuple[int, ...] = (90, 80, 100, 90)`
  - `run_check(board: ServoBoard, prompt: Callable[[str], str] = input, output: Callable[[str], None] = print) -> None`
  - `main() -> int`

- [ ] **Step 1: Add tests that load the numbered example as a module**

Create `tests/test_servo_check.py` with a helper based on
`importlib.util.spec_from_file_location()`:

```python
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


SCRIPT = Path(__file__).parents[1] / "examples" / "04_servo_check.py"


def load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("servo_check_example", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeBoard:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    def init_servo(self, channel: int) -> None:
        self.calls.append(("init_servo", channel))

    def servo(self, channel: int, angle: int) -> None:
        self.calls.append(("servo", channel, angle))


def test_run_check_initializes_and_moves_one_channel_at_a_time():
    module = load_script()
    board = FakeBoard()
    prompts: list[str] = []

    module.run_check(
        board,
        prompt=lambda message: prompts.append(message) or "",
        output=lambda _message: None,
    )

    assert board.calls == [
        ("init_servo", 2),
        ("servo", 2, 90),
        ("servo", 2, 80),
        ("servo", 2, 100),
        ("servo", 2, 90),
        ("init_servo", 3),
        ("servo", 3, 90),
        ("servo", 3, 80),
        ("servo", 3, 100),
        ("servo", 3, 90),
        ("init_servo", 4),
        ("servo", 4, 90),
        ("servo", 4, 80),
        ("servo", 4, 100),
        ("servo", 4, 90),
    ]
    assert len(prompts) == 12


@pytest.mark.parametrize("answer", ["", "no", "YES ", "y"])
def test_main_rejects_any_confirmation_except_exact_yes(monkeypatch, answer: str):
    module = load_script()
    constructed = False

    def forbidden_constructor(*_args, **_kwargs):
        nonlocal constructed
        constructed = True
        raise AssertionError("NeZha must not be constructed")

    monkeypatch.setattr("builtins.input", lambda _message: answer)
    monkeypatch.setattr(module, "NeZha", forbidden_constructor)

    assert module.main() == 1
    assert constructed is False
```

- [ ] **Step 2: Run the new tests and confirm the example is absent**

Run:

```bash
uv run pytest tests/test_servo_check.py -v
```

Expected: FAIL with `FileNotFoundError` because `examples/04_servo_check.py` does not exist.

- [ ] **Step 3: Implement the interactive example**

Create `examples/04_servo_check.py` with:

```python
"""互動式檢查機械臂的三顆舵機。

實體配置：S2、S3、S4。每次只動一顆，並只在 90° 中位附近移動 ±10°。
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Protocol

from carbot.nezha import NeZha, NeZhaError

SERVO_CHANNELS = (2, 3, 4)
TEST_ANGLES = (90, 80, 100, 90)


class ServoBoard(Protocol):
    def init_servo(self, channel: int) -> None: ...

    def servo(self, channel: int, angle: float) -> None: ...


def run_check(
    board: ServoBoard,
    prompt: Callable[[str], str] = input,
    output: Callable[[str], None] = print,
) -> None:
    for channel in SERVO_CHANNELS:
        output(f"\n=== S{channel} ===")
        board.init_servo(channel)

        for angle in TEST_ANGLES:
            prompt(
                f"確認手已移開、關節沒有卡住，按 Enter 讓 S{channel} 移到 {angle}°；"
                "有異常請直接關閉主電源。"
            )
            board.servo(channel, angle)

        output(f"S{channel} 完成：請記下它控制哪個關節、移動方向，以及有無異音。")


def main() -> int:
    print("本測試依序檢查 S2、S3、S4，每次只做 90° 附近的小幅移動。")
    print("若卡住、抖動、持續嗡嗡叫或接近極限，立刻關閉機器人主電源。")
    answer = input("手臂周圍已淨空，而且主電源開關伸手可及嗎？(yes/no) ")
    if answer != "yes":
        print("未收到完整的 yes；不送出任何舵機指令。")
        return 1

    board: NeZha | None = None
    try:
        board = NeZha(init_motors=False)
        run_check(board)
    except KeyboardInterrupt:
        print("\n測試已中止。舵機可能仍保持扭力；請關閉機器人主電源。")
        return 130
    except NeZhaError as exc:
        print(f"\n通訊失敗：{exc}")
        print("請關閉機器人主電源，再檢查接線與 I2C 連線。")
        return 1
    finally:
        if board is not None:
            board.close(stop_motors=False)

    print("\n三個接口測試完成。舵機仍可能保持扭力；記錄結果後請關閉主電源。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Add success and error-path tests**

Append to `tests/test_servo_check.py`:

```python
def test_main_runs_check_and_closes_without_motor_stop(monkeypatch):
    module = load_script()
    calls: list[tuple[object, ...]] = []

    class Board(FakeBoard):
        def __init__(self, *, init_motors: bool):
            super().__init__()
            calls.append(("construct", init_motors))

        def close(self, *, stop_motors: bool) -> None:
            calls.append(("close", stop_motors))

    monkeypatch.setattr("builtins.input", lambda _message: "yes")
    monkeypatch.setattr(module, "NeZha", Board)
    monkeypatch.setattr(module, "run_check", lambda _board: calls.append(("run_check",)))

    assert module.main() == 0
    assert calls == [
        ("construct", False),
        ("run_check",),
        ("close", False),
    ]


def test_main_handles_keyboard_interrupt_and_closes(monkeypatch):
    module = load_script()
    closed: list[bool] = []

    class Board(FakeBoard):
        def __init__(self, *, init_motors: bool):
            assert init_motors is False

        def close(self, *, stop_motors: bool) -> None:
            closed.append(stop_motors)

    monkeypatch.setattr("builtins.input", lambda _message: "yes")
    monkeypatch.setattr(module, "NeZha", Board)
    monkeypatch.setattr(
        module,
        "run_check",
        lambda _board: (_ for _ in ()).throw(KeyboardInterrupt),
    )

    assert module.main() == 130
    assert closed == [False]
```

These tests prove that `main()` constructs the driver with wheel initialization disabled, uses the
servo-only cleanup path, and still cleans up after an operator interrupt.

- [ ] **Step 5: Run the servo-check tests**

Run:

```bash
uv run pytest tests/test_servo_check.py -v
```

Expected: all servo-check tests pass.

- [ ] **Step 6: Add the example to the README sequence**

Add this command after `examples/03_drive.py` in `README.md`:

```bash
uv run python examples/04_servo_check.py
```

Add a fourth list item explaining that it interactively checks arm servos `S2`–`S4`, one channel
at a time, while the operator remains beside the robot.

- [ ] **Step 7: Run full non-hardware verification**

Run:

```bash
uv run pytest
uv run ruff check .
```

Expected: all tests pass and Ruff reports `All checks passed!`.

- [ ] **Step 8: Perform a dry-run rejection smoke check**

Run locally with no hardware access:

```bash
printf 'no\n' | uv run python examples/04_servo_check.py
```

Expected: exit code `1`, output says no servo commands were sent, and the code never constructs
`NeZha`.

Do not run the `yes` path on behalf of the user because it moves real hardware.
