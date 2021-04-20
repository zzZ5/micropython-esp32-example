# 声明用到的类库，尤其是dht的类库
import utime
import network
import onewire
import ds18x20
import machine


pin2 = machine.Pin(2, machine.Pin.OUT, value=1)  # 控制继电器引脚 引脚2（G2）

ow = onewire.OneWire(machine.Pin(4))  # 创建onewire总线 引脚4（G4）
ds = ds18x20.DS18X20(ow)

time_interval = 6000  # 间隔时间，单位ms


def get_temp():
    roms = ds.scan()  # 扫描总线上的设备
    ds.convert_temp()  # 获取采样温度
    return ds.read_temp(roms[0]), ds.read_temp(roms[1])  # 得到温度


# 关闭继电器
def relay_off():
    pin2.on()


# 开启继电器
def relay_on():
    pin2.off()


def do_measure():
    temp_1, temp_2 = get_temp()  # 读取measure()函数中的温度数据
    dif = float(temp_1) - float(temp_2)
    print('===========================================')
    print("First temperature: {}℃".format(temp_1))
    print("Second temperature: {}℃".format(temp_2))
    print("The temperature difference: {}℃".format(dif))
    if float(dif) > 5.0:
        # 开启继电器
        relay_on()


while True:
    try:
        t1 = utime.ticks_ms()
        do_measure()
        t2 = utime.ticks_ms()

        # 休息一段时间再测量
        sleep_time = time_interval - (t2 - t1)
        if sleep_time > 0:
            utime.sleep_ms(sleep_time)
        # 关闭继电器
        relay_off()

    except Exception as e:
        print(e)
        utime.sleep(1)
        machine.reset()
