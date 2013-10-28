from __future__ import division, unicode_literals


def term256color(r, g, b, a):
    """Get the xterm-color palette entry for given color"""
    def f(v):
        if v < 0:
            return 0
        elif v > 5:
            return 5
        else:
            return round(v)
    term = a / 256 / 256 * 6
    r = f(r * term)
    g = f(g * term)
    b = f(b * term)
    return int(16 + r * 36 + g * 6 + b)


def image_to_term256(pil_image):
    """Convert image to a string that resembles it when printed on a terminal

    Needs a PIL image as input and a 256-color xterm for output.
    """
    result = []
    im = pil_image.convert('RGBA')
    try:
        from PIL import Image
    except ImportError:
        im.thumbnail((80, 80))
    else:
        im.thumbnail((80, 80), Image.ANTIALIAS)
    width, height = im.size
    for y in range(height // 2):
        try:
            for x in range(width):
                result.append('\033[48;5;%dm\033[38;5;%dm' % (
                    term256color(*im.getpixel((x, y * 2))),
                    term256color(*im.getpixel((x, y * 2 + 1)))))
                result.append('\N{LOWER HALF BLOCK}')
        finally:
            result.append('\033[0m\n')
    return ''.join(result)
