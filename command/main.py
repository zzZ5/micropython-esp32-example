from light import Light


class RemoteControl():
    '''
        遥控类, 用于注册命令和触发命令.
    '''

    def __init__(self):
        self.buttons = {}

    def set_command(self, button, command):
        # 注册命令到遥控类上
        self.buttons[button] = command

    def on_command(self, button):
        # 当按键被触发时执行命令
        self.buttons[button].execute()


# 新建遥控器类和命令类
remote_control = RemoteControl()
light_command = Light()
# 将命令类注册到遥控器按键上
remote_control.set_command(0, light_command)
