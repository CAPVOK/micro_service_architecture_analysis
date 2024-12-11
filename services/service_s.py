import random

import simpy


class ServiceS:
    def __init__(
        self,
        env,
        read_failure_probability,
        write_failure_probability,
        max_write_time,
        max_read_time,
        concurrency_limit,
    ):
        self.env = env
        self.read_failure_probability = read_failure_probability
        self.write_failure_probability = write_failure_probability
        self.max_write_time = max_write_time
        self.max_read_time = max_read_time
        self.resource = simpy.Resource(env, capacity=concurrency_limit)
        self.storage = {}

    def read(self, req_id):
        with self.resource.request() as req:
            yield req
            read_time = random.uniform(0, self.max_read_time)
            yield self.env.timeout(read_time)

            if random.random() < self.read_failure_probability:
                raise RuntimeError("S failed")

            if req_id not in self.storage:
                raise RuntimeError("S: data not found")

            return self.storage[req_id]

    def write(self, req_id, data):
        with self.resource.request() as req:
            yield req
            write_time = random.uniform(0, self.max_write_time)
            yield self.env.timeout(write_time)

            if random.random() < self.write_failure_probability:
                raise RuntimeError("S failed")

            self.storage[req_id] = data
