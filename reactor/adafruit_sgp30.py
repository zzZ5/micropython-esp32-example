import math
import time
from micropython import const

_SGP30_DEFAULT_I2C_ADDR = const(0x58)
_SGP30_FEATURESET = const(0x0022)

_SGP30_CRC8_POLYNOMIAL = const(0x31)
_SGP30_CRC8_INIT = const(0xFF)
_SGP30_WORD_LEN = const(2)

class Adafruit_SGP30:
    """
   SGP30:传感器驱动
    Args:
    	i2c: I2C对象.
    	Address int: (optional) 设备的I2C地址.

    """

    def __init__(self, i2c, address=_SGP30_DEFAULT_I2C_ADDR):
        """初始化传感器，获取序列号，并验证正确找到SGP30"""
        self._i2c = i2c
        self._addr = address

        # 获取唯一的序列
        self.serial = self._i2c_read_words_from_cmd([0x36, 0x82], 0.01, 3)
        # 获取功能集
        featureset = self._i2c_read_words_from_cmd([0x20, 0x2f], 0.01, 1)
        if featureset[0] != _SGP30_FEATURESET:
            raise RuntimeError('SGP30 Not detected')
        self.iaq_init()

    @property
    def tvoc(self):
        """总Tvoc(挥发性有机物)"""
        return self.iaq_measure()[1]

    @property
    def baseline_tvoc(self):
        """总挥发性有机化合物基准值"""
        return self.get_iaq_baseline()[1]

    @property
    def co2eq(self):
        """CO2当量"""
        return self.iaq_measure()[0]

    @property
    def baseline_co2eq(self):
        """CO2当量基准值"""
        return self.get_iaq_baseline()[0]

    def iaq_init(self):
        """初始化IAQ算法"""
        # name, command, signals, delay
        self._run_profile(["iaq_init", [0x20, 0x03], 0, 0.01])

    def iaq_measure(self):
        """测算 CO2eq 和 TVOC"""
        # name, command, signals, delay
        return self._run_profile(["iaq_measure", [0x20, 0x08], 2, 0.05])

    def get_iaq_baseline(self):
        """用IAQ算法获得CO2eq和TVOC的基准值"""
        # name, command, signals, delay
        return self._run_profile(["iaq_get_baseline", [0x20, 0x15], 2, 0.01])

    def set_iaq_baseline(self, co2eq, tvoc):
        """设置之前记录的CO2eq和TVOC的IAQ算法基线"""
        if co2eq == 0 and tvoc == 0:
            raise RuntimeError('Invalid baseline')
        buffer = []
        for value in [tvoc, co2eq]:
            arr = [value >> 8, value & 0xFF]
            arr.append(self._generate_crc(arr))
            buffer += arr
        self._run_profile(["iaq_set_baseline", [0x20, 0x1e] + buffer, 0, 0.01])

    def set_iaq_humidity(self, gramsPM3):
        """设置eCo2和TVOC补偿算法的湿度"""
        tmp = int(gramsPM3 * 256)
        buffer = []
        for value in [tmp]:
            arr = [value >> 8, value & 0xFF]
            arr.append(self._generate_crc(arr))
            buffer += arr
        self._run_profile(["iaq_set_humidity", [0x20, 0x61] + buffer, 0, 0.01])

    def set_iaq_rel_humidity(self, rh, temp):
        """为eCo2和TVOC补偿算法设置相对湿度"""
        gramsPM3 = rh/100.0 * 6.112 * math.exp(17.62*temp/(243.12+temp))
        gramsPM3 *= 216.7 / (273.15 + temp)

        self.set_iaq_humidity(gramsPM3)

    def _run_profile(self, profile):
        """运行配置文件"""
        name, command, signals, delay = profile

        return self._i2c_read_words_from_cmd(command, delay, signals)

    def _i2c_read_words_from_cmd(self, command, delay, reply_size):
        """运行sgp命令查询"""
        self._i2c.writeto(self._addr, bytes(command))
        time.sleep(delay)
        if not reply_size:
            return None
        crc_result = bytearray(reply_size * (_SGP30_WORD_LEN + 1))
        self._i2c.readfrom_into(self._addr, crc_result)
        result = []
        for i in range(reply_size):
            word = [crc_result[3*i], crc_result[3*i+1]]
            crc = crc_result[3*i+2]
            if self._generate_crc(word) != crc:
                raise RuntimeError('CRC Error')
            result.append(word[0] << 8 | word[1])
        return result

    def _generate_crc(self, data):
        """用于检查数据的8位CRC算法"""
        crc = _SGP30_CRC8_INIT
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ _SGP30_CRC8_POLYNOMIAL
                else:
                    crc <<= 1
        return crc & 0xFF
