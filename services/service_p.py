import random


class ServiceP:
    def __init__(self, env, q_service, request_rate, read_probability):
        self.env = env
        self.q_service = q_service
        self.request_rate = request_rate
        self.read_probability = read_probability
        self.action = env.process(self.run())

    def run(self):
        req_id_counter = 0
        while True:
            # Генерируем запросы с интенсивностью request_rate
            interarrival = 1.0 / self.request_rate
            yield self.env.timeout(interarrival)
            req_id_counter += 1
            # Определяем тип запроса
            if random.random() < self.read_probability:
                req_type = "read"
            else:
                req_type = "write"
            data = f"data_{req_id_counter}" if req_type == "write" else None

            # Обрабатываем запрос
            result = yield self.env.process(
                self.q_service.process_request(req_type, req_id_counter, data)
            )
            # Можно логировать результат
            print(
                f"Time {self.env.now}: P got response for {req_type} {req_id_counter} -> {result}"
            )
