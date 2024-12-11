import simpy
import yaml

from services import ServiceP, ServiceQ, ServiceS, ServiceT


def main():
    # Читаем конфиг
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    env = simpy.Environment()

    # Создаем сервисы
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
        request_rate=config["P"]["request_rate"],
        read_probability=config["P"]["read_probability"],
    )

    # Запускаем симуляцию
    env.run(until=config["P"]["simulation_time"])


if __name__ == "__main__":
    main()
