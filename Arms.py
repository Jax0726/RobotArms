import os
import platform
import time
import math

def is_raspberry_pi():
    try:
        with open('/proc/device-tree/model', 'r') as f:
            return 'Raspberry Pi' in f.read()
    except:
        return False

USE_REAL_GPIO = platform.system() == 'Linux' and is_raspberry_pi()

try:
    from gpiozero import Servo as GPIOServo
except Exception:
    GPIOServo = None


class DummyServo:
    def __init__(self, pin):
        self.pin = pin
        self._value = 0

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        if v is None:
            self._value = 0
        else:
            self._value = max(-1, min(1, float(v)))


class RobotArm:
    def __init__(self, gpio_pin, name="arm", min_limit=-1, max_limit=1, offset=0.0):
        self.gpio_pin = gpio_pin
        self.name = name

        self.min_limit = min_limit
        self.max_limit = max_limit
        self.offset = offset

        self.servo = self._create_servo()

        self.position = 0.0
        self.target = 0.0
        self.velocity = 0.0

        self.max_speed = 0.08
        self.accel = 0.02
        self.active = True

    def _create_servo(self):
        if not USE_REAL_GPIO or GPIOServo is None:
            return DummyServo(self.gpio_pin)
        try:
            s = GPIOServo(self.gpio_pin)
            s.value = 0
            return s
        except:
            return DummyServo(self.gpio_pin)

    def set_target(self, target):
        self.target = max(self.min_limit, min(self.max_limit, float(target) + self.offset))
        self.velocity = 0.0
        self.active = True

    def stop(self):
        self.servo.value = None
        self.velocity = 0.0
        self.active = False

    def update(self):
        if not self.active:
            return

        error = self.target - self.position

        if abs(error) < 0.003 and abs(self.velocity) < 0.003:
            self.position = self.target
            self.velocity = 0.0
            self.servo.value = self.position
            return

        desired = max(-self.max_speed, min(self.max_speed, error))

        self.velocity = (
            self.velocity * (1 - self.accel)
            + desired * self.accel
        )

        self.velocity *= 0.9

        self.position += self.velocity
        self.position = max(-1, min(1, self.position))

        self.servo.value = self.position


class ArmController:
    def __init__(self, hz=60):
        self.arms = {}
        self.hz = hz
        self.running = False

    def register_arm(self, name, arm):
        self.arms[name] = arm

    def set_target(self, name, target):
        arm = self.arms.get(name)
        if arm:
            arm.set_target(target)

    def stop_all(self):
        for a in self.arms.values():
            a.stop()

    def update_all(self):
        for a in self.arms.values():
            a.update()

    def run_loop(self):
        self.running = True
        dt = 1.0 / self.hz

        try:
            while self.running:
                start = time.time()

                self.update_all()

                elapsed = time.time() - start
                sleep_time = dt - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            self.stop_all()
            self.running = False

    def stop(self):
        self.running = False


def create_default_controller():
    c = ArmController(hz=60)

    c.register_arm("base", RobotArm(17, "base"))
    c.register_arm("elbow", RobotArm(18, "elbow"))

    return c


def main():
    robot = create_default_controller()

    robot.set_target("base", 0.6)
    robot.set_target("elbow", -0.4)

    start = time.time()
    while time.time() - start < 2:
        robot.update_all()
        time.sleep(0.02)

    robot.set_target("base", -0.6)
    robot.set_target("elbow", 0.4)

    robot.run_loop()


if __name__ == "__main__":
    main()