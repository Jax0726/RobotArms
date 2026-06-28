from gpiozero import Servo


class Arm:
    def __init__(self, pin=17):
        self.position = 0
        self.pin = pin
        self.servo = Servo(self.pin)

    def move_servo(self, position):
        position = max(-1, min(1, position))
        self.servo.value = position
        self.position = position
    
    def get_servo_position(self):
        return self.position