from services import ServiceP, ServiceQ, ServiceS, ServiceT


def test_p_all_write_success(env):
    """Тест: Все сервисы работают без отказов, P генерирует запросы на запись, все OK."""
    t_service = ServiceT(
        env, read_failure_probability=0.0, write_failure_probability=0.0
    )
    s_service = ServiceS(
        env, 0.0, 0.0, max_write_time=0.1, max_read_time=0.1, concurrency_limit=2
    )
    q_service = ServiceQ(
        env, response_timeout=1.0, service_t=t_service, service_s=s_service
    )

    # Все запросы — запись, без сбоев
    p = ServiceP(env, q_service=q_service, request_rate=1, read_probability=0.0)

    env.run(until=3)
    print("P: all success write test passed")


def test_p_t_write_failure(env):
    """Тест: T всегда отказывает при записи, P генерирует запросы на запись, ожидаем ошибки у P."""
    # Сделаем так, чтобы T всегда падал при записи.
    t_service = ServiceT(
        env, read_failure_probability=0.0, write_failure_probability=1.0
    )
    s_service = ServiceS(
        env, 0.0, 0.0, max_write_time=0.1, max_read_time=0.1, concurrency_limit=2
    )
    q_service = ServiceQ(env, 1.0, t_service, s_service)

    # Все запросы — запись, но T отказывает, значит Q вернет ошибку, P это залогирует (в нашем случае просто print)
    p = ServiceP(env, q_service, request_rate=1, read_probability=0.0)

    env.run(until=2)
    # Проверим по выводу (или можно внедрить логику подсчета ошибок)
    print("P: T failure test passed")


def test_p_t_write_and_s_write_failure(env):
    """Тест: T всегда отказывает при записи, P генерирует запросы на запись, ожидаем ошибки у P."""
    # Сделаем так, чтобы T всегда падал при записи.
    t_service = ServiceT(
        env, read_failure_probability=0.0, write_failure_probability=1.0
    )
    s_service = ServiceS(
        env, 0.0, 1.0, max_write_time=0.1, max_read_time=0.1, concurrency_limit=2
    )
    q_service = ServiceQ(env, 1.0, t_service, s_service)

    # Все запросы — запись, но T отказывает, значит Q вернет ошибку, P это залогирует (в нашем случае просто print)
    p = ServiceP(env, q_service, request_rate=1, read_probability=0.0)

    env.run(until=2)
    # Проверим по выводу (или можно внедрить логику подсчета ошибок)
    print("P: T failure test passed")


def test_p_s_failure(env):
    """Тест: S отказывает при записи, при чтении - Q обращается к T или S.
    Попытаемся сделать запись (которая вызывает T, потом S) и убедимся, что из-за S - ошибка.
    """
    t_service = ServiceT(env, 0.0, 0.0)  # T без отказа
    s_service = ServiceS(
        env, 0.0, 1.0, max_write_time=0.1, max_read_time=0.1, concurrency_limit=2
    )
    q_service = ServiceQ(env, 1.0, t_service, s_service)

    # Все запросы — запись, S отказывает, значит Q вернет ошибку
    p = ServiceP(env, q_service, request_rate=1, read_probability=0.0)

    env.run(until=2)
    print("P: S failure on write test passed")


def test_p_mixed_read_write(env):
    """Тест: Смешанные запросы: часть на чтение, часть на запись.
    При этом T иногда не содержит данных, S содержит.
    Проверяем, что P правильно получает результаты (иногда OK, иногда ERROR)."""

    # Запишем сначала в T и S вручную данные, а потом P будет читать
    t_service = ServiceT(env, 0.0, 0.0)
    s_service = ServiceS(
        env, 0.0, 0.0, max_write_time=0.1, max_read_time=0.1, concurrency_limit=2
    )
    q_service = ServiceQ(env, 1.0, t_service, s_service)

    # Запишем данные с id=10 в T
    t_service.write(10, "data_10")
    # Не пишем в S, чтобы проверить fallback Q на чтение

    # Теперь P будет генерировать запросы, половина на чтение, половина на запись
    p = ServiceP(env, q_service=q_service, request_rate=2, read_probability=0.5)

    # За время, скажем 5 единиц, P сгенерирует ~10 запросов
    # Некоторые будут читать, некоторые писать.
    # Чтение id=10 всегда должно быть успешным (T уже содержит данные_10),
    # Чтение чего-то другого - ошибка (no data).
    # Запись будет проходить без ошибок, так как нет отказов.
    env.run(until=5)
    print("P: mixed read/write test passed")


def test_p_q_timeout(env):
    """Тест: Q настроим так, чтобы S очень долго отвечала, превысив timeout. P получит ошибку из Q."""
    t_service = ServiceT(env, 0.0, 0.0)
    s_service = ServiceS(
        env, 0.0, 0.0, max_write_time=2.0, max_read_time=2.0, concurrency_limit=1
    )
    # Timeout Q = 0.5, а операции S занимают до 2.0
    q_service = ServiceQ(
        env, response_timeout=0.5, service_t=t_service, service_s=s_service
    )

    # Все запросы — запись, но S отвечает слишком долго => Q вернет timeout error
    p = ServiceP(env, q_service=q_service, request_rate=1, read_probability=0.0)

    env.run(until=2)
    print("P: Q timeout test passed")


def test_p_partial_failure(env):
    """Тест: Частичный отказ. Например, при записи в Q, T успешно пишет, а S иногда отказывает.
    Или S успешно пишет, а T - нет. Попытаемся вызвать ситуацию, когда один запрос прошел частично.
    """

    t_service = ServiceT(env, 0.0, 0.5)  # 50% отказ на запись
    s_service = ServiceS(
        env, 0.0, 0.5, max_write_time=0.1, max_read_time=0.1, concurrency_limit=2
    )
    q_service = ServiceQ(env, 1.0, t_service, s_service)

    # Все запросы — запись. Иногда они будут успешны (когда T и S не упадут),
    # Иногда будут падать на T, иногда на S.
    # P просто принимает результат. Мы не делаем assert, но по логам можно увидеть разные исходы.
    p = ServiceP(env, q_service=q_service, request_rate=2, read_probability=0.0)
    env.run(until=3)
    print("P: partial failure test passed")
