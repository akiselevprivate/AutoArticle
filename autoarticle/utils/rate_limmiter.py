import time
from threading import Lock
from settings.logger import logger
from openai import RateLimitError
from settings.settings import settings


class RateLimiter:
    # https://platform.openai.com/docs/guides/rate-limits/rate-limits-in-headers

    def __init__(self):
        self.logger = logger
        self.lock = Lock()
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def calculate_total_price(self):
        input_price = (
            self.total_input_tokens / 1000 * settings.PRICE_PER_THOUSAND_INPUT_TOKENS
        )
        output_price = (
            self.total_output_tokens / 1000 * settings.PRICE_PER_THOUSAND_OUTPUT_TOKENS
        )
        return input_price, output_price

    def request(self, func):
        def wrap(*args, **kwargs):
            def req(*args, **kwargs):
                response = func(*args, **kwargs)
                completion, usage = response
                self.total_input_tokens += usage.prompt_tokens
                self.total_output_tokens += usage.completion_tokens
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
