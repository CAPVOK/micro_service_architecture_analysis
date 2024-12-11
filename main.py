import statistics

import simpy
import yaml

from services import ServiceP, ServiceQ, ServiceS, ServiceT


def run_simulation(config):
    env = simpy.Environment()

    # Инициализируем сервисы на основе конфигурации
    t_service = ServiceT(
        env,
        read_failure_probability=config["T"]["read_failure_probability"],
        write_failure_probability=config["T"]["write_failure_probability"],
    )

    s_service = ServiceS(
        env,
        read_failure_probability=config["S"]["read_failure_probability"],
        write_failure_probability=config["S"]["write_failure_probability"],
        max_write_time=config["S"]["max_write_time"],
        max_read_time=config["S"]["max_read_time"],
        concurrency_limit=config["S"]["concurrency_limit"],
    )

    q_service = ServiceQ(
        env,
        response_timeout=config["Q"]["response_timeout"],
        service_t=t_service,
        service_s=s_service,
    )

    p_service = ServiceP(
        env,
        q_service=q_service,
        arrival_process=config["P"]["arrival_process"],
        mean_interarrival=config["P"]["mean_interarrival"],
        read_probability=config["P"]["read_probability"],
        num_requests=config["P"]["num_requests"],
    )

    # Запускаем симуляцию
    env.run()

    # После завершения собираем результаты
    results = (
        p_service.results
    )  # предполагается, что P хранит список (req_type, req_id, result)
    # Подсчёт успешных/неуспешных запросов и среднего времени
    # Предположим, что для времени ответа у нас есть start_time/end_time внутри P или Q,
    # либо мы можем модифицировать P, чтобы он хранил (req_type, req_id, result, time).

    # Если в p_service.results только (req_type, req_id, result), добавим время в P
    # Например, пусть P хранит (req_type, req_id, result, duration):
    # Если этого нет, доработайте P для записи времени (start_time/end_time) запроса.

    # Предположим, что теперь p_service.results = [(req_type, req_id, result, duration), ...]
    successes = sum(
        1 for r in results if r[2] == "OK" or (r[0] == "read" and "data" in r[2])
    )
    errors = len(results) - successes
    times = [r[5] for r in results]  # duration из четвертого элемента кортежа
    avg_time = statistics.mean(times) if times else 0.0

    summary = {
        "successes": successes,
        "errors": errors,
        "avg_time": avg_time,
        "times": times,
        "details": results,
    }

    return summary


if __name__ == "__main__":
    # Читаем конфиг
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    summary = run_simulation(config)

    print("Simulation summary:")
    print(f"Successes: {summary['successes']}")
    print(f"Errors: {summary['errors']}")
    print(f"Avg Time: {summary['avg_time']:.4f}")
