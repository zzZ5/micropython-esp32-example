# 声明用到的类库，尤其是dht的类库
import utime
import network
import onewire
import ds18x20
import machine

ow = onewire.OneWire(machine.Pin(4))  # 创建onewire总线 引脚4（G4）
ds = ds18x20.DS18X20(ow)
time_interval = 6000
wlan = network.WLAN(network.STA_IF)  # 设置开发板的网络模式
wlan.active(True)


def GetTemp():
    roms = ds.scan()  # 扫描总线上的设备
    ds.convert_temp()  # 获取采样温度

    return ds.read_temp(roms[0]), ds.read_temp(roms[1])  # 得到温度


def do_measure():
    temp_ = GetTemp()  # 读取measure()函数中的温度数据
    print(temp_)


while True:
    try:
        t1 = utime.ticks_ms()
        do_measure()
        t2 = utime.ticks_ms()
        sleep_time = time_interval - (t2 - t1)
        if sleep_time > 0:
            utime.sleep_ms(sleep_time)
    except Exception as e:
        print(e)
        utime.sleep(1)
        machine.reset()
