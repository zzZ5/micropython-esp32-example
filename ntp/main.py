import utime as time
import ntptime
from machine import Timer


def sync_ntp():
    ntptime.NTP_DELTA = 3155644800   # 可选 UTC+8偏移时间（秒），不设置就是UTC0
    ntptime.host = 'ntp1.aliyun.com'  # 可选，ntp服务器，默认是"pool.ntp.org"
    ntptime.settime()   # 修改设备时间,到这就已经设置好了


def time_calibration():
    timer = Timer(1)
    timer.init(mode=Timer.PERIODIC, period=1000 * 60 *
               60 * 7, callback=lambda t: sync_ntp())


time_calibration()
print(time.localtime())
