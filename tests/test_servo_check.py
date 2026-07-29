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


def test_main_handles_communication_error_and_closes(monkeypatch):
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
        lambda _board: (_ for _ in ()).throw(module.NeZhaError("I2C failed")),
    )

    assert module.main() == 1
    assert closed == [False]
