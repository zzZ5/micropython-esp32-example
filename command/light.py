from command import Command


class Light(Command):
    # 开灯命令
    def execute(self):
        # 执行
        print("Light on!")

    def undo(self):
        # 撤销
        print("Light off!")
