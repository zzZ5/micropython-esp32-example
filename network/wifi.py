import time
import json
import network
import usocket as socket
import ure as re

addr = ("192.168.4.1", 80)

html0 = '''<!DOCTYPE html><html><meta charset="UTF-8"><meta http-equiv="X-UA-Compatible" content="IE=edge"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Compost</title><body><h2>堆肥反应器wifi连接设置</h2><form method="GET">wifi名:<br><select name="ssid">{options}</select><br><br>wifi密码:<br><input type="password" name="password" /><br><br><input type="submit" value="确定" /></from></body></html>'''

html1 = '''<!DOCTYPE html><html><body>success</body></html>'''

html2 = '''<!DOCTYPE html><html><body>This ssid or password was wrong!!! Please try again.</body></html>'''


def _html_sever():
    '''
    当WiFi连接失败，运行此函数，通过手机连接热点wifi-config浏览器访问192.168.4.1获取WiFi信息。
    '''

    # 获取所有可以连接wifi的信息
    sta = network.WLAN(network.STA_IF)  # 创建WLAN对象
    sta.active(True)
    time.sleep_ms(100)
    if sta.isconnected():
        return True
    set_wifi = set()
    for i in sta.scan():
        set_wifi.add(i[0])
    sta.active(False)
    options = ''
    for i in set_wifi:
        option = '<option value="{ssid}">{ssid}</option>'.format(
            ssid=i.decode('utf-8'))
        options += option
    print(options)

    is_connect = False
    ap = network.WLAN(network.AP_IF)  # 创建接入点界面
    ap.active(True)
    ap.config(essid='wifi-config')
    sk = socket.socket()
    sk.bind(addr)
    sk.listen(5)
    server = True
    while server:
        con, _ = sk.accept()
        data = con.recv(1024)  # 等待数据
        data_utf8 = str(data.decode('utf8'))  # 将接受的数据转换为utf8格式
        print(data_utf8)
        match = re.search(r"GET /\?ssid=(.*?)&password=(.*?) HTTP",
                          data_utf8)  # 从HTML返回的数据中获取WiFi信息
        if match:  # 如果获取到信息
            try:
                ssid = match.group(1)
                password = match.group(2)
                if _connect_wifi(ssid, password):
                    server = False
                    is_connect = True
                    _set_wifi_config(ssid, password)
                    con.sendall(html1)
                else:
                    con.sendall(html2)
            except:
                con.sendall(html2)
        else:
            con.sendall(html0.format(options=options))
        con.close()

    time.sleep(1)
    sk.close()
    ap.active(False)
    return is_connect


def _get_wifi_config():
    '''
    获取本地文件中的wifi配置。

    Returns:
        dict: 如果存在则返回格式为{'ssid':'', 'password':''}的字典
        bool: 如果不存在或者配置错误返回False。
    '''
    try:
        with open('wifi_config.json', 'r') as f:
            wifi_config = json.loads(f.read())
        return wifi_config
    except:
        return False


def _set_wifi_config(ssid, password):
    '''
    将WiFi信息写入wifi_config.json。

    Parameters:
        ssid(str): wifi名
        password(str): wifi密码

    Returns:
        bool: 设置成功返回True, 设置失败错误返回False。
    '''
    try:
        wifi_config = {'ssid': ssid, 'password': password}
        with open('wifi_config.json', 'w') as f:
            f.write(json.dumps(wifi_config))
        return True
    except:
        return False


def _connect_wifi(ssid, password):
    '''
    根据参数连接wifi。

    Parameter:
        ssid(str): wifi名
        password(str): wifi密码

    Returns:
        bool: 若连接成功，打印接口的IP/netmask/gw/DNS地址,返回True；若连接失败，返回False。
    '''
    wlan = network.WLAN(network.STA_IF)  # 创建WLAN对象
    wlan.active(True)  # 激活界面
    if not wlan.isconnected():  # 检查站点是否连接
        print('connecting to network...')
        wlan.connect(ssid, password)
        for i in range(12):  # 循环检查是否连接成功
            time.sleep_ms(500)
            if wlan.isconnected():  # 检查站点是否连接
                # 获取接口的IP/netmask/gw/DNS地址
                print('network config:', wlan.ifconfig())
                return True
            if i >= 11:
                print('connection failed')
                wlan.active(False)
                return False
    else:
        print('network config:', wlan.ifconfig())
        return True


def do_connect():
    '''
    优先连接本地保存的wifi，如果连接不上，则开启一个名为“wifi-config”的热点，
    连接上热点后，浏览器访问192.168.4.1输入要连接的WiFi信息
    若连接成功，打印接口的IP/netmask/gw/DNS地址,返回True；
    若连接失败，返回False。
    '''
    wifi_config = _get_wifi_config()
    if wifi_config:
        if _connect_wifi(wifi_config['ssid'], wifi_config['password']):
            _set_wifi_config(wifi_config['ssid'], wifi_config['password'])
            return True
        try:
            _html_sever()
        except:
            return False
    else:
        try:
            _html_sever()
        except:
            return False


def do_connect_local():
    '''
    只连接本地保存的wifi，直到连接上为止。
    '''

    is_connected = False
    wifi_config = _get_wifi_config()

    while not is_connected:
        is_connected = _connect_wifi(
            wifi_config['ssid'], wifi_config['password'])
