import random
import time


class ServiceT:
    def __init__(self, is_down=False, failure_rate=0.0, response_time=0.0):
        self.is_down = is_down
        self.failure_rate = failure_rate
        self.response_time = response_time
        self.data = {i: f"Data from T for user {i}" for i in range(1000)}

    def get_data(self, user_id):
        time.sleep(self.response_time)  # Добавляем задержку
        if self.is_down or random.random() < self.failure_rate:
            raise Exception("Service T is down")
        return self.data.get(user_id, None)
