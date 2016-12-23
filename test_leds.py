#!/usr/bin/env python

from strip import Strip

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
SPI_BUS = 0
SPI_DEVICE = 0


def main():
    init_logging(logging.INFO)

    signal.signal(signal.SIGINT, signal_handler)

    strip = Strip(NUM_LEDS, SPI_BUS, SPI_DEVICE)

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


