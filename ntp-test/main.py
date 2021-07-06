import utime as time
from machine import Timer


wifi_name = 'HW'
wifi_password = 'ZNXK8888'


def sync_ntp(**kwargs):
    """通过网络校准时间"""
    import ntptime
    ntptime.NTP_DELTA = 3155644800  # 可选 UTC+8偏移时间（秒），不设置就是UTC0
    ntptime.host = 'ntp1.aliyun.com'  # 可选，ntp服务器，默认是"pool.ntp.org" 这里使用阿里服务器
    ntptime.settime()  # 修改设备时间,到这就已经设置好了


def time_calibration():
    timer = Timer(1)
    timer.init(mode=Timer.PERIODIC, period=1000 * 60 *
               60 * 7, callback=lambda t: sync_ntp())


def wlan_connect(ssid='MYSSID', password='MYPASS'):
    import network
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active() or not wlan.isconnected():
        wlan.active(True)
        print('connecting to:', ssid)
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())


wlan_connect(wifi_name, wifi_password)
time_calibration()
while(True):
    print("{}-{}-{} {}:{}:{}".format(*time.localtime()))
    time.sleep(1)
