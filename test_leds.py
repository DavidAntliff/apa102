#!/usr/bin/env python

import spidev
import random
import time
import signal

import logging

logger = logging.getLogger(__name__)

def init_logging(log_level):
    logging.basicConfig(level=log_level)

# catch signals for tidy exit
_exiting = False
def signal_handler(signal, frame):
    global _exiting
    _exiting = True

NUM_LEDS = 60
MAX_BRIGHTNESS = 31
MAX_RGB = 255

class Strip(object):
    def __init__(self, num_LEDs, spi):
        self._num_LEDs = num_LEDs
        self._leds = all_off(self._num_LEDs)
        self._spi = spi

    def set_led(self, pos, red, green, blue, brightness=MAX_BRIGHTNESS):
        try:
            self._leds[pos].set(red, green, blue, brightness)
        except IndexError:
            logger.error("LED pos {0} out of range".format(pos))

    def set_all(self, red, green, blue, brightness=MAX_BRIGHTNESS):
        for led in self._leds:
            led.set(red, green, blue, brightness)

    def set_all_off(self):
        for led in self._leds:
            led.set(0, 0, 0, 0)

    def update(self):
        render(self._spi, self._leds)

def constrain_rgb(x):
    return int(max(0, min(MAX_RGB, x))) 

def constrain_brightness(x):
    return int(max(0, min(MAX_BRIGHTNESS, x)))

class LEDState(object):
    def __init__(self, red, green, blue, brightness=MAX_BRIGHTNESS):
        self.set(red, green, blue, brightness)

    def set(self, red, green, blue, brightness=MAX_BRIGHTNESS):
	self.set_red(red)
	self.set_green(green)
	self.set_blue(blue)
	self.set_brightness(brightness)

    def set_red(self, red):
        self._red = constrain_rgb(red)

    def set_green(self, green):
        self._green = constrain_rgb(green)

    def set_blue(self, blue):
        self._blue = constrain_rgb(blue)

    def set_brightness(self, brightness):
        self._brightness = constrain_brightness(brightness)

    def render(self):
        return [ 0xe0 + self._brightness, self._blue, self._green, self._red ]

def set_all(num, red, green, blue, brightness=MAX_BRIGHTNESS):
    states = []
    for i in range(num):
        states.append(LEDState(red, green, blue, brightness))
    return states

def all_off(num):
    return set_all(num, 0, 0, 0, 0)

def render(spi, states):
    to_send = [0x00, 0x00, 0x00, 0x00]
    for state in states:
        to_send += state.render()
    num_leds = len(states)
    num_end_bits = (num_leds + 1) / 2
    num_end_bytes = (num_end_bits + 7) / 8
    to_send += [0x00] * num_end_bytes
    logger.debug(to_send)
    spi.xfer(to_send)

def main():
    init_logging(logging.INFO)

    signal.signal(signal.SIGINT, signal_handler)

    bus = 0
    device = 0
    spi = spidev.SpiDev()
    spi.open(bus, device)

#    led_states = all_off(num_leds)
#    led_states = set_all(num_leds, 0, 0, 0xff)
#    render(spi, led_states)

    strip = Strip(NUM_LEDS, spi)

    updates = 0
    start_time = time.time()
    last_report_time = start_time
    while not _exiting:
        strip.set_all(random.randint(0, 255), random.randint(0, 255), random.randint(0,255), 1)
        strip.update()
        time.sleep(0.15)
        updates += 1
        now = time.time()
        if now - last_report_time > 1.0:
            elapsed = now - start_time
            updates_per_second = updates / elapsed
            logger.info("Updates per second: {0}".format(updates_per_second))
            last_report_time = now

    strip.set_all_off()
    strip.update()
    
if __name__ == "__main__":
    main()


