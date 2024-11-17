import random
import time


class ServiceS:
    def __init__(self, is_overloaded=False, failure_rate=0.0, response_time=0.0):
        self.is_overloaded = is_overloaded
        self.failure_rate = failure_rate
        self.response_time = response_time
        self.data = {i: f"Data from S for user {i}" for i in range(1000)}

    def get_data(self, user_id):
        time.sleep(self.response_time)  # Добавляем задержку
        if self.is_overloaded or random.random() < self.failure_rate:
            raise Exception("Service S is overloaded")
        return self.data.get(user_id, None)
