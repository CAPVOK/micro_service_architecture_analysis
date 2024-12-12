import statistics

import simpy
import yaml

from services import ServiceP, ServiceQ, ServiceS, ServiceT


def run_simulation(config):
    env = simpy.Environment()

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

    # Читаем количество пользователей (экземпляров P), если нет — по умолчанию 1
    num_users = config["P"].get("num_users", 1)

    p_services = []
    for i in range(num_users):
        p = ServiceP(
            env,
            q_service=q_service,
            arrival_process=config["P"]["arrival_process"],
            mean_interarrival=config["P"]["mean_interarrival"],
            read_probability=config["P"]["read_probability"],
            num_requests=config["P"]["num_requests"],
        )
        p_services.append(p)

    # Запускаем симуляцию
    env.run()

    # Объединяем результаты всех P
    all_results = []
    for p in p_services:
        all_results.extend(p.results)

    successes = sum(
        1 for r in all_results if r[2] == "OK" or (r[0] == "read" and "data" in r[2])
    )
    errors = len(all_results) - successes
    times = [r[5] for r in all_results]  # duration в 6-м элементе кортежа (индекс 5)
    avg_time = statistics.mean(times) if times else 0.0

    summary = {
        "successes": successes,
        "errors": errors,
        "avg_time": avg_time,
        "times": times,
        "details": all_results,
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
