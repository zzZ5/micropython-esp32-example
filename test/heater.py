from command import Command
from machine import Pin

pin2 = Pin(2, Pin.OUT, value=1)


class Heater(Command):
    def execute(self):
        pin2.off()
        print('heater on')

    def undo(self):
        pin2.on()
        print('heater off')
