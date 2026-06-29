from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
import time

factory = PiGPIOFactory()

class MotionSmoother:
    def __init__(self, step=0.05, delay=0.02):
        self.step = step
        self.delay = delay

    def move(self, servo, current_position, target_position):
        target_position = max(-1, min(1, target_position))
        while abs(current_position - target_position) > self.step:
            current_position += self.step if current_position < target_position else -self.step
            servo.value = current_position
            time.sleep(self.delay)
        servo.value = target_position
        return target_position

class RobotArm:
    def __init__(self, gpio_pin=17, smoother=None):
        self.gpio_pin = gpio_pin
        self.servo = Servo(self.gpio_pin, pin_factory=factory)
        self.current_position = 0
        self.servo.value = 0
        self.smoother = smoother

    def move_to_position(self, target_position, smooth=False):
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

    def register_arm(self, arm_id, robot_arm):
        self.arms[arm_id] = robot_arm

    def move_arm(self, arm_id, target_position, smooth=False):
        if arm_id in self.arms:
            self.arms[arm_id].move_to_position(target_position, smooth)

    def stop_all_arms(self):
        for arm in self.arms.values():
            arm.stop()

    def get_arm_position(self, arm_id):
        if arm_id in self.arms:
            return self.arms[arm_id].get_position()
        return None

if __name__ == "__main__":
    smoother = MotionSmoother(step=0.05, delay=0.02)
    controller = ArmController()
    base = RobotArm(gpio_pin=17, smoother=smoother)
    elbow = RobotArm(gpio_pin=18, smoother=smoother)
    controller.register_arm("base", base)
    controller.register_arm("elbow", elbow)
    controller.move_arm("base", 0.5)
    time.sleep(1)
    controller.move_arm("elbow", -0.5, smooth=True)
    time.sleep(1)
    controller.stop_all_arms()