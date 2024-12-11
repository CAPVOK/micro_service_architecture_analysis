from services import ServiceP, ServiceQ, ServiceS, ServiceT


def test_p_all_write_success(env):
    """Все сервисы без отказов, P генерирует только записи. Ожидаем все 'OK'."""
    t_service = ServiceT(env, 0.0, 0.0)
    s_service = ServiceS(
        env, 0.0, 0.0, max_write_time=0.1, max_read_time=0.1, concurrency_limit=2
    )
    q_service = ServiceQ(
        env, response_timeout=1.0, service_t=t_service, service_s=s_service
    )

    # Все записи: read_probability=0.0
    p = ServiceP(
        env,
        q_service=q_service,
        arrival_process="fixed_interval",
        mean_interarrival=0.1,
        read_probability=0.0,
        num_requests=10,
    )
    env.run()

    assert len(p.results) == 10, "Должно быть 10 запросов."
    for req_type, req_id, result in p.results:
        assert req_type == "write"
        assert result == "OK", f"Ожидался успех, получено: {result}"


def test_p_mixed_read_write(env):
    """Смешанные запросы: часть чтений, часть записей. Нет отказов.
    Ожидаем, что записи будут успешны, и чтения успешны после того, как появились данные.
    """
    t_service = ServiceT(env, 0.0, 0.0)
    s_service = ServiceS(
        env, 0.0, 0.0, max_write_time=0.1, max_read_time=0.1, concurrency_limit=2
    )
    q_service = ServiceQ(
        env, response_timeout=100.0, service_t=t_service, service_s=s_service
    )

    # Смешанный поток: половина чтений, половина записей
    p = ServiceP(
        env,
        q_service=q_service,
        arrival_process="fixed_interval",
        mean_interarrival=0.05,
        read_probability=0.5,
        num_requests=20,
    )
    env.run()

    # Проверим: должны быть и write, и read
    writes = [r for r in p.results if r[0] == "write"]
    reads = [r for r in p.results if r[0] == "read"]
    assert len(writes) > 0, "Должны быть записи"
    # Без записей не будет чтений. Если есть чтения, они должны быть после первых успешных записей.
    # Так как P гарантирует, что не будет читать несуществующие данные, все read должны быть OK.
    for req_type, req_id, result in p.results:
        if req_type == "write":
            # Запись при успехе возвращает "OK"
            assert result == "OK", f"Запись должна быть успешной, получено: {result}"
        else:
            # Чтение при успехе возвращает данные, а не "OK"
            # Проверим, что результат не содержит "ERROR" и это строка данных.
            assert not result.startswith(
                "ERROR"
            ), f"Чтение не должно быть с ошибкой, получено: {result}"
            # Можно добавить дополнительную проверку, что это действительно 'data_<id>' или похожий формат
            # Для простоты проверим, что в результате есть слово "data"
            assert "data" in result, f"Ожидались данные, а не {result}"


def test_p_t_write_failure(env):
    """T отказывает при записи (100%), ожидаем ошибки при каждом запросе записи."""
    t_service = ServiceT(
        env, read_failure_probability=0.0, write_failure_probability=1.0
    )
    s_service = ServiceS(env, 0.0, 0.0, 0.1, 0.1, 2)
    q_service = ServiceQ(env, 1.0, t_service, s_service)

    p = ServiceP(
        env,
        q_service=q_service,
        arrival_process="fixed_interval",
        mean_interarrival=0.1,
        read_probability=0.0,
        num_requests=5,
    )
    env.run()

    # Все 5 запросов - записи, все должны упасть
    for req_type, req_id, result in p.results:
        assert req_type == "write"
        assert "ERROR" in result, "Ожидалась ошибка при записи, но получен успех?"


def test_p_s_write_failure(env):
    """S отказывает при записи (100%), ожидаем ошибку при каждой записи."""
    t_service = ServiceT(env, 0.0, 0.0)
    s_service = ServiceS(
        env,
        read_failure_probability=0.0,
        write_failure_probability=1.0,
        max_write_time=0.1,
        max_read_time=0.1,
        concurrency_limit=2,
    )
    q_service = ServiceQ(env, 1.0, t_service, s_service)

    p = ServiceP(
        env,
        q_service,
        arrival_process="fixed_interval",
        mean_interarrival=0.1,
        read_probability=0.0,
        num_requests=5,
    )
    env.run()

    for req_type, req_id, result in p.results:
        assert req_type == "write"
        assert "ERROR" in result, "Ожидалась ошибка из-за отказа S при записи"


def test_p_q_timeout(env):
    """Q таймаут: S очень медленно отвечает, Q выдает timeout, P получает ошибку."""
    t_service = ServiceT(env, 0.0, 0.0)
    # Очень долгий ответ S
    s_service = ServiceS(
        env, 0.0, 0.0, max_write_time=2.0, max_read_time=2.0, concurrency_limit=1
    )
    q_service = ServiceQ(
        env, response_timeout=0.1, service_t=t_service, service_s=s_service
    )

    p = ServiceP(
        env,
        q_service=q_service,
        arrival_process="fixed_interval",
        mean_interarrival=0.1,
        read_probability=0.0,
        num_requests=3,
    )
    env.run()

    # Все записи должны закончиться таймаутом
    for req_type, req_id, result in p.results:
        assert req_type == "write"
        assert "timeout" in result.lower(), f"Ожидался timeout, получено: {result}"


def test_p_partial_failure(env):
    """Частичный отказ: T или S иногда падают.
    Проверим, что часть запросов OK, часть ERROR."""
    t_service = ServiceT(env, 0.0, 0.5)  # 50% отказ на запись
    s_service = ServiceS(
        env, 0.0, 0.5, max_write_time=0.1, max_read_time=0.1, concurrency_limit=2
    )
    q_service = ServiceQ(env, 1.0, t_service, s_service)

    p = ServiceP(
        env,
        q_service=q_service,
        arrival_process="fixed_interval",
        mean_interarrival=0.05,
        read_probability=0.0,
        num_requests=10,
    )
    env.run()

    results = [res for _, _, res in p.results]
    assert len(results) == 10
    # При 50% отказах ожидаем хотя бы одну ошибку и один успех.
    # Это статистически не гарантировано при малом числе запросов, но очень вероятно.
    # Для теста можно зафиксировать `random.random()` или увеличить num_requests.
    assert any(r == "OK" for r in results), "Ожидаем хотя бы один успешный запрос"
    assert any("ERROR" in r for r in results), "Ожидаем хотя бы одну ошибку"

    print("P: partial failure test passed")
