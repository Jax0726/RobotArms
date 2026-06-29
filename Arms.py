import os
import platform
import time

USE_REAL_GPIO = platform.system() == 'Linux' and os.path.exists('/proc/cpuinfo')
Servo = None
REAL_GPIO_AVAILABLE = False

if USE_REAL_GPIO:
    try:
        from gpiozero import Servo
        REAL_GPIO_AVAILABLE = True
    except ImportError:
        Servo = None


class DummyServo:

    def __init__(self, pin):
        self.pin = pin
        self._value = 0

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value is None:
            self._value = None
        elif -1 <= value <= 1:
            self._value = value
        else:
            raise ValueError('Servo value must be between -1 and 1 or None')


class MotionSmoother:

    def __init__(self, step: float = 0.05, delay: float = 0.02):
        self.step = step
        self.delay = delay

    def move(self, servo, current_position: float, target_position: float) -> float:
        target_position = max(-1, min(1, target_position))
        while abs(current_position - target_position) > self.step:
            current_position += self.step if current_position < target_position else -self.step
            servo.value = current_position
            time.sleep(self.delay)
        servo.value = target_position
        return target_position


class RobotArm:

    def __init__(self, gpio_pin: int = 17, smoother=None):
        self.gpio_pin = gpio_pin
        self.servo = self._create_servo()
        self.current_position = 0
        self.servo.value = 0
        self.smoother = smoother

    def _create_servo(self):
        if not REAL_GPIO_AVAILABLE or Servo is None:
            print('Info: running in dummy servo mode.')
            return DummyServo(self.gpio_pin)

        try:
            return Servo(self.gpio_pin)
        except Exception as exc:
            print('Warning: unable to initialize GPIO servo:', exc)
            print('Info: running in dummy servo mode.')
            return DummyServo(self.gpio_pin)

    def move_to_position(self, target_position: float, smooth: bool = False):
        target_position = max(-1, min(1, target_position))
        if smooth and self.smoother:
            self.current_position = self.smoother.move(self.servo, self.current_position, target_position)
        else:
            self.servo.value = target_position
            self.current_position = target_position

    def stop(self):
        self.servo.value = None
        self.current_position = None

    def get_position(self):
        return self.current_position


class ArmController:

    def __init__(self):
        self.arms = {}

    def register_arm(self, arm_id: str, robot_arm: RobotArm):
        self.arms[arm_id] = robot_arm

    def move_arm(self, arm_id: str, target_position: float, smooth: bool = False):
        arm = self.arms.get(arm_id)
        if arm:
            arm.move_to_position(target_position, smooth)

    def stop_all_arms(self):
        for arm in self.arms.values():
            arm.stop()

    def get_arm_position(self, arm_id: str):
        arm = self.arms.get(arm_id)
        return arm.get_position() if arm else None


def create_default_controller() -> ArmController:
    smoother = MotionSmoother(step=0.05, delay=0.02)
    controller = ArmController()

    base = RobotArm(gpio_pin=17, smoother=smoother)
    elbow = RobotArm(gpio_pin=18, smoother=smoother)

    controller.register_arm('base', base)
    controller.register_arm('elbow', elbow)
    return controller


def main() -> None:
    controller = create_default_controller()
    controller.move_arm('base', 0.5)
    time.sleep(1)
    controller.move_arm('elbow', -0.5, smooth=True)
    time.sleep(1)
    controller.stop_all_arms()


if __name__ == '__main__':
    main()
