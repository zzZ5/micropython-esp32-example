import ujson as json


def read_confg():
    with open("config.json") as f:
        a = json.load(f)
        print(a)


read_confg()
