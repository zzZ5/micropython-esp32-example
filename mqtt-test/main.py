from mqtt import MQTTClient
import uasyncio as asyncio
import ujson as json


class MyIotPrj:
    def __init__(self):
        mqtt_user = 'test'
        mqtt_password = '12345678'
        client_id = 'test2222'
        wifi_name = 'HW'
        wifi_password = 'ZNXK8888'
        self.mserver = '118.25.108.254'
        self.wlan_connect(wifi_name, wifi_password)
        self.client = MQTTClient(
            client_id, self.mserver, user=mqtt_user, password=mqtt_password)
        self.isconn = False
        self.topic_ctl = b'topic/test'
        self.topic_sta = b'topic/test'

    def wlan_connect(self, ssid='MYSSID', password='MYPASS'):
        import network
        wlan = network.WLAN(network.STA_IF)
        if not wlan.active() or not wlan.isconnected():
            wlan.active(True)
            print('connecting to:', ssid)
            wlan.connect(ssid, password)
            while not wlan.isconnected():
                pass
        print('network config:', wlan.ifconfig())

    async def sub_callback(self, topic, msg):
        print((topic, msg))

    async def mqtt_main_thread(self):

        try:
            self.client.set_callback(self.sub_callback)

            conn_ret_code = await self.client.connect()
            if conn_ret_code != 0:
                return

            print('conn_ret_code = {0}'.format(conn_ret_code))

            await self.client.subscribe(self.topic_ctl)
            print("Connected to %s, subscribed to %s topic" %
                  (self.mserver, self.topic_ctl))

            self.isconn = True

            while True:
                await self.client.wait_msg()
                await asyncio.sleep(1)
                print('wait_msg')
        finally:
            if self.client is not None:
                print('off line')
                await self.client.disconnect()

        self.isconn = False

    async def mqtt_upload_thread(self):
        #        my_dht = dht.DHT11(Pin(14, Pin.IN))
        dht_data = {
            'temperature': 0,
            'humidity': 0
        }

        while True:
            if self.isconn == True:
                #  my_dht.measure()
                #  dht_data['temperature'] = my_dht.temperature()
                #  dht_data['humidity']    = my_dht.humidity()
                print(dht_data)
                await self.client.publish(self.topic_sta, json.dumps(dht_data), retain=True)

            await asyncio.sleep(10)

        while True:
            if self.isconn == True:
                await self.client.ping()
            await asyncio.sleep(5)


def main():
    mip = MyIotPrj()

    loop = asyncio.get_event_loop()
    loop.create_task(mip.mqtt_main_thread())
    loop.create_task(mip.mqtt_upload_thread())
    loop.run_forever()


if __name__ == '__main__':
    main()
