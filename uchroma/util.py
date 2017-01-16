"""
Various helper functions that are used across the library.
"""
import struct
import time

from decorator import decorator

from grapefruit import Color
from numpy import interp


def clamp(value, min_, max_):
    """
    Constrain a value to the specified range

    :param value: Input value
    :param min_: Range minimum
    :param max_: Range maximum

    :return: The constrained value
    """
    return max(min_, min(value, max_))


def scale(value, src_min, src_max, dst_min, dst_max, round_=False):
    """
    Scale a value from one range to another.

    :param value: Input value
    :param src_min: Min value of input range
    :param src_max: Max value of input range
    :param dst_min: Min value of output range
    :param dst_max: Max value of output range
    :param round_: True if the scale value should be rounded to an integer

    :return: The scaled value
    """
    scaled = interp(clamp(value, src_min, src_max), [src_min, src_max], [dst_min, dst_max])
    if round_:
        scaled = int(round(scaled))

    return scaled


def rgb_from_tuple(arg: tuple) -> Color:
    """
    Convert a 3-tuple of ints or floats to a Grapefruit color

    :param arg: The RGB tuple to convert
    :return: The Color object
    """
    if len(arg) >= 3:
        return Color.NewFromRgb(clamp(arg[0], 0, 255) / 255.0,
                                clamp(arg[1], 0, 255) / 255.0,
                                clamp(arg[2], 0, 255) / 255.0)

    raise TypeError('Unable to convert %s (%s) to color' % (arg, type(arg[0])))


def rgb_to_int_tuple(arg: tuple) -> tuple:
    """
    Convert/sanitize a 3-tuple of ints or floats

    :param arg: Tuple of RGB values

    :return: Tuple of RGB ints
    """
    if len(arg) >= 3:
        return tuple([clamp(round(x), 0, 255) for x in arg[:3]])

    raise TypeError('Unable to convert %s (%s) to color' % (arg, type(arg[0])))


def to_color(arg) -> Color:
    """
    Convert various color representations to grapefruit.Color

    Handles RGB triplets, hexcodes, and html color names.

    :return: The color
    """
    if arg is None:
        return None
    if isinstance(arg, Color):
        return arg
    if isinstance(arg, str):
        return Color.NewFromHtml(arg)
    if isinstance(arg, tuple) or isinstance(arg, list):
        if isinstance(arg[0], list) or isinstance(arg[0], tuple) \
                or isinstance(arg[0], str) or isinstance(arg[0], Color):
            return [to_color(item) for item in arg]
        return rgb_from_tuple(arg)

    raise TypeError('Unable to parse color from \'%s\' (%s)' % (arg, type(arg)))


def to_rgb(arg) -> tuple:
    """
    Convert various representations to RGB tuples

    :return: An RGB int tuple
    """
    if arg is None:
        return (0, 0, 0)
    if isinstance(arg, Color):
        return arg.intTuple[:3]
    if isinstance(arg, str):
        return Color.NewFromHtml(arg).intTuple[:3]
    if isinstance(arg, tuple) or isinstance(arg, list):
        if isinstance(arg[0], list) or isinstance(arg[0], tuple) \
                or isinstance(arg[0], str) or isinstance(arg[0], Color):
            return [to_rgb(item) for item in arg]
        return rgb_to_int_tuple(arg)

    raise TypeError('Unable to parse color from \'%s\' (%s)' % (arg, type(arg)))


def colorarg(*decls):
    """
    Decorator to parse various color representations

    Invokes to_color on any arguments listed in decls. This will cause
    the listed arguments to be resolved to grapefruit.Color objects from
    the various different representations that might be in use.

    Example:

    @colorarg('color1', 'color2')
    def frobizzle(self, speed, color1=None, color2=None)

    """
    @decorator
    def wrapper(func, *args, **kwargs):
        """
        Replace arguments with appropriate Color objects
        """
        code = func.__code__
        names = code.co_varnames[:code.co_argcount]

        new_args = list(args)

        for argname in decls:
            pos = names.index(argname)
            if pos < len(args):
                new_args[pos] = to_color(args[pos])

        return func(*new_args, **kwargs)

    return wrapper



def scale_brightness(brightness, from_hw=False):
    """
    Converts a brightness value between float percentage (0 - 100)
    and an integer value (0 - 255). All API methods should deal in
    percentages, but interaction with the hardware will use the
    integer value.

    :param brightness: The brightness level
    :param from_hw: True if we are converting from integer to percentage

    :return: The scaled value
    """
    if from_hw:
        if brightness < 0 or brightness > 255:
            raise ValueError('Integer brightness must be between 0 and 255 (%d)' % brightness)

        if brightness is None:
            return 0.0

        return round(float(brightness) * (100.0 / 255.0), 2)

    if brightness < 0.0 or brightness > 100.0:
        raise ValueError('Float brightness must be between 0 and 100 (%f)' % brightness)

    if brightness is None:
        return 0

    return int(round(brightness * (255.0 / 100.0)))


def to_byte(value: int) -> bytes:
    """
    Convert a single int to a single byte
    """
    return struct.pack('=B', value)


def smart_delay(delay: float, last_cmd: float, remain: int=0) -> float:
    """
    A "smart" delay mechanism which tries to reduce the
    delay as much as possible based on the time the last
    delay happened.

    :param delay: delay in seconds
    :param last_cmd: time of last command
    :param remain: counter, skip delay unless it's zero

    :return: timestamp to feed to next invocation
    """
    now = time.perf_counter()

    if remain == 0 and last_cmd is not None and delay > 0.0:

        delta = now - last_cmd
        if delta < delay:
            sleep = delay - delta
            time.sleep(sleep)

    return now


def test_bit(value: int, bit: int) -> bool:
    """
    Test if the bit at the specified position is set.

    :param value: The value to test
    :param bit: The bit to check

    :return: True if the bit is set
    """
    return (value & 1 << bit) == 1 << bit


def set_bits(value: int, *bits) -> int:
    """
    Given a list of bools, set (or clear) the bits in
    value and return it as an int.

    :param value: The initial value
    :param bits: Tuple of bools

    :return: Integer with bits set or cleared
    """
    for bit in range(0, len(bits)):
        if bits[bit]:
            value |= 1 << bit
        else:
            value &= ~(1 << bit)

    return value

