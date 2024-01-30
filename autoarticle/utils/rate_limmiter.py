import time
from threading import Lock
from settings.logger import logger
from openai import RateLimitError


class RateLimiter:
    # https://platform.openai.com/docs/guides/rate-limits/rate-limits-in-headers

    def __init__(self):
        self.logger = logger
        self.lock = Lock()
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def request(self, func):
        def wrap(*args, **kwargs):
            def req(*args, **kwargs):
                response = func(*args, **kwargs)
                return response

            try:
                return req(*args, **kwargs)
            except RateLimitError as e:
                wait_time = float(e.request.headers["x-ratelimit-reset-tokens"][0:-1])
                logger.debug(f"Hit rate limmit witing for {wait_time}")
                if not self.lock.locked():
                    self.lock.acquire()
                    time.sleep(wait_time + 0.01)
                    responce = req(*args, **kwargs)
                    self.lock.release()
                    return responce
                else:
                    with self.lock:
                        return wrap(*args, **kwargs)

        return wrap
