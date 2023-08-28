from command import Command
from machine import Pin


class Heater(Command):

    def __init__(self):
        self.pin2 = Pin(2, Pin.OUT, value=1)

    def execute(self):
        self.pin2.off()
        print('heater on')

    def undo(self):
        self.pin2.on()
        print('heater off')
