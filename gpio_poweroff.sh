#!/bin/bash
#利用echo输出一些提示语句
echo export pin $1 value $2
echo $1 > /sys/class/gpio/export

echo setting direction to output
echo out > /sys/class/gpio/gpio$1/direction

echo setting pi
echo $2 > /sys/class/gpio/gpio$1/value