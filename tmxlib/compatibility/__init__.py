import sys

py3 = (sys.version_info >= (3, 0))

if py3:
    # ord: convert byte to int
    ord_ = lambda x: x
else:
    # ord: convert byte to int
    ord_ = ord
