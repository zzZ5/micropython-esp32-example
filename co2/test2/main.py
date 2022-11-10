import adafruit_sgp30
from mqtt import MQTTClient

import ds18x20
import machine
import onewire
import uasyncio as asyncio
import ujson as json
import utime as time
from machine import I2C, Pin

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

ERROR_LEVEL = ["DEBUG", "INFO", "WARN",  "ERROR", "FATAL"]


def write_error(msg, err_lev=3):
    '''.
    记录错误信息。
    '''
    open_mode = 'w'

    # 错误文件过大就覆盖掉
    try:
        with open("error.log") as f:
            if len(f.readlines()) < 100:
                open_mode = 'a'
    except:
        pass

    try:
        with open("error.log", open_mode) as f:
            f.write(ERROR_LEVEL[err_lev] + ": " + msg +
                    " --{}-{}-{} {}:{}:{}".format(*time.localtime()) + "\n")
    except:
        time.sleep_ms(1)
        machine.reset()
    return


# 二氧化碳传感器
try:
    i2c = I2C(0)
    i2c = I2C(1, scl=Pin(22), sda=Pin(21), freq=100000)
    sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)  # 创建sgp30传感器 引脚22、21（G22、G21）
    baseline_time = time.time()
    has_baseline = False
except:
    time.sleep_ms(1)
    write_error("二氧化碳传感器连接失败。")
    machine.reset()


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

    print("配置文件提取完成！")


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
        machine.reset()


def sync_ntp():
    '''
    通过网络校准时间。
    '''

    print("开始校准时间......")
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
                    write_error("时间校准失败。")
                    machine.reset()
                times += 1
                continue
    print("时间校准完成！")


def wlan_connect(ssid, password):
    '''
    连接网络。

    Args:
        ssid: wifi名。
        password: wifi密码。
    '''

    print("开始连接网络......")
    import network
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active() or not wlan.isconnected():
        wlan.active(True)
        print('connecting to:', ssid)
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    print("网络连接成功！")


def init_sgp():
    '''
    初始化spg30传感器
    '''
    global baseline_time
    print("初始化spg30传感器......")
    try:
        sgp30.iaq_init()
        baseline_time = time.time()
    except:
        time.sleep_ms(1)
        write_error("sgp30传感器初始化失败。")
        machine.reset()
    print("Waiting 15 seconds for SGP30 initialization.")
    time.sleep(15)
    global has_baseline
    try:
        f_co2 = open('co2eq_baseline.txt', 'r')
        f_tvoc = open('tvoc_baseline.txt', 'r')
        co2_baseline = int(f_co2.read())
        tvoc_baseline = int(f_tvoc.read())
        # Use them to calibrate the sensor
        sgp30.set_iaq_baseline(co2_baseline, tvoc_baseline)

        f_co2.close()
        f_tvoc.close()
        has_baseline = True
    except:
        pass
    print("spg30传感器初始化成功！")


def get_CO2():
    '''
    获取sgp30传感器的CO2数据。
    '''
    global baseline_time, has_baseline
    try:
        co2eq, tvoc = sgp30.iaq_measure()

        if (has_baseline and (time.time() - baseline_time >= 3600)) \
                or ((not has_baseline) and (time.time() - baseline_time >= 43200)):
            print('Saving baseline!')

            baseline_time = time.time()

            f_co2 = open('co2eq_baseline.txt', 'w')
            f_tvoc = open('tvoc_baseline.txt', 'w')

            bl_co2, bl_tvoc = sgp30.get_iaq_baseline()
            f_co2.write(str(bl_co2))
            f_tvoc.write(str(bl_tvoc))

            f_co2.close()
            f_tvoc.close()
            has_baseline = True

        return co2eq, keys['sgp']

    except:
        time.sleep_ms(1)
        write_error("获取二氧化碳数据失败。")
        machine.reset()


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
            'config': self.handle_config,
        }

        self.client = MQTTClient(
            self.client_id, self.mserver, user=self.user, password=self.password)
        self.isconn = False
        self.topic_ctl = 'compostlab/{}/response'.format(
            equipment_key).encode()
        self.topic_sta = 'compostlab/{}/{}/{}'

    def handle_cmd(self, cmd):
        if cmd == "reset":
            time.sleep_ms(1)
            machine.reset()
        else:
            pass

    def handle_config(self, cmd):
        update_config(cmd)

    async def do_cmd(self, cmd):
        try:
            cmd_dict = json.loads(cmd)
            for key, value in cmd_dict.items():
                if key in self.cmd_lib.keys():
                    handle = self.cmd_lib[key]
                    handle(value)
        except:
            print('cmd error')

    async def sub_callback(self, topic, msg):
        await self.do_cmd(msg)

    async def mqtt_main_thread(self):
        '''
        主程序，主要负责连接mqtt服务器。订阅topic，接收数据。
        '''
        try:
            self.client.set_callback(self.sub_callback)

            conn_ret_code = await self.client.connect()
            if conn_ret_code != 0:
                return

            print("开始连接MQTT服务器......")
            print('conn_ret_code = {0}'.format(conn_ret_code))
            await self.client.subscribe(self.topic_ctl)
            print("Connected to {}, subscribed to {} topic".format(
                self.mserver, self.topic_ctl))
            self.isconn = True
            print("MQTT服务器连接成功！开始监听数据......")

            while True:
                await self.client.wait_msg()
                await asyncio.sleep(1)
        except:
            time.sleep_ms(1)
            write_error("连接MQTT服务器失败。")
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

                co2_value, co2_key = get_CO2()
                if co2_value not in value_skip:
                    data_co2 = {"value": co2_value,
                                "key": co2_key,
                                "measured_time": "{}-{}-{} {}:{}:{}".format(*time.localtime())}
                    datas["data"].append(data_co2)

                # print("上传数据：")
                # print(datas["data"])
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
    init_sgp()
    mip = MyIotPrj()
    loop = asyncio.get_event_loop()

    # 循环协程运行主程序和上传数据程序
    loop.create_task(mip.mqtt_main_thread())
    loop.create_task(mip.mqtt_upload_thread())
    loop.run_forever()


if __name__ == '__main__':
    main()
