from unittest.mock import patch

import pytest

from services import ServiceQ, ServiceS, ServiceT


def test_q_write_success(env):
    """Проверяем успешную запись: T и S не отказывают, Q должен вернуть OK."""
    t_service = ServiceT(env, 0.0, 0.0)
    s_service = ServiceS(
        env, 0.0, 0.0, max_write_time=0.1, max_read_time=0.1, concurrency_limit=2
    )
    q = ServiceQ(env, response_timeout=1.0, service_t=t_service, service_s=s_service)

    def scenario():
        res = yield env.process(q.process_request("write", 1, "q_data"))
        assert res == "OK"
        # Проверим, что данные действительно дошли до T и S
        assert t_service.storage.get(1) == "q_data"
        assert s_service.storage.get(1) == "q_data"
        print("Q: write success test passed")

    env.process(scenario())
    env.run()


def test_q_read_success_from_t(env):
    """Читаем данные, которые есть в T. T не отказывает, Q возвращает данные."""
    t_service = ServiceT(env, 0.0, 0.0)
    s_service = ServiceS(env, 0.0, 0.0, 0.1, 0.1, 2)
    q = ServiceQ(env, 1.0, t_service, s_service)

    # Запишем данные заранее в T
    t_service.write(10, "t_data")

    def scenario():
        res = yield env.process(q.process_request("read", 10))
        assert res == "t_data"
        print("Q: read success from T test passed")

    env.process(scenario())
    env.run()


def test_q_read_fallback_s(env):
    """Читаем данные, которых нет в T, но есть в S, Q должен вернуть данные из S."""
    t_service = ServiceT(env, 0.0, 0.0)
    s_service = ServiceS(env, 0.0, 0.0, 0.1, 0.1, 2)
    q = ServiceQ(env, 1.0, t_service, s_service)

    # Запишем данные только в S
    def setup_s():
        yield env.process(s_service.write(20, "s_data"))

    env.process(setup_s())
    env.run()

    # Теперь читаем через Q
    def scenario():
        res = yield env.process(q.process_request("read", 20))
        assert res == "s_data"
        print("Q: read fallback to S test passed")

    env.process(scenario())
    env.run()


def test_q_write_t_failure(env):
    """При записи T отказывает, значит Q сразу вернёт ошибку, не дойдя до S."""
    t_service = ServiceT(env, 0.0, 1.0)  # 100% отказ при записи
    s_service = ServiceS(env, 0.0, 0.0, 0.1, 0.1, 2)
    q = ServiceQ(env, 1.0, t_service, s_service)

    def scenario():
        res = yield env.process(q.process_request("write", 30, "fail_data"))
        assert "ERROR" in res
        # Убедимся, что в S данные не появились
        assert 30 not in s_service.storage
        print("Q: write t failure test passed")

    env.process(scenario())
    env.run()


def test_q_write_s_failure(env):
    """При записи T успешна, но S отказывает, Q вернёт ошибку."""
    t_service = ServiceT(env, 0.0, 0.0)
    s_service = ServiceS(env, 0.0, 1.0, 0.1, 0.1, 2)  # 100% отказ при записи
    q = ServiceQ(env, 1.0, t_service, s_service)

    def scenario():
        res = yield env.process(q.process_request("write", 40, "fail_s_data"))
        assert "ERROR" in res
        # Данные должны быть в T, но Q всё равно возвращает ошибку, так как S упал.
        assert t_service.storage.get(40) == "fail_s_data"
        print("Q: write s failure test passed")

    env.process(scenario())
    env.run()


def test_q_read_not_found(env):
    """Данных нет ни в T, ни в S, Q вернёт ошибку."""
    t_service = ServiceT(env, 0.0, 0.0)
    s_service = ServiceS(env, 0.0, 0.0, 0.1, 0.1, 2)
    q = ServiceQ(env, 1.0, t_service, s_service)

    def scenario():
        res = yield env.process(q.process_request("read", 999))
        assert "ERROR" in res
        print("Q: read not found test passed")

    env.process(scenario())
    env.run()


def test_q_timeout(env):
    """Сделаем так, чтобы S очень долго отвечал, а Q имел маленький timeout."""
    t_service = ServiceT(env, 0.0, 0.0)
    # Большое время записи в S, чтобы превысить timeout Q
    s_service = ServiceS(
        env, 0.0, 0.0, max_write_time=2.0, max_read_time=0.1, concurrency_limit=1
    )
    q = ServiceQ(env, response_timeout=0.5, service_t=t_service, service_s=s_service)

    def scenario():
        res = yield env.process(q.process_request("write", 50, "timeout_data"))
        assert "ERROR: timeout" in res
        # Возможно, T уже успел записаться (проверяем), но Q вернул ошибку из-за таймаута на S.
        print("Q: timeout test passed")

    env.process(scenario())
    env.run()
