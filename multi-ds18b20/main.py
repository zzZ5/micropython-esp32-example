# 声明用到的类库，尤其是dht的类库
import utime
import network
import onewire
import ds18x20
import machine

ow = onewire.OneWire(machine.Pin(4))  # 创建onewire总线 引脚4（G4）
ds = ds18x20.DS18X20(ow)
sleep_time = 5000
wlan = network.WLAN(network.STA_IF)  # 设置开发板的网络模式
wlan.active(True)


def GetTemp():
    roms = ds.scan()  # 扫描总线上的设备
    ds.convert_temp()  # 获取采样温度
    for i in roms:
        yield ds.read_temp(i)


def do_measure():
    print("temperature:")
    for temp in GetTemp():
        print(temp, end='  ')
    print("")
    print("====================")


while True:
    try:
        do_measure()
        utime.sleep_ms(sleep_time)
    except Exception as e:
        print(e)
        utime.sleep(1)
        machine.reset()
