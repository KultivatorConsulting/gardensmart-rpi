import smbus
import sys

DEVICE_BUS = 1
DEVICE_ADDR = 0x10
RELAY_ON = 0xFF
RELAY_OFF = 0x00

bus = smbus.SMBus(DEVICE_BUS)

def relay_on(relay_num):
  bus.write_byte_data(DEVICE_ADDR, relay_num, RELAY_ON)

def relay_off(relay_num):
  bus.write_byte_data(DEVICE_ADDR, relay_num, RELAY_OFF)

def relay_get_port_status(relay_num):
  return True if bus.read_byte_data(DEVICE_ADDR, relay_num) == RELAY_ON else False
