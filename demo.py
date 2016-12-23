#!/usr/bin/env python

import argparse
import time
import random
import operator
import logging
logger = logging.getLogger(__name__)

def init_logging(log_level):
    logging.basicConfig(level=log_level)

# catch signals for tidy exit
import signal
_exiting = False
def signal_handler(signal, frame):
    global _exiting
    _exiting = True

from strip import Strip
    
DEFAULT_NUM_LEDS = 60
DEFAULT_SPI_BUS = 0
DEFAULT_SPI_DEVICE = 0
DEFAULT_RATE = 5.0 # Hz
DEFAULT_BRIGHTNESS = 1

def main():
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", dest="debug", action="store_true", help="Show debugging output")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Show verbose output")
    parser.add_argument("-n", "--num-leds", dest="num_leds", type=int, help="Number of LEDs in strip", default=DEFAULT_NUM_LEDS)
    parser.add_argument("--spi-bus", dest="spi_bus", type=int, help="SPI bus", default=DEFAULT_SPI_BUS)
    parser.add_argument("--spi-device", dest="spi_device", type=int, help="SPI device", default=DEFAULT_SPI_DEVICE)
    parser.add_argument("-b", "--brightness", dest="brightness", type=int, help="Global brightness (0-31)", default=DEFAULT_BRIGHTNESS)

    subparsers = parser.add_subparsers(help="Subcommand help")
    random_flash_parser = subparsers.add_parser("random_flash", help="Random flash")
    random_flash_parser.add_argument("-r", "--rate", dest="rate", type=float, help="Animation rate (Hz)", default=5)
    random_flash_parser.set_defaults(subparser="random_flash")

    rgb_fader_parser = subparsers.add_parser("rgb_fader", help="RGB fader")
    rgb_fader_parser.add_argument("-r", "--rate", dest="rate", type=float, help="Animation rate (Hz)", default=200)
    rgb_fader_parser.add_argument("-s", "--steps", dest="steps", type=int, help="Steps per target colour", default=100)
    rgb_fader_parser.set_defaults(subparser="rgb_fader")

    comet_parser = subparsers.add_parser("comet", help="Comet")
    comet_parser.add_argument("-s", "--speed", dest="speed", type=float, help="Speed of descent", default=100)
    comet_parser.add_argument("-l", "--length", dest="length", type=int, help="Length of tail", default=20)
    comet_parser.add_argument("-c", "--cycle", dest="cycle", action="store_true", help="Cycle comet colour")
    comet_parser.add_argument("-r", "--reverse", dest="reverse", action="store_true", help="Reverse direction")
    comet_parser.set_defaults(subparser="comet", brightness=31)

    args = parser.parse_args()

    init_logging(logging.DEBUG if args.debug else (logging.INFO if args.verbose else logging.WARNING))

    strip = Strip(args.num_leds, args.spi_bus, args.spi_device)

    if args.subparser == "random_flash":
        demo_random_flash(strip, args.rate, args.brightness)
    elif args.subparser == "rgb_fader":
        demo_rgb_fader(strip, args.rate, args.steps, args.brightness)
    elif args.subparser == "comet":
        demo_comet(strip, args.speed, args.length, args.cycle, args.reverse, args.brightness)

    strip.set_all_off()
    strip.update()
   
def demo_random_flash(strip, rate, brightness=1):
    """Rate in Hz."""
    delay_time = 1.0 / rate
    updates = 0
    start_time = time.time()
    last_report_time = start_time
    while not _exiting:
        strip.set_all(random.randint(0, 255), random.randint(0, 255), random.randint(0,255), brightness)
        strip.update()
        time.sleep(delay_time)
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

def demo_comet(strip, speed, length, cycle, reverse, brightness):

    if reverse:
        strip.reverse()
    pos = 0
    delay_time = 1. / speed

    r_mod = 0.0
    g_mod = 30.0 / (length / 20.0)
    b_mod = 50.0 / (length / 20.0)
    bright_mod = 2.5 / (length / 20.0)

    while not _exiting:
        for i in range(length):
            strip.set_led(pos - i, 255 - i * r_mod, 255 - i * g_mod, 255 - i * b_mod, brightness - i * bright_mod)
        strip.set_led(pos - length, 0, 0, 0, 0)
        strip.update()
        pos = (pos + 1) % (len(strip) + 2 * length)
        if cycle and pos == 0:
            x_mod = r_mod
            r_mod = g_mod
            g_mod = b_mod
            b_mod = x_mod
        time.sleep(delay_time)
        
if __name__ == "__main__":
   main()
