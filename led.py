import logging
logger = logging.getLogger(__name__)

MAX_BRIGHTNESS = 31
MAX_RGB = 255

LED_FRAME_BASE = 0xe0

def constrain_rgb(x):
    return int(max(0, min(MAX_RGB, x))) 

def constrain_brightness(x):
    return int(max(0, min(MAX_BRIGHTNESS, x)))

class LED(object):
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
        return [ LED_FRAME_BASE + self._brightness, self._blue, self._green, self._red ]
