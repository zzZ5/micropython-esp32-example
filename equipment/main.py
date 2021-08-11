from mqtt import MQTTClient

import ds18x20
import machine
import onewire
import uasyncio as asyncio
import ujson as json
import utime as time


# 参数设置
config = {

}
equipment_key = ''
wifi_name = ''
wifi_password = ''
mqtt_user = ''
mqtt_password = ''
mqtt_server = ''
keys = []
value_skip = []
post_interval = 60
ntp_host = []
ntp_interval = 1000

ow = onewire.OneWire(machine.Pin(4))  # 创建onewire总线 引脚4（G4）
ds = ds18x20.DS18X20(ow)


def read_config():
    '''
    提取配置文件。
    '''

    with open("config.json") as f:
        global config
        config = json.load(f)
        global equipment_key, wifi_name, wifi_password, mqtt_user, mqtt_password, mqtt_server, keys, value_skip, post_interval, ntp_host, ntp_interval
        equipment_key = config['equipment_key']
        wifi_name = config['wifi_name']
        wifi_password = config['wifi_password']
        mqtt_user = config['mqtt_user']
        mqtt_password = config['mqtt_password']
        mqtt_server = config['mqtt_server']
        keys = config['keys']
        value_skip = config['value_skip']
        post_interval = config['post_interval']
        ntp_host = config['ntp_host']
        ntp_interval = config['ntp_interval']


def update_config(new_config, restart=False):
    '''
    更新当前参数。

    Args:
        new_config: 新的设置字典。
        restart: bool，更新参数后是否重启。
    '''

    global config
    for i in new_config.keys():
        if i in config:
            config[i] = new_config[i]
    with open("config.json", 'w+') as f:
        f.write(json.dumps(config))
    read_config()
    if restart:
        time.sleep_ms(1)
        machine.soft_reset()


def sync_ntp():
    '''
    通过网络校准时间。
    '''

    import ntptime
    ntptime.NTP_DELTA = 3155644800  # 可选 UTC+8偏移时间（秒），不设置就是UTC0
    is_setted = False
    times = 0
    while not is_setted:
        for host in ntp_host:
            ntptime.host = host  # 可选，ntp服务器，默认是"pool.ntp.org" 这里使用阿里服务器
            try:
                print('ntp:{}'.format(host))
                ntptime.settime()  # 修改设备时间,到这就已经设置好了
                is_setted = True
                break
            except:
                time.sleep_ms(ntp_interval)
                if times > 30:
                    time.sleep_ms(1)
                    machine.reset()
                times += 1
                continue


def wlan_connect(ssid, password):
    '''
    连接网络。

    Args:
        ssid: wifi名。
        password: wifi密码。
    '''

    import network
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active() or not wlan.isconnected():
        wlan.active(True)
        print(ssid)
        print(password)
        print('connecting to:', ssid)
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())


def get_temp():
    '''
    获取传感器温度数据。
    扫描总线以及配置的keys，确保key和温度一一匹配。
    '''

    roms = ds.scan()  # 扫描总线上的设备
    assert len(roms) == len(keys)
    ds.convert_temp()  # 获取采样温度
    for i, key in zip(roms, keys):
        yield ds.read_temp(i), key


class MyIotPrj:
    '''
    物联网主程序，包括接收和发送数据。
    '''

    def __init__(self):
        self.user = mqtt_user
        self.password = mqtt_password
        self.client_id = equipment_key
        self.mserver = mqtt_server

        # 指令响应，针对不同的指令调用不同的方法。
        self.cmd_lib = {
            'cmd': self.handle_cmd,
            'heater': self.handle_heater,
            'config': self.handle_config}

        self.client = MQTTClient(
            self.client_id, self.mserver, user=self.user, password=self.password)
        self.isconn = False
        self.topic_ctl = 'compostlab/{}/response'.format(
            equipment_key).encode()
        self.topic_sta = 'compostlab/{}/{}/{}'

    def handle_cmd(self, cmd):
        print('cmd:{}'.format(cmd))
        if cmd == "reset":
            time.sleep_ms(1)
            machine.reset()
        elif cmd == "soft_reset":
            time.sleep_ms(1)
            machine.soft_reset()
        else:
            pass

    def handle_config(self, cmd):
        update_config(cmd)

    def handle_heater(self, cmd):
        print('heater:{}'.format(cmd))

    def do_cmd(self, cmd):
        try:
            cmd_dict = json.loads(cmd)
            for key, value in cmd_dict.items():
                if key in self.cmd_lib.keys():
                    handle = self.cmd_lib[key]
                    handle(value)
        except:
            print('cmd error')

    async def sub_callback(self, topic, msg):
        self.do_cmd(msg)

    async def mqtt_main_thread(self):
        '''
        主程序，主要负责连接mqtt服务器。订阅topic，接收数据。
        '''
        try:
            self.client.set_callback(self.sub_callback)

            conn_ret_code = await self.client.connect()
            if conn_ret_code != 0:
                return

            print('conn_ret_code = {0}'.format(conn_ret_code))

            await self.client.subscribe(self.topic_ctl)
            print("Connected to {}, subscribed to {} topic".format(
                self.mserver, self.topic_ctl))

            self.isconn = True

            while True:
                await self.client.wait_msg()
                await asyncio.sleep(1)
        except:
            time.sleep_ms(1)
            machine.reset()
        finally:
            if self.client is not None:
                print('off line')
                await self.client.disconnect()
        self.isconn = False

    async def mqtt_upload_thread(self):
        '''
        上传数据程序。主要负责传输数据到mqtt服务器。
        '''
        while True:
            t1 = time.ticks_ms()
            if self.isconn == True:
                datas = {"data": []}
                for temp, key in get_temp():
                    if temp in value_skip:
                        continue
                    data = {"value": temp,
                            "key": key,
                            "measured_time": "{}-{}-{} {}:{}:{}".format(*time.localtime())}
                    datas["data"].append(data)
                await self.client.publish(self.topic_sta.format(equipment_key, 'post', 'data').encode(), json.dumps(datas), retain=False)
            t2 = time.ticks_ms()
            sleep_time = post_interval * 1000 - (t2 - t1)
            await asyncio.sleep_ms(sleep_time)
        while True:
            if self.isconn == True:
                await self.client.ping()
            await asyncio.sleep(5)


def main():
    read_config()
    wlan_connect(wifi_name, wifi_password)
    sync_ntp()
    mip = MyIotPrj()
    loop = asyncio.get_event_loop()

    # 循环携程运行主程序和上传数据程序
    loop.create_task(mip.mqtt_main_thread())
    loop.create_task(mip.mqtt_upload_thread())
    loop.run_forever()


if __name__ == '__main__':
    main()
