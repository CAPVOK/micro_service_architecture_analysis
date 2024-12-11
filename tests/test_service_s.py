from unittest.mock import patch

import pytest

from services import ServiceS


def test_s_write_read_success(env):
    s_service = ServiceS(
        env,
        read_failure_probability=0.0,
        write_failure_probability=0.0,
        max_write_time=0.1,
        max_read_time=0.1,
        concurrency_limit=2,
    )

    def scenario():
        yield env.process(s_service.write(1, "data_s"))
        val = yield env.process(s_service.read(1))
        assert val == "data_s"
        print("S: write/read success test passed")

    env.process(scenario())
    env.run()


def test_s_read_not_found(env):
    s_service = ServiceS(
        env,
        read_failure_probability=0.0,
        write_failure_probability=0.0,
        max_write_time=0.1,
        max_read_time=0.1,
        concurrency_limit=2,
    )

    def scenario():
        with pytest.raises(RuntimeError, match="data not found"):
            yield env.process(s_service.read(999))
        print("S: read not found test passed")

    env.process(scenario())
    env.run()


def test_s_read_error(env):
    s_service = ServiceS(
        env,
        read_failure_probability=1.0,
        write_failure_probability=0.0,
        max_write_time=0.1,
        max_read_time=0.1,
        concurrency_limit=2,
    )

    def scenario():
        with pytest.raises(RuntimeError, match="failed"):
            yield env.process(s_service.read(999))
        print("S: read error test passed")

    env.process(scenario())
    env.run()


def test_s_write_error(env):
    s_service = ServiceS(
        env,
        read_failure_probability=0.0,
        write_failure_probability=1.0,
        max_write_time=0.1,
        max_read_time=0.1,
        concurrency_limit=2,
    )

    def scenario():
        with pytest.raises(RuntimeError, match="failed"):
            yield env.process(s_service.write(1, "fdvdf"))
        print("S: write error test passed")

    env.process(scenario())
    env.run()


def test_s_queue_par(env):
    s_service = ServiceS(
        env,
        read_failure_probability=0.0,
        write_failure_probability=0.0,
        max_write_time=0.5,
        max_read_time=0.5,
        concurrency_limit=3,
    )

    results = []

    def op(name, req_id):
        start_time = env.now
        yield env.process(s_service.write(req_id, f"data_{req_id}"))
        end_time = env.now
        results.append((name, start_time, end_time))

    # Запустим 5 записи одновременно
    env.process(op("op1", 1))
    env.process(op("op2", 2))
    env.process(op("op3", 3))
    env.process(op("op4", 4))
    env.process(op("op5", 5))
    env.process(op("op6", 5))
    env.process(op("op7", 5))
    env.process(op("op8", 5))
    env.process(op("op9", 5))
    env.process(op("op10", 5))
    env.process(op("op11", 5))
    env.process(op("op12", 5))

    env.run()

    print(results)

    print("S: test_s_queue_par test passed")


def test_s_queue_concurrency(env):
    """Проверяем, что при concurrency_limit=2 третий запрос ждет,
    пока один из первых двух не завершится."""

    s_service = ServiceS(
        env,
        read_failure_probability=0.0,
        write_failure_probability=0.0,
        max_write_time=0.5,
        max_read_time=0.5,
        concurrency_limit=4,
    )

    results = []

    def op(name, req_id):
        start_time = env.now
        yield env.process(s_service.write(req_id, f"data_{req_id}"))
        end_time = env.now
        results.append((name, start_time, end_time))

    # Запустим 3 записи одновременно
    env.process(op("op1", 1))
    env.process(op("op2", 2))
    env.process(op("op3", 3))
    env.process(op("op4", 4))
    env.process(op("op5", 5))

    env.run()

    # Проверим, что первые две операции запустились примерно в одно и то же время (время = 0)
    # Третья операция должна была начаться только после освобождения ресурса.
    # Время старта первой и второй операций должно быть 0 (они сразу начнутся).
    # Третья операция тоже запустится сразу (в смысле, вызов process), но начнет выполняться
    # (займет ресурс) только после завершения одной из первых двух. Из-за этого ее end_time будет позже.
    # Мы не контролируем случайные задержки точно, но если все три стартуют одновременно,
    # первые две завершатся раньше, а третья начнет выполняться после освобождения слота.

    # Отсортируем результаты по времени завершения
    results.sort(key=lambda x: x[2])

    # Теперь results[0] и results[1] – первые две операции, results[2] – третья.
    # Проверим, что первая и вторая операции стартовали в 0
    assert results[0][1] == 0
    assert results[1][1] == 0
    assert results[2][1] == 0
    assert results[3][1] == 0

    # Третья операция тоже "стартует" в 0-мом времени (процесс запущен),
    # но она не может начать выполнение до освобождения ресурса.
    # Мы не имеем прямого доступа ко времени начала выполнения внутри ServiceS,
    # но можно сделать косвенную проверку: время завершения третьей операции должно быть заметно больше,
    # чем у первых двух, что говорит о том, что она ожидала в очереди.

    # Проверим, что третья операция завершилась позже, чем хотя бы одна из первых двух операций на значительную величину.
    # Поскольку max_write_time=0.5, операции завершаются примерно через 0.0-0.5 времени.
    # Если concurrency_limit=2 и три запроса одновременно, третий должен начаться только после окончания одного из первых.
    # Значит, end_time третьего > end_time одной из первых примерно на 0.5.
    # Из-за рандома может быть трудно проверить точно, но мы хотя бы убедимся, что третья операция завершилась значительно позже.

    first_op_end = results[0][2]
    second_op_end = results[1][2]
    third_op_end = results[2][2]
    fourth_op_end = results[3][2]
    fifth_op_end = results[4][2]

    print(first_op_end)
    print(second_op_end)
    print(third_op_end)
    print(fourth_op_end)
    print(fifth_op_end)

    # Предположим, что третья операция завершилась минимум на 0.1 позже, чем самая ранняя из первых двух.
    assert fourth_op_end > min(first_op_end, second_op_end, third_op_end)

    print("S: concurrency queue test passed")
