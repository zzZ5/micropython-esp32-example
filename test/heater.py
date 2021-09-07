from command import Command


class Heater(Command):
    def execute(self):
        print('heater on')

    def undo(self):
        print('heater off')
