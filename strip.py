import math
import spidev
import logging

from led import MAX_BRIGHTNESS
from led_list import all_off

logger = logging.getLogger(__name__)


# SPI configuration
SPI_SPEED = 1000000  # 1 MHz
SPI_CPOL = 0
SPI_CPHA = 0


def render(spi, states):
    to_send = [0x00, 0x00, 0x00, 0x00]
    for state in states:
        to_send += state.render()
    num_leds = len(states)
    num_end_bytes = int(math.ceil(num_leds / 8.))
    to_send += [0x00] * num_end_bytes
    logger.debug("xfer [" + ", ".join(["{:X}".format(x) for x in to_send]) + "]")
    spi.xfer(to_send)


class Strip(object):
    def __init__(self, num_LEDs, bus, device, speed=None):
        self._num_LEDs = num_LEDs
        self._offset = 0
        self._reverse = False
        self._leds = all_off(self._num_LEDs)
        self._spi = spidev.SpiDev()
        self._spi.open(bus, device)
        self._spi.max_speed_hz = SPI_SPEED if speed is None else speed
        self._spi.mode = SPI_CPOL | SPI_CPHA
        self._spi.bits_per_word = 8
        #self._spi.no_cs = True
        #self._spi.lsbfirst = True
        logger.debug("LED Strip of {0} LEDS on SPI bus {1}, device {2}, speed {3} Hz, mode 0x{4:x}"
                     .format(num_LEDs, bus, device, self._spi.max_speed_hz, self._spi.mode))

    def __len__(self):
        return len(self._leds)

    def set_offset(self, offset):
        self._offset = offset

    def set_led(self, pos, red, green, blue, brightness=MAX_BRIGHTNESS):
        if pos < 0:
            raise IndexError("Negative position")
        try:
            self._leds[pos].set(red, green, blue, brightness)
        except IndexError:
            logger.debug("LED pos {0} out of range".format(pos))

    def set_off(self, pos):
        if pos < 0:
            raise IndexError("Negative position")
        try:
            self._leds[pos].set(0, 0, 0, 0)
        except IndexError:
            logger.debug("LED pos {0} out of range".format(pos))

    def set_all(self, red, green, blue, brightness=MAX_BRIGHTNESS):
        for led in self._leds:
            led.set(red, green, blue, brightness)

    def set_all_off(self):
        for led in self._leds:            
            led.set(0, 0, 0, 0)

    def update(self):
        leds = list(reversed(self._leds)) if self._reverse else self._leds
        pre_offset_leds = all_off(self._offset)
        render(self._spi, pre_offset_leds + leds)

    def reverse(self):
        """Reverse mapping of LEDs on strip."""
        self._reverse = not self._reverse
        logger.info("Strip mapping is now {0}".format("normal" if not self._reverse else "reversed"))
