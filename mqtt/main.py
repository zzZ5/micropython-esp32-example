from mqtt import MQTTClient
import utime
import network
import ujson
from machine import Pin

pin2 = Pin(2, Pin.OUT, value=1)
wifi_name = 'CU'
wifi_password = '62814029'
wlan = network.WLAN(network.STA_IF)  # 设置开发板的网络模式
wlan.active(True)


def relay_off():
    pin2.on()


def relay_on():
    pin2.off()


def do_connect(wifi_name, wifi_password):  # 定义开发板连接无线网络的函数
    if not wlan.isconnected():  # 判断是否有网络连接
        print('connecting to network...')
        wlan.connect(wifi_name, wifi_password)  # 设置想要连接的无线名称和密码
        while not wlan.isconnected():  # 等待连接上无线网络
            pass
    print('network config:', wlan.ifconfig())


def sub_cb(topic, msg):  # 回调函数，收到服务器消息后会调用这个函数
    msg = ujson.loads(msg)
    if msg['msg'] == 'on':
        relay_on()
    elif msg['msg'] == 'off':
        relay_off()


do_connect(wifi_name, wifi_password)
# 建立一个MQTT客户端
c = MQTTClient(client_id='123', server='118.25.108.254',
               port=0, user='test', password='123456')
c.set_callback(sub_cb)  # 设置回调函数
c.connect()  # 建立连接
c.subscribe(b"test_topic")  # 监控pin2ctl这个通道，接收控制命令
while True:
    c.wait_msg()
    print('test')
