# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import json
import threading


class EmqService(threading.Thread):
    def __init__(self):
        # BCM GPIO编号
        threading.Thread.__init__(self)
        self.client = mqtt.Client()
        self.pins = [17, 18, 27, 22, 23, 24, 25, 4]
    def run(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.gpio_setup()

        try:
            # 请根据实际情况改变MQTT代理服务器的IP地址
            self.client.connect("120.77.171.20", 1883, 60)
            self.client.loop_forever()
        except KeyboardInterrupt:
            self.client.disconnect()
            self.gpio_destroy()

    def gpio_setup(self):
        # 采用BCM编号
        GPIO.setmode(GPIO.BCM)
        # 设置所有GPIO为输出状态，且输出低电平
        for pin in self.pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

    def gpio_destroy(self):
        for pin in self.pins:
            GPIO.output(pin, GPIO.LOW)
            GPIO.setup(pin, GPIO.IN)

    # 连接成功回调函数
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        # 连接完成之后订阅gpio主题
        client.subscribe("luoromeo-rpi-gpio")

    # 消息推送回调函数
    def on_message(self, client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))
        # 获得负载中的pin 和 value
        gpio = json.loads(str(msg.payload))

        if gpio['pin'] in self.pins:
            if gpio['value'] == 0:
                GPIO.output(gpio['pin'], GPIO.LOW)
            else:
                GPIO.output(gpio['pin'], GPIO.HIGH)


emqService = EmqService()
emqService.start()