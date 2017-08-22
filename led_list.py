from led import LED, MAX_BRIGHTNESS


def set_all(num, red, green, blue, brightness=MAX_BRIGHTNESS):
    states = []
    for i in range(num):
        states.append(LED(red, green, blue, brightness))
    return states


def all_off(num):
    return set_all(num, 0, 0, 0, 0)
