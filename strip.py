from led import MAX_BRIGHTNESS
from led_list import all_off

import spidev
import logging
logger = logging.getLogger(__name__)

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

class Strip(object):
    def __init__(self, num_LEDs, bus, device):
        self._num_LEDs = num_LEDs
        self._leds = all_off(self._num_LEDs)
        self._spi = spidev.SpiDev()
        self._spi.open(bus, device)
        logger.debug("LED Strip of {0} LEDS on SPI bus {1}, device {2}".format(num_LEDs, bus, device))

    def __len__(self):
        return len(self._leds)
        
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
