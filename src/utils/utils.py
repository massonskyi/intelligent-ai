import functools
import time
import traceback

LOGFILE = "ai_debug.log"

def log(msg, flush=True):
    # Пишет и в файл, и на экран/стдераут
    with open(LOGFILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
        f.flush()
    print(msg, flush=flush)  # Можно заменить на print(msg, file=sys.stderr, flush=flush)

def log_exc(e):
    # Логгирует traceback
    with open(LOGFILE, "a", encoding="utf-8") as f:
        traceback.print_exc(file=f)
        f.flush()
        
def time_it(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        msg = f"Time taken for {func.__name__}: {end_time - start_time:.2f} seconds"
        log(msg)
        return result
    return wrapper
