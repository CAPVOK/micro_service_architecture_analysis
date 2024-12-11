import random


class ServiceT:
    def __init__(self, env, read_failure_probability, write_failure_probability):
        self.env = env
        self.read_failure_probability = read_failure_probability
        self.write_failure_probability = write_failure_probability
        self.storage = {}

    def read(self, req_id):
        # Операция мгновенная, но есть вероятность отказа
        if random.random() < self.read_failure_probability:
            raise RuntimeError("T failed")
        if req_id not in self.storage:
            raise RuntimeError("T: data not found")
        return self.storage[req_id]

    def write(self, req_id, data):
        # Аналогично, мгновенно, но с вероятностью отказа
        if random.random() < self.write_failure_probability:
            raise RuntimeError("T failed")
        self.storage[req_id] = data
