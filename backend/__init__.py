import sys

# Emoji in log output must never crash the app on Windows (cp1252) consoles.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
