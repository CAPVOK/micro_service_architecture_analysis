import copy

import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import yaml

from main import run_simulation

st.title("Микросервисная симуляция")

# Загружаем базовый конфиг
with open("config.yaml", "r") as f:
    base_config = yaml.safe_load(f)

# Создадим вкладки для настроек
tab_config, tab_scenarios = st.tabs(["Конфигурация", "Сценарии"])

with tab_config:
    st.header("Настройка параметров")

    # Добавим пояснения к параметрам с помощью `help`
    st.subheader("Параметры P (генерация запросов)")
    arrival_process = st.selectbox(
        "Тип процесса поступления запросов: 'poisson' - случайные интервалы, 'fixed_interval' - равные интервалы.",
        ["poisson", "fixed_interval"],
        index=0,
    )
    mean_interarrival = st.slider(
        "Средний интервал между запросами. При 'fixed_interval' это постоянный интервал, при 'poisson' - среднее для экспоненциального распределения.",
        0.05,
        1.0,
        0.2,
        0.05,
    )
    read_probability = st.slider(
        "Вероятность, что сгенерированный запрос будет чтением (read), иначе будет запись (write).",
        0.0,
        1.0,
        0.5,
        0.1,
    )
    num_requests = st.number_input(
        "Общее количество запросов, которые P сгенерирует.",
        min_value=10,
        max_value=1000000,
        value=50,
        step=10,
    )

    # Параметры Q
    st.subheader("Параметры Q (промежуточный сервис)")
    response_timeout = st.number_input(
        "Максимальное время ожидания ответа от сервисов T и S в Q. Если превышено - таймаут и ошибка.",
        min_value=0.1,
        max_value=10.0,
        value=1.0,
        step=0.1,
    )

    # Параметры T
    st.subheader("Параметры T (кеш)")
    t_read_failure = st.slider(
        "Вероятность отказа T при операции чтения.",
        0.0,
        1.0,
        0.0,
        0.05,
    )
    t_write_failure = st.slider(
        "Вероятность отказа T при операции записи.",
        0.0,
        1.0,
        0.0,
        0.05,
    )

    # Параметры S
    st.subheader("Параметры S (постоянное хранилище)")
    s_read_failure = st.slider(
        "Вероятность отказа S при чтении.",
        0.0,
        1.0,
        0.0,
        0.05,
    )
    s_write_failure = st.slider(
        "Вероятность отказа S при записи.",
        0.0,
        1.0,
        0.0,
        0.05,
    )
    s_max_write_time = st.slider(
        "Максимальное время выполнения операции записи в S.",
        0.0,
        5.0,
        0.1,
        0.1,
    )
    s_max_read_time = st.slider(
        "Максимальное время выполнения операции чтения из S.",
        0.0,
        5.0,
        0.1,
        0.1,
    )
    s_concurrency = st.number_input(
        "Максимальное количество параллельных операций в S.",
        min_value=1,
        max_value=100000,
        value=2,
        step=1,
    )

    if st.button("Запустить симуляцию с текущими параметрами"):
        config = copy.deepcopy(base_config)
        config["P"]["arrival_process"] = arrival_process
        config["P"]["mean_interarrival"] = mean_interarrival
        config["P"]["read_probability"] = read_probability
        config["P"]["num_requests"] = num_requests

        config["Q"]["response_timeout"] = response_timeout

        config["T"]["read_failure_probability"] = t_read_failure
        config["T"]["write_failure_probability"] = t_write_failure

        config["S"]["read_failure_probability"] = s_read_failure
        config["S"]["write_failure_probability"] = s_write_failure
        config["S"]["max_write_time"] = s_max_write_time
        config["S"]["max_read_time"] = s_max_read_time
        config["S"]["concurrency_limit"] = s_concurrency

        summary = run_simulation(config)

        st.write("**Результаты симуляции:**")
        st.write(f"- Успешных запросов: {summary['successes']}")
        st.write(f"- Ошибок: {summary['errors']}")
        st.write(f"- Среднее время ответа: {summary['avg_time']:.4f}")

        # Новые графики, предполагая, что summary["details"] = [(req_type, req_id, result, start_time, end_time, duration), ...]
        details = summary.get("details", [])
        if details:
            # Пример: Кол-во ошибок по времени
            # Для этого сгруппируем запросы по интервалам времени и посчитаем кумулятивно ошибки
            # Предположим, у нас есть start_time. Если нет, нужно добавить в run_simulation.
            errors_over_time = []
            successes_over_time = []
            sorted_details = sorted(
                details, key=lambda x: x[3]
            )  # сортируем по start_time (x[3])

            cumulative_errors = 0
            cumulative_success = 0
            time_points = []

            for d in sorted_details:
                req_type, req_id, result, start_time, end_time, duration = d
                if "ERROR" in result:
                    cumulative_errors += 1
                else:
                    # Успешный запрос: либо "OK" (для записи) либо "data..." (для чтения)
                    cumulative_success += 1
                time_points.append(end_time)
                errors_over_time.append(cumulative_errors)
                successes_over_time.append(cumulative_success)

            # График ошибок по времени
            fig5, ax5 = plt.subplots(figsize=(6, 4))
            ax5.plot(time_points, errors_over_time, color="red", marker="o")
            ax5.set_title("Накопленное число ошибок по времени")
            ax5.set_xlabel("Время (симуляционное)")
            ax5.set_ylabel("Число ошибок (накопленное)")
            st.pyplot(fig5)

            # Еще один график: Распределение типов запросов
            # Посчитаем, сколько было read и write
            read_count = sum(1 for d in details if d[0] == "read")
            write_count = sum(1 for d in details if d[0] == "write")

            fig6, ax6 = plt.subplots(figsize=(4, 4))
            ax6.pie(
                [read_count, write_count], labels=["read", "write"], autopct="%1.1f%%"
            )
            ax6.set_title("Соотношение операций read и write")
            st.pyplot(fig6)

            # Еще один график: Распределение успехов и ошибок по типам запросов (столбчатая диаграмма)
            read_success = sum(
                1 for d in details if d[0] == "read" and not d[2].startswith("ERROR")
            )
            read_error = sum(
                1 for d in details if d[0] == "read" and d[2].startswith("ERROR")
            )
            write_success = sum(
                1 for d in details if d[0] == "write" and not d[2].startswith("ERROR")
            )
            write_error = sum(
                1 for d in details if d[0] == "write" and d[2].startswith("ERROR")
            )

            fig7, ax7 = plt.subplots(figsize=(6, 4))
            ops = ["read", "write"]
            success_values = [read_success, write_success]
            error_values = [read_error, write_error]

            ax7.bar(ops, success_values, color="green", label="Success")
            ax7.bar(
                ops, error_values, bottom=success_values, color="red", label="Error"
            )
            ax7.set_title("Распределение успехов и ошибок по типам запросов")
            ax7.set_ylabel("Количество запросов")
            ax7.legend()
            st.pyplot(fig7)

        # Сохраним конфиг и результаты в сессию для сценариев
        if "scenarios" not in st.session_state:
            st.session_state["scenarios"] = []
        scenario_data = {
            "config": {
                "mean_interarrival": mean_interarrival,
                "read_probability": read_probability,
                "response_timeout": response_timeout,
                "t_read_failure": t_read_failure,
                "t_write_failure": t_write_failure,
                "s_read_failure": s_read_failure,
                "s_write_failure": s_write_failure,
            },
            "summary": summary,
        }
        if st.button("Сохранить этот результат как сценарий"):
            st.session_state["scenarios"].append(scenario_data)
            st.success("Сценарий добавлен!")

with tab_scenarios:
    st.header("Сравнение сценариев")
    if "scenarios" not in st.session_state or not st.session_state["scenarios"]:
        st.write("Нет сохраненных сценариев. Запустите симуляцию и сохраните сценарий.")
    else:
        # Выведем таблицу с результатами сценариев
        scenarios_list = st.session_state["scenarios"]
        st.write("Сохраненные сценарии:")
        for i, sc in enumerate(scenarios_list):
            st.write(
                f"Сценарий {i+1}: mean_interarrival={sc['config']['mean_interarrival']}, "
                f"read_prob={sc['config']['read_probability']}, timeout={sc['config']['response_timeout']}"
            )
            st.write(
                f"  successes={sc['summary']['successes']}, errors={sc['summary']['errors']}, avg_time={sc['summary']['avg_time']:.4f}"
            )

        # График зависимости ошибок от mean_interarrival
        x = [sc["config"]["mean_interarrival"] for sc in scenarios_list]
        errors = [sc["summary"]["errors"] for sc in scenarios_list]
        avg_times = [sc["summary"]["avg_time"] for sc in scenarios_list]

        fig3, ax3 = plt.subplots(figsize=(6, 4))
        ax3.plot(x, errors, marker="o", color="red")
        ax3.set_title("Зависимость числа ошибок от mean_interarrival")
        ax3.set_xlabel("mean_interarrival")
        ax3.set_ylabel("Ошибки")
        st.pyplot(fig3)

        # График зависимости среднего времени ответа от mean_interarrival
        fig4, ax4 = plt.subplots(figsize=(6, 4))
        ax4.plot(x, avg_times, marker="o", color="purple")
        ax4.set_title("Зависимость среднего времени ответа от mean_interarrival")
        ax4.set_xlabel("mean_interarrival")
        ax4.set_ylabel("Среднее время ответа")
        st.pyplot(fig4)
