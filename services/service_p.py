import logging
import random

# Настроим корневой логгер на INFO (можно потом менять уровень извне)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Установим DEBUG для более подробного вывода
handler = logging.StreamHandler()
formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


class ServiceP:
    def __init__(
        self,
        env,
        q_service,
        arrival_process="fixed_interval",
        mean_interarrival=0.2,
        read_probability=0.5,
        num_requests=50,
    ):
        self.env = env
        self.q_service = q_service
        self.arrival_process = arrival_process
        self.mean_interarrival = mean_interarrival
        self.read_probability = read_probability
        self.num_requests = num_requests

        self.completed_requests = 0
        self.written_ids = []  # Список успешно записанных id, чтобы было что читать.
        # results будет: (req_type, req_id, result, start_time, end_time, duration)
        self.results = []

        # Логируем начальную конфигурацию
        logger.info(
            f"ServiceP initialized with: arrival_process={arrival_process}, "
            f"mean_interarrival={mean_interarrival}, read_probability={read_probability}, "
            f"num_requests={num_requests}"
        )

        self.action = env.process(self.run())

    def run(self):
        logger.info("ServiceP starting request generation...")
        req_id_counter = 0

        while self.completed_requests < self.num_requests:
            interarrival = self.get_interarrival()
            yield self.env.timeout(interarrival)

            # Определяем тип запроса
            if self.written_ids and random.random() < self.read_probability:
                req_type = "read"
            else:
                req_type = "write"

            if req_type == "write":
                req_id_counter += 1
                current_req_id = req_id_counter
                data = f"data_{current_req_id}"
            else:
                # Если читаем, но нет данных - делаем запись
                if not self.written_ids:
                    logger.debug(
                        "No data available for reading, forcing a WRITE request."
                    )
                    req_type = "write"
                    req_id_counter += 1
                    current_req_id = req_id_counter
                    data = f"data_{current_req_id}"
                    logger.debug(
                        f"Forced WRITE request for id={current_req_id} at time={self.env.now:.4f}."
                    )
                else:
                    current_req_id = random.choice(self.written_ids)
                    data = None
                    logger.debug(
                        f"Generated READ request for id={current_req_id} at time={self.env.now:.4f}."
                    )

            start_time = self.env.now
            logger.debug(
                f"Sending {req_type.upper()} request (id={current_req_id}) to Q at time={start_time:.4f}..."
            )

            result = yield self.env.process(
                self.q_service.process_request(req_type, current_req_id, data)
            )

            end_time = self.env.now
            duration = end_time - start_time

            # Логируем результат запроса
            if req_type == "write":
                if result == "OK":
                    logger.info(
                        f"WRITE request (id={current_req_id}) succeeded at time={end_time:.4f}, "
                        f"duration={duration:.4f}. Data stored."
                    )
                else:
                    logger.warning(
                        f"WRITE request (id={current_req_id}) FAILED at time={end_time:.4f}, "
                        f"duration={duration:.4f}, result={result}"
                    )
            else:
                if result.startswith("ERROR"):
                    logger.warning(
                        f"READ request (id={current_req_id}) FAILED at time={end_time:.4f}, "
                        f"duration={duration:.4f}, result={result}"
                    )
                else:
                    logger.info(
                        f"READ request (id={current_req_id}) succeeded at time={end_time:.4f}, "
                        f"duration={duration:.4f}, returned data."
                    )

            # Сохраняем результат
            self.results.append(
                (req_type, current_req_id, result, start_time, end_time, duration)
            )

            # Если успешная запись - добавим id
            if req_type == "write" and result == "OK":
                self.written_ids.append(current_req_id)

            self.completed_requests += 1
            logger.debug(
                f"Completed {self.completed_requests}/{self.num_requests} requests so far."
            )

        logger.info("ServiceP finished generating requests.")

    def get_interarrival(self):
        if self.arrival_process == "poisson":
            val = random.expovariate(1.0 / self.mean_interarrival)
            logger.debug(f"Poisson arrival chosen, interval={val:.4f}")
            return val
        else:
            return self.mean_interarrival
