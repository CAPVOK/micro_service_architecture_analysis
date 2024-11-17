import random

import yaml

from services import ServiceP, ServiceQ, ServiceS, ServiceT


def run_simulation(config):
    num_requests = config["simulation"]["num_requests"]

    # Инициализация служб с параметрами из конфигурации, с использованием значений по умолчанию
    service_t = ServiceT(
        is_down=config["services"]["service_t"].get("is_down", False),
        failure_rate=config["services"]["service_t"].get("failure_rate", 0.0),
        response_time=config["services"]["service_t"].get("response_time", 0.0),
    )

    service_s = ServiceS(
        is_overloaded=config["services"]["service_s"].get("is_overloaded", False),
        failure_rate=config["services"]["service_s"].get("failure_rate", 0.0),
        response_time=config["services"]["service_s"].get("response_time", 0.0),
    )

    service_q = ServiceQ(service_t, service_s)

    service_p = ServiceP(
        service_q, expect_404=config["services"]["service_p"].get("expect_404", False)
    )

    success_requests = 0
    failures = 0
    for _ in range(num_requests):
        user_id = random.randint(0, 999)
        try:
            service_p.request_data(user_id)
            success_requests += 1
        except Exception as e:
            failures += 1
    return success_requests, failures


if __name__ == "__main__":
    # Загрузка конфигурации
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)

    success, fail = run_simulation(config)
    print(f"Успешных запросов: {success}, Сбоев: {fail}")
