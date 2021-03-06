# coding=utf-8
import pytz
import urllib
import urllib2
import datetime
import json
import sys
import threading
import socket
import time
import logging
import random
import Adafruit_DHT
import StringIO
import traceback
from wave_share_43inch_epaper import *

# SERVER_URL = "http://你的服务器提供的API地址”
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

BMPS = {"ABUG": "ABUG.BMP", "ACAT": "ACAT.BMP", "ADOG": "ADOG.BMP", "ADRG": "ADRG.BMP", "AFISH": "AFISH.BMP",
        "APIG": "APIG.BMP", "ASHEEP": "ASHEEP.BMP", "ATUR": "ATUR.BMP", "EANGRY": "EANGRY.BMP", "ECOOL": "ECOOL.BMP",
        "ECRY": "ECRY.BMP", "ECUTE": "ECUTE.BMP", "EHAPPY": "EHAPPY.BMP", "EKISS": "EKISS.BMP", "EKL": "EKL.BMP",
        "ELOVE": "ELOVE.BMP", "EQUES": "EQUES.BMP", "ESAD": "ESAD.BMP", "ESURP": "ESURP.BMP", "EWINK": "EWINK.BMP",
        "FBERRY": "FBERRY.BMP", "FCHAMP": "FCHAMP.BMP", "FGRAP": "FGRAP.BMP", "FLEMO": "FLEMO.BMP",
        "FMILK": "FMILK.BMP", "FNUT": "FNUT.BMP", "FRES": "FRES.BMP", "FTOM": "FTOM.BMP", "FWINE": "FWINE.BMP",
        "LBOOK": "LBOOK.BMP", "LFAN": "LFAN.BMP", "LFILM": "LFILM.BMP", "LGALSS": "LGALSS.BMP", "LGAME": "LGAME.BMP",
        "LIKE": "LIKE.BMP", "LMONEY": "LMONEY.BMP", "LSAN": "LSAN.BMP", "LTEMP": "LTEMP.BMP", "LTIME": "LTIME.BMP",
        "LTS": "LTS.BMP", "LTV": "LTV.BMP", "LZHEN": "LZHEN.BMP", "ODNA": "ODNA.BMP", "ODOWN": "ODOWN.BMP",
        "OGUN": "OGUN.BMP", "OIDEA": "OIDEA.BMP", "OLIGHT": "OLIGHT.BMP", "OMUSH": "OMUSH.BMP", "OMUSIC": "OMUSIC.BMP",
        "ONEWS": "ONEWS.BMP", "ORECY": "ORECY.BMP", "ORING": "ORING.BMP", "OTREE": "OTREE.BMP", "OUP": "OUP.BMP",
        "OWARN": "OWARN.BMP", "PCOOK": "PCOOK.BMP", "PFREE": "PFREE.BMP", "PGIRL": "PGIRL.BMP", "PMODE": "PMODE.BMP",
        "PPLICE": "PPLICE.BMP", "QT1": "QT1.BMP", "QT2": "QT2.BMP", "PSHOP": "PSHOP.BMP", "PSIT": "PSIT.BMP",
        "PTWO": "PTWO.BMP", "PWOM": "PWOM.BMP", "PYOGA": "PYOGA.BMP"}

WEATHER = {u"小雨": "WXYU.BMP", u"中雨": "WZYU.BMP", u"大雨": "WDYU.BMP", u"暴雨": "WWET.BMP",
           u"晴": "WQING.BMP", u"多云": "WDYZQ.BMP", u"阴": "WYIN.BMP",
           u"雷阵雨": "WLZYU.BMP", u"阵雨": "WYGTQ.BMP",
           u"霾": "WFOG.BMP", u"雾": "WWU.BMP",
           u"雪": "WXUE.BMP", u"雨夹雪": "WYJX.BMP", u"冰雹": "WBBAO.BMP",
           u"月亮": "WMOON.BMP", u"深夜": "WSLEEP.BMP", u"日落": "SUMSET.BMP", u"日出": "SUNRISE.BMP"}

GAP = 0.1

# 日志模块
logfile = 'log.txt'
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename=logfile,
                    filemode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class WeatherService(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.init = False
        self.city = None
        self.word = "hello world."
        self.weather = None
        self.screen = None
        self.summary = "today is a good day"
        self.gift = "auto"
        self.status = ""
        # first load data when init
        self.load_data()
        self.init_screen()

    def init_screen(self):
        self.screen = Screen('/dev/ttyAMA0')
        self.screen.connect()
        self.screen.handshake()
        # 需要准备一张TF卡
        #self.screen.load_pic()
        #time.sleep(5)
        self.screen.clear()
        self.screen.set_memory(MEM_SD)
        self.screen.set_rotation(ROTATION_180)

    def run(self):
        while True:
            try:
                if self.connect_network():
                    self.status = "ONLINE"
                else:
                    self.status = "OFFLINE"
                # self.summary = "cpu温度:%s" % pi_status.CPU_temp
                if self.init:
                    print '更新时间...'
                    logger.info("refresh screen")
                    self.update_data()
                    self.update_screen()
                    sleep_second = 60 - self.get_second()
                    print '睡眠时间为%s' % sleep_second
                    time.sleep(sleep_second)
                else:
                    print '初始化加载数据...'
                    self.load_data()
                    time.sleep(10)
            except Exception as e:
                fp = StringIO.StringIO()  # 创建内存文件对象
                traceback.print_exc(file=fp)
                message = fp.getvalue()
                logger.error("serial error, reconnect e-paper, error %s" % message)
                try:
                    self.screen.disconnect()
                except Exception as err:
                    logger.warning("disconnect error")
                self.screen = None
                self.init_screen()
                time.sleep(10)
            else:
                None

    '''update e-paper screen display'''

    def update_screen(self):
        self.screen.clear()
        self.show_datetime()
        self.show_status()
        self.show_weather()
        self.show_tomorrow()
        self.show_gift()
        self.show_message()
        self.screen.update()

    def show_datetime(self):
        clock_x = 40
        clock_y = 40
        temp_x = 0
        time_string, date_string, week_string = self.get_datetime()
        if time_string[0] == '0':
            time_string = time_string[1:]
            temp_x += 40
        for c in time_string:
            bmp_name = 'NUM{}.BMP'.format('S' if c == ':' else c)
            self.screen.bitmap(clock_x + temp_x, clock_y, bmp_name)
            temp_x += 70 if c == ':' else 100
        self.screen.set_ch_font_size(FONT_SIZE_48)
        self.screen.set_en_font_size(FONT_SIZE_48)
        self.screen.text(530, 40, date_string)
        self.screen.text(560, 95, week_string)
        self.screen.line(0, clock_y + 160, 800, clock_y + 160)
        self.screen.line(0, clock_y + 161, 800, clock_y + 161)
        logger.info("now time -> %s" % time_string)

    def show_gift(self):
        gift_x = SCREEN_WIDTH - 200
        gift_y = 210
        # random select a item
        key = random.choice(BMPS.keys())
        bmp_name = BMPS.get(key)
        if self.gift != "auto":
            bmp_name = self.gift
        self.screen.bitmap(gift_x, gift_y, bmp_name)
        logger.info("show gift %s" % bmp_name)

    def show_weather(self):
        cw = self.weather["weather"]
        bmp_name = WEATHER.get(cw, None)
        if not bmp_name:
            if u'雨' in cw:
                bmp_name = 'WZYU.BMP'
            elif u'雪' in cw:
                bmp_name = 'WXUE.BMP'
            elif u'雹' in cw:
                bmp_name = 'WBBAO.BMP'
            elif u'雾' in cw or u'霾' in cw:
                bmp_name = 'WWU.BMP'
        if bmp_name:
            self.screen.bitmap(10, 260, bmp_name)

        title_x = 220
        title_font = FONT_SIZE_32
        title_font_size = 32

        tile_margin_top = 5

        value_font = FONT_SIZE_48
        value_font_size = 48

        weather_font = FONT_SIZE_64
        weather_font_size = 64

        small_temp_font = FONT_SIZE_32
        small_temp_font_size = 32

        weather_x = 300
        weather_y = 220
        line_spacing = 8

        # 偏移量
        city_y = weather_y + tile_margin_top
        temp_y = weather_y + weather_font_size + (line_spacing / 2)
        outside_y = temp_y + small_temp_font_size + line_spacing
        inside_y = outside_y + value_font_size + line_spacing
        air_y = inside_y + value_font_size + line_spacing

        pm25_y = air_y + value_font_size + line_spacing

        self.screen.set_ch_font_size(title_font)
        self.screen.set_en_font_size(title_font)

        # part 1
        city_name = self.weather["city"]
        self.screen.text(title_x - (self.screen.get_text_width(city_name, title_font) - title_font_size * 2), city_y,
                         city_name)  # 默认城市只有两个字,超过的要向前移

        self.screen.text(title_x, outside_y + tile_margin_top, u"室外")

        self.screen.text(title_x, inside_y + tile_margin_top, u"室内")

        self.screen.text(title_x - (self.screen.get_text_width(u"空气质量", title_font) - title_font_size * 2),
                         air_y + tile_margin_top,
                         u"空气质量")

        self.screen.text(title_x - (self.screen.get_text_width(u"PM2.5", title_font) - title_font_size * 2),
                         pm25_y + tile_margin_top,
                         u"PM2.5")

        # part 2
        self.screen.set_ch_font_size(weather_font)
        self.screen.set_en_font_size(weather_font)

        self.screen.text(weather_x, weather_y, cw)

        self.screen.set_ch_font_size(small_temp_font)
        self.screen.set_en_font_size(small_temp_font)
        fmt = u"{hight_temp}-{low_temp}℃ {wd}{ws}"
        self.screen.text(weather_x, temp_y, fmt.format(**self.weather))  # 今日温度详情显示

        # part 3
        self.screen.set_ch_font_size(value_font)
        self.screen.set_en_font_size(value_font)
        fmt = u"{temp}℃-{hum}"
        self.screen.text(weather_x, outside_y, fmt.format(**self.weather))  # 室外实时温度

        fmt = u"{temp}℃-{humidity}%"
        home_air = self.get_home_air();
        self.screen.text(weather_x, inside_y, fmt.format(**home_air))  # 室内实时温度

        fmt = u"{aqi} {air_desc}"
        if len(self.weather["air_desc"]) > 3:
            fmt = u"{air_desc}"
        self.screen.text(weather_x, air_y, fmt.format(**self.weather))  # 空气质量

        self.screen.text(weather_x, pm25_y - tile_margin_top, self.weather["pm25"])  # PM2.5

        self.show_tomorrow()

    def show_tomorrow(self):
        box_height = 230
        box_width = 230
        box_x = 550
        box_y = 360

        self.screen.line(box_x, box_y, box_x + box_width, box_y)

        self.screen.line(box_x, box_y + 48 + 10, box_x + box_width, box_y + 48 + 10)

        self.screen.line(box_x, box_y, box_x, box_y + box_height)

        self.screen.line(box_x + box_width, box_y, box_x + box_width, box_y + box_height)

        self.screen.line(box_x, box_y + box_height, box_x + box_width, box_y + box_height)

        self.screen.set_ch_font_size(FONT_SIZE_32)
        self.screen.set_en_font_size(FONT_SIZE_32)
        #
        self.screen.text(box_x + 50, box_y + 12, u'明日预告')

        fmt = u"{weather} {hight_temp}-{low_temp}℃ {wd}{ws} 降水概率:{pcpn}"
        tomorrow = self.weather["tomorrow"]

        self.screen.wrap_text(box_x + 8, box_y + 48 + 20, box_width, fmt.format(**tomorrow))

        # self.screen.text(box_x + 50, box_y + 12, u'穿衣建议')
        #
        # self.screen.wrap_text(box_x + 8, box_y + 48 + 20, box_width, self.weather["suggestion"])

    def show_message(self):
        self.screen.set_ch_font_size(FONT_SIZE_32)
        self.screen.set_en_font_size(FONT_SIZE_32)
        self.screen.text(530, 155, self.summary)

        self.screen.set_ch_font_size(FONT_SIZE_32)
        self.screen.set_en_font_size(FONT_SIZE_32)
        speaker_x = 10
        speaker_y = SCREEN_HEIGHT - 48
        self.screen.bitmap(speaker_x, speaker_y, "SPEAK.BMP")

        message_x = speaker_x + 48
        message_y = SCREEN_HEIGHT - 50
        self.screen.text(message_x, message_y, self.word)

    def show_status(self):
        self.screen.set_ch_font_size(FONT_SIZE_32)
        self.screen.set_en_font_size(FONT_SIZE_32)
        self.screen.text(10, 210, self.status)

    '''update data'''

    def update_data(self):
        minute = time.strftime("%M", time.localtime())
        # every 30 minute update weather info
        if minute == 0 or minute == 30:
            self.load_data()

    def load_data(self):
        if self.connect_network():
            self.status = "ONLINE"
            # load configure
            self.load_configure()
            logger.debug("load configure")
            # load weather
            self.load_weather()
            logger.debug("load weather")
        else:
            self.status = "OFFLINE"
            logger.debug("network didn't connect")

    def get_datetime(self):
        tz = pytz.timezone('Asia/Shanghai')
        time_now = datetime.datetime.now(tz)
        time_string = time_now.strftime('%H:%M')
        date_string = time_now.strftime('%Y-%m-%d')
        week_string = [u'星期一', u'星期二', u'星期三', u'星期四', u'星期五', u'星期六', u'星期日'][time_now.isoweekday() - 1]
        return time_string, date_string, week_string

    def get_second(self):
        tz = pytz.timezone('Asia/Shanghai')
        time_now = datetime.datetime.now(tz)
        second_string = time_now.strftime('%S')
        return int(second_string)

    def get_home_air(self):
        h, t = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 4)
        print '获取温湿度数据成功:'
        print '温度: %s' % t
        print '湿度: %s' % h
        if self.connect_network():
           self.status = "OFFLINE"
        result = {'temp': int(t), 'humidity': int(h), 'update': int(time.time())}
        return result

    '''check is connect network'''

    def connect_network(self):
        try:
            name = socket.gethostbyname("baidu.com")
        except Exception as e:
            print e
            return False
        else:
            return True

    '''load configure from aliyun'''

    def load_configure(self):
        babyDay = self.get_babyDay()
        self.init = True
        self.city = '厦门'
        self.word = u"今天是宝宝出生的第%s天" % babyDay
        self.summary = "summary"
        self.gift = "gift"
        return True
        # data = self.request_json(SERVER_URL)
        # if data is not None:
        #     self.init = True
        #     self.city = data["city"]
        #     self.word = data["data"]
        #     self.summary = data["summary"]
        #     self.gift = data["gift"]
        #     return True
        # return False

    def get_babyDay(self):
        d1 = datetime.datetime(2016, 11, 22, 16, 28, 00)
        d2 = datetime.datetime.now()
        return (d2 - d1).days

    '''send http request to get json data'''

    def request_json(self, url):
        try:
            page = urllib.urlopen(url)
            html = page.read()
            json_data = json.loads(html)
        except Exception as e:
            logger.error("request json error")
            return None
        else:
            return json_data
        finally:
            None

    '''get weather info from public api'''

    def load_weather(self):
        if (self.city is not None) and self.init:
            print '开始获取天气数据...' + '当前城市为' + self.city
            # weather_url = "http://apis.baidu.com/apistore/weatherservice/cityid?cityid=" + str(self.city)
            weather_url = 'http://saweather.market.alicloudapi.com/area-to-weather?area=' + self.city + '&need3HourForcast=0&needAlarm=0&needHourData=0&needIndex=1&needMoreDay=0'
            try:
                req = urllib2.Request(weather_url)
                # api key
                req.add_header("Authorization", 'APPCODE 0c71c229301c4c10ae38857391efc635')
                html = urllib2.urlopen(req).read().decode('utf-8')
                json_datas = json.loads(html)
                # 验证请求是否成功
                if json_datas["showapi_res_code"] != 0:
                    print json_datas
                    pass
                # 获取天气信息
                basic = json_datas["showapi_res_body"]
                # 当前天气信息
                now = basic["now"]
                # 今日天气信息
                today = basic["f1"]
                # 穿衣建议
                suggestion = today["index"]['clothes']['desc']
                # 明天天气
                tomorrow = basic["f2"]
                # 空气质量
                air = now["aqiDetail"]
                # 城市
                city = basic["cityInfo"]["c3"]
                # 更新时间
                date_time = now["temperature_time"]

                # 当前温度
                temp = now["temperature"]
                # 当前湿度
                hum = now["sd"]

                # 天气描述
                weather = now["weather"]
                aqi = air['aqi']
                air_desc = air['quality']
                pm25 = str(air["pm2_5"])
                # 气温范围
                l_temp = today["night_air_temperature"]
                h_temp = today["day_air_temperature"]

                wind_desc = today["day_wind_direction"]
                wind_power = today["day_wind_power"]

                # 日出
                sun_rise = today["sun_begin_end"].split('|')[0]
                # 日落
                sun_set = today["sun_begin_end"].split('|')[1]

                content = {"city": city, "datetime": date_time, "weather": weather, "temp": temp, "hum": hum,
                           "low_temp": l_temp,
                           "hight_temp": h_temp, "wd": wind_desc, "ws": wind_power, "sun_rise": sun_rise,
                           "sun_set": sun_set, "aqi": aqi, "air_desc": air_desc, "pm25": pm25, "suggestion": suggestion}
                content["tomorrow"] = self.tomorrow_weather(tomorrow)
                print '天气获取成功'
                logging.warning(content)
                if content is not None:
                    self.weather = content
            except Exception as e:
                logger.error("get weather info error")
                return False
            else:
                return True
            finally:
                None
        else:
            logger.warning("city is None or not init")
            return None

    def tomorrow_weather(self, data):
        weather = data["day_weather"]
        # 气温范围
        l_temp = data["night_air_temperature"]
        h_temp = data["day_air_temperature"]

        wind_desc = data["day_wind_direction"]
        wind_power = data["day_wind_power"]
        #
        # 日出
        sun_rise = data["sun_begin_end"].split('|')[0]
        # 日落
        sun_set = data["sun_begin_end"].split('|')[1]
        # 降水量
        pcpn = data["jiangshui"]
        # 降水概率
        # pop = data["pop"]
        # hum = data["hum"]

        tomorrow = {"weather": weather, "low_temp": l_temp,
                    "hight_temp": h_temp, "wd": wind_desc, "ws": wind_power, "sun_rise": sun_rise, "sun_set": sun_set, "pcpn": pcpn}
        return tomorrow


service = WeatherService()
service.start()
