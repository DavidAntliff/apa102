#!/usr/bin/env python

import argparse
import time
import random
import operator
from collections import namedtuple, deque
import signal
import logging

from strip import Strip
from led import MAX_RGB

logger = logging.getLogger(__name__)


def init_logging(log_level):
    logging.basicConfig(level=log_level)

# catch signals for tidy exit
_exiting = False
def signal_handler(signal, frame):
    global _exiting
    _exiting = True


DEFAULT_NUM_LEDS = 120
DEFAULT_SPI_BUS = 0
DEFAULT_SPI_DEVICE = 0
DEFAULT_SPI_SPEED = 10000000  # 10MHz - above this is diminishing returns
DEFAULT_RATE = 5.0  # Hz
DEFAULT_BRIGHTNESS = 1


def main():
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", dest="debug", action="store_true", help="Show debugging output")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Show verbose output")
    parser.add_argument("-n", "--num-leds", dest="num_leds", type=int, help="Number of LEDs in strip", default=DEFAULT_NUM_LEDS)
    parser.add_argument("-o", "--offset", dest="offset", type=int, help="First LED to address", default=0)
    parser.add_argument("--spi-bus", dest="spi_bus", type=int, help="SPI bus", default=DEFAULT_SPI_BUS)
    parser.add_argument("--spi-device", dest="spi_device", type=int, help="SPI device", default=DEFAULT_SPI_DEVICE)
    parser.add_argument("--spi-speed", dest="spi_speed", type=int, help="SPI speed in Hz", default=DEFAULT_SPI_SPEED)
    parser.add_argument("-b", "--brightness", dest="brightness", type=int, help="Global brightness (0-31)", default=DEFAULT_BRIGHTNESS)

    subparsers = parser.add_subparsers(help="Subcommand help")
    random_flash_parser = subparsers.add_parser("flash", help="Random flash")
    random_flash_parser.add_argument("-r", "--rate", dest="rate", type=float, help="Animation rate (Hz)", default=5)
    random_flash_parser.add_argument("-d", "--dutycycle", dest="dutycycle", type=float, help="Duty cycle (on time, 1.0 = always on)", default=1.0)
    random_flash_parser.set_defaults(subparser="flash")

    rgb_fader_parser = subparsers.add_parser("fade", help="RGB fader")
    rgb_fader_parser.add_argument("-r", "--rate", dest="rate", type=float, help="Animation rate (Hz)", default=200)
    rgb_fader_parser.add_argument("-s", "--steps", dest="steps", type=int, help="Steps per target colour", default=100)
    rgb_fader_parser.set_defaults(subparser="fade")

    comet_parser = subparsers.add_parser("comet", help="Comet")
    comet_parser.add_argument("-s", "--speed", dest="speed", type=float, help="Speed of descent", default=100)
    comet_parser.add_argument("-l", "--length", dest="length", type=int, help="Length of tail", default=20)
    comet_parser.add_argument("-x", "--colour", dest="colour", choices={"red", "green", "blue"}, help="Colour", default="red")
    comet_parser.add_argument("-c", "--cycle", dest="cycle", action="store_true", help="Cycle comet colour")
    comet_parser.add_argument("-r", "--reverse", dest="reverse", action="store_true", help="Reverse direction")
    comet_parser.set_defaults(subparser="comet", brightness=31)

    chaser_parser = subparsers.add_parser("chaser", help="Chaser")
    chaser_parser.add_argument("-n", "--number", dest="number", type=int, help="Number of chasers", default=10)
    chaser_parser.add_argument("-s", "--speed", dest="speed", type=float, help="Speed of descent", default=100)
    chaser_parser.add_argument("-p", "--proximity", dest="proximity", type=int, help="Maximum distance between chasers", default=15)
    chaser_parser.add_argument("-l", "--length", dest="length", type=int, help="Length of chaser", default=10)
    chaser_parser.add_argument("-e", "--decrease", dest="decrease", action="store_true", help="Decrease length of chasers")
    chaser_parser.add_argument("-r", "--reverse", dest="reverse", action="store_true", help="Reverse direction")
    chaser_parser.set_defaults(subparser="chaser")

    pixel_parser = subparsers.add_parser("pixel", help="Direct pixel control")
    pixel_parser.add_argument("-p", "--pos", dest="position", type=int, help="LED position (0-based)", default=0)
    pixel_parser.add_argument("-r", "--red", dest="red", type=int, help="Red value (0-255)", default=0)
    pixel_parser.add_argument("-g", "--green", dest="green", type=int, help="Green value (0-255)", default=0)    
    pixel_parser.add_argument("-b", "--blue", dest="blue", type=int, help="Blue value (0-255)", default=0)    
    pixel_parser.add_argument("-l", "--length", dest="length", type=int, help="Number of pixels", default=1)
    pixel_parser.add_argument("-x", "--random", dest="random", action="store_true", help="Randomise colours")
    pixel_parser.set_defaults(subparser="pixel")

    all_parser = subparsers.add_parser("all", help="All LED control")
    all_parser.add_argument("-r", "--red", dest="red", type=int, help="Red value (0-255)", default=0)
    all_parser.add_argument("-g", "--green", dest="green", type=int, help="Green value (0-255)", default=0)    
    all_parser.add_argument("-b", "--blue", dest="blue", type=int, help="Blue value (0-255)", default=0)    
    all_parser.add_argument("-o", "--off", dest="off", action="store_true", help="All LEDS off")
    all_parser.add_argument("-x", "--random", dest="random", action="store_true", help="Randomise colours")
    all_parser.set_defaults(subparser="all")
    
    args = parser.parse_args()

    init_logging(logging.DEBUG if args.debug else (logging.INFO if args.verbose else logging.WARNING))

    if args.brightness >= 8:
        logger.warning("Beware excessive current draw! Recommend a lower brightness setting.")

    strip = Strip(args.num_leds, args.spi_bus, args.spi_device, args.spi_speed)
    strip.set_offset(args.offset)
    persist = False

    if args.subparser == "flash":
        demo_random_flash(strip, args.rate, args.brightness, args.dutycycle)
    elif args.subparser == "fade":
        demo_rgb_fader(strip, args.rate, args.steps, args.brightness)
    elif args.subparser == "comet":
        demo_comet(strip, args.speed, args.length, args.colour, args.cycle, args.reverse, args.brightness)
    elif args.subparser == "chaser":
        demo_chaser(strip, args.number, args.speed, args.proximity, args.length, args.decrease, args.reverse, args.brightness)
    elif args.subparser == "pixel":
        demo_pixel(strip, args.position, args.length, args.random, args.red, args.green, args.blue, args.brightness)
        persist = True
    elif args.subparser == "all":
        demo_all(strip, args.random, args.off, args.red, args.green, args.blue, args.brightness)
        persist = True

    if not persist:
        strip.set_all_off()
        strip.update()


def demo_random_flash(strip, rate, brightness=1, duty_cycle=1.0):
    """Rate in Hz."""
    delay_time = 1.0 / rate
    updates = 0
    start_time = time.time()
    last_report_time = start_time

    duty_cycle = max(0.01, min(1.0, duty_cycle))
    on_time = delay_time * duty_cycle
    off_time = delay_time * (1.0 - duty_cycle)
    logger.debug("on_time {}, off_time {}".format(on_time, off_time))

    while not _exiting:
        strip.set_all(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), brightness)
        strip.update()
        time.sleep(on_time)
        if off_time:
            strip.set_all_off()
            strip.update()
            time.sleep(off_time)
        updates += 1
        now = time.time()
        if now - last_report_time > 1.0:
            elapsed = now - start_time
            updates_per_second = updates / elapsed
            logger.info("Updates per second: {0}".format(updates_per_second))
            last_report_time = now


def demo_rgb_fader(strip, rate, steps, brightness):
    """Fade entire strip through a range of colours."""
    # red, green, blue
    targets = ((255,   0,   0),
               (255, 165,   0),  # orange
               (255, 255,   0),  # yellow
               (173, 255,  47),  # yellow green
               (  0, 255,   0),  # green
               ( 32, 178, 170),  # sea green
               (  0,   0, 255),  # blue
               (138,  43, 226))  # violet

    delay_time = 1.0 / rate
    steps_per_target = float(steps)  # must be a float
    step_count = 0
    rgb = (0, 0, 0)
    target = 0
    delta = tuple((y - x)/steps_per_target for x, y in zip(rgb, targets[target]))

    while not _exiting:
        if step_count < steps_per_target:
            rgb = tuple(map(operator.add, rgb, delta))
            step_count += 1
        else:
            rgb = targets[target]
            target = (target + 1) % len(targets)
            delta = tuple((y - x)/steps_per_target for x, y in zip(rgb, targets[target]))
            logger.info("Current {0}, new target: {1}, delta {2}".format(rgb, targets[target], delta))
            step_count = 0
        logger.debug("r {0}, g {1}, b {2}".format(rgb[0], rgb[1], rgb[2]))
        strip.set_all(rgb[0], rgb[1], rgb[2], brightness)
        strip.update()
        time.sleep(delay_time)


def demo_comet(strip, speed, length, colour, cycle, reverse, brightness):

    logger.warning("Brightness overridden: %d", brightness)
    if reverse:
        strip.reverse()
    pos = 0
    delay_time = 1. / speed

    mod = (0.0, 30.0 / (length / 20.0), 50.0 / (length / 20.0))
    if colour == "red":
        r_mod, g_mod, b_mod = mod
    elif colour == "green":
        g_mod, b_mod, r_mod = mod
    elif colour == "blue":
        b_mod, r_mod, g_mod = mod
    else:
        raise Exception("unknown colour")

    bright_mod = 2.5 / (length / 20.0)

    while not _exiting:
        for i in range(length):
            try:
                strip.set_led(pos - i, 255 - i * r_mod, 255 - i * g_mod, 255 - i * b_mod, brightness - i * bright_mod)
            except IndexError:
                pass
        try:
            strip.set_led(pos - length, 0, 0, 0, 0)
        except IndexError:
            pass
        strip.update()
        pos = (pos + 1) % (len(strip) + 2 * length)
        if cycle and pos == 0:
            x_mod = r_mod
            r_mod = g_mod
            g_mod = b_mod
            b_mod = x_mod
        time.sleep(delay_time)


def demo_chaser2(strip, number, speed, proximity, length, decrease, reverse, brightness):
    # TODO: INCOMPLETE
    class Chaser(object):
        def __init__(self, red, green, blue, length):
            self._red = red; self._green = green; self._blue = blue
            self._length = length
            self._pos = 0

        def go(self):
            self._pos = 0

        def update(self):
            self._pos += 1

    def mod_length(x):
        if decrease:
            k = length ** (1.0 / (number - 1.0))
            return int(length / k ** x + 0.5)
        else:
            return length

    # create a queue of Chasers
    chasers = [Chaser(random.randint(0, MAX_RGB), random.randint(0, MAX_RGB), random.randint(0, MAX_RGB), -i * proximity, mod_length(i)) for i in range(number)]

    running_queue = deque()
    waiting_queue = deque(chasers)
    count = 0

    while not _exiting:
        if count % proximity == 0:
            # start a new chaser
            if waiting_queue:
                chaser = waiting_queue.pop()
                chaser.go()
                running_queue.append(chaser)

            for chaser in running_queue:
                chaser.update()
            count += 1

def demo_chaser(strip, number, speed, proximity, length, decrease, reverse, brightness):

    pos = 0
    delay_time = 1.0 / speed

    Chaser = namedtuple("Chaser", ("red", "green", "blue", "offset", "length"))

    def mod_length(x):
        if decrease:
            k = length ** (1.0 / (number - 1.0))
            return int(length / k ** x + 0.5)
        else:
            return length

    chasers = [Chaser(random.randint(0, MAX_RGB), random.randint(0, MAX_RGB), random.randint(0, MAX_RGB), -i * proximity, mod_length(i)) for i in range(number)]
    logger.debug(chasers)

    if reverse:
        strip.reverse()
    
    while not _exiting:
        for chaser in chasers:
            for i in range(chaser.length):
                try:
                    strip.set_off(chaser.offset + pos - i)
                except IndexError:
                    pass
        pos = (pos + 1) % (len(strip) + number * proximity)
        logger.debug(pos)
        for chaser in chasers:
            for i in range(chaser.length):
                try:
                    strip.set_led(chaser.offset + pos - i, chaser.red, chaser.green, chaser.blue, brightness)
                except IndexError:
                    pass
        strip.update()
        time.sleep(delay_time)


def demo_pixel(strip, position, length, randomise, red, green, blue, brightness):
    for i in range(length):
        if randomise:
            red = random.randint(0, MAX_RGB)
            green = random.randint(0, MAX_RGB)
            blue = random.randint(0, MAX_RGB)
        strip.set_led(position + i, red, green, blue, brightness)
    strip.update()


def demo_all(strip, randomise, off, red, green, blue, brightness):
    if off:
        strip.set_all_off()
    else:
        if randomise:
            red = random.randint(0, MAX_RGB)
            green = random.randint(0, MAX_RGB)
            blue = random.randint(0, MAX_RGB)
        strip.set_all(red, green, blue, brightness)
    strip.update()
    
if __name__ == "__main__":
    main()
