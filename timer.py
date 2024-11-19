import time

def get_ms(time_start):
    ms = (time.time() - time_start) * 1000
    return f"{ms:.2f} ms"