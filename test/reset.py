from command import Command
import machine
import utime as time


class Reset(Command):
    def execute(self):
        print('new_reset')
        time.sleep_ms(1)
        machine.reset()
