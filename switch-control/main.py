from machine import Pin

pin2 = Pin(2, Pin.OUT, value=1)


# 关闭继电器
def relay_off():
    pin2.on()


# 开启继电器
def relay_on():
    pin2.off()
