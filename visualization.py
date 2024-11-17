import matplotlib.pyplot as plt

from simulation import run_simulation


def main():
    # Базовая конфигурация
    base_config = {
        "simulation": {"num_requests": 1000},
        "services": {
            "service_t": {"is_down": False, "failure_rate": 0.0, "response_time": 0.0},
            "service_s": {
                "is_overloaded": False,
                "failure_rate": 0.0,
                "response_time": 0.0,
            },
            "service_p": {"expect_404": False},
        },
    }

    scenarios = [
        {"name": "Все службы работают", "config_updates": {}},
        {
            "name": "T недоступна",
            "config_updates": {"services": {"service_t": {"is_down": True}}},
        },
        {
            "name": "T недоступна, S перегружена",
            "config_updates": {
                "services": {
                    "service_t": {"is_down": True},
                    "service_s": {"is_overloaded": True},
                }
            },
        },
        {
            "name": "Высокая вероятность отказа S и T",
            "config_updates": {
                "services": {
                    "service_s": {"failure_rate": 0.7},
                    "service_t": {"failure_rate": 0.7},
                }
            },
        },
        {
            "name": "S перегружена",
            "config_updates": {"services": {"service_s": {"is_overloaded": True}}},
        },
        {
            "name": "T работает с высокой вероятностью отказа",
            "config_updates": {"services": {"service_t": {"failure_rate": 0.9}}},
        },
    ]

    results = []
    for scenario in scenarios:
        config = base_config.copy()

        for key, value in scenario["config_updates"].items():
            for sub_key, sub_value in value.items():
                config[key][sub_key] = sub_value

        success, fail = run_simulation(config)
        results.append({"name": scenario["name"], "success": success, "fail": fail})

    # Построение графика
    labels = [res["name"] for res in results]
    success_counts = [res["success"] for res in results]
    fail_counts = [res["fail"] for res in results]

    x = range(len(labels))
    plt.bar(x, success_counts, label="Успешные запросы")
    plt.bar(x, fail_counts, bottom=success_counts, label="Сбои")
    plt.xticks(x, labels, rotation=45)
    plt.ylabel("Количество запросов")
    plt.legend()
    plt.tight_layout()
    plt.title("Результаты симуляции")
    plt.show()


if __name__ == "__main__":
    main()
