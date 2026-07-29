# Robotic Arm Servo Check Design

## Goal

Add a simple interactive hardware check for the three robotic-arm servos connected to NeZha
channels `S2`, `S3`, and `S4`. The workflow should resemble `examples/02_motor_check.py`: it must
guide the operator one step at a time, keep movements conservative, and make observations easy to
record.

## Safety Constraints

- The operator must remain beside the robot and explicitly type `yes` before any servo command.
- The arm workspace must be clear, and the main power switch must remain within reach.
- Test one servo at a time.
- Use only the small sequence `90° -> 80° -> 100° -> 90°`.
- Require Enter before every angle change so the operator can stop between movements.
- Tell the operator to cut main power immediately if a joint binds, chatters, produces a sustained
  buzzing sound, or approaches a mechanical stop.
- Do not drive wheel motors.
- Do not claim that software shutdown removes servo holding torque. The NeZha protocol has no
  verified servo-disable command.

## Interface

Create `examples/04_servo_check.py`.

The script will:

1. Explain the emergency-stop rule and ask for the exact confirmation `yes`.
2. Open `NeZha(init_motors=False)`.
3. For each channel in `S2`, `S3`, and `S4`:
   - announce the channel;
   - initialize that servo channel;
   - wait for Enter before each target angle;
   - command `90°`, `80°`, `100°`, then `90°`;
   - ask the operator to record the controlled joint, observed direction, and any abnormal behavior.
4. Print a completion message and remind the operator to switch off robot power when finished.

`Ctrl-C` and communication errors must produce a short, actionable message. The script must not
promise that exiting Python removes servo power.

## Verification

- Add focused automated tests using a fake `NeZha` object or extracted testable runner function.
- Verify the confirmation gate rejects anything except `yes`.
- Verify the exact channel order is `2, 3, 4`.
- Verify each channel is initialized before movement.
- Verify the exact angle sequence is `90, 80, 100, 90`.
- Verify wheel-motor methods are never invoked.
- Run the relevant `pytest` suite and `ruff`.

Real hardware execution remains an operator action because the repository rules prohibit an agent
from running programs that move hardware.
