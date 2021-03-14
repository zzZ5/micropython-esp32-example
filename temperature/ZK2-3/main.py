# 声明用到的类库，尤其是dht的类库
import utime
import urequests
import ujson
import network
import onewire
import ds18x20
import machine

key = "y6DvZ4izS78uGBq"
wifi_name = 'CU'
wifi_password = '62814029'
url = 'http://118.25.108.254/submit/'

ow = onewire.OneWire(machine.Pin(4))  # 创建onewire总线 引脚4（G4）
ds = ds18x20.DS18X20(ow)
led = machine.Pin(2, machine.Pin.OUT)
time_interval = 60000
wlan = network.WLAN(network.STA_IF)  # 设置开发板的网络模式
wlan.active(True)


def GetTemp():
    roms = ds.scan()  # 扫描总线上的设备
    ds.convert_temp()  # 获取采样温度
    return ds.read_temp(roms[0])  # 得到温度


def http_get(url):  # 定义数据上传的函数
    response = urequests.get(url)
    if response.status_code == 200:
        parsed = ujson.loads(response.text)
        # you can also use parsed = response.json()
        if parsed['Code'] == 100:
            pass
        else:
            print("{}: {}".format(parsed['Code'], parsed['Message']))
    else:
        print(response.status_code)
    response.close()


def do_connect(wifi_name, wifi_password):  # 定义开发板连接无线网络的函数
    if not wlan.isconnected():  # 判断是否有网络连接
        print('connecting to network...')
        wlan.connect(wifi_name, wifi_password)  # 设置想要连接的无线名称和密码
        while not wlan.isconnected():  # 等待连接上无线网络
            pass


def do_measure(key, descript=''):
    temp_ = GetTemp()  # 读取measure()函数中的温度数据
    if '{}'.format(temp_) == '85.0':
        return
    http_get('http://118.25.108.254/submit/?key={}&value={}&descript={}'.format(
        key, temp_, descript))


do_connect(wifi_name, wifi_password)  # 调用一次开发板连接无线网络的函数
while True:
    try:
        t1 = utime.ticks_ms()
        do_measure(key=key, descript='℃')
        t2 = utime.ticks_ms()
        sleep_time = time_interval - (t2 - t1)
        if sleep_time > 0:
            utime.sleep_ms(sleep_time)
    except Exception as e:
        print(e)
        utime.sleep(1)
        machine.reset()
