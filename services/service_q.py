import simpy


class ServiceQ:
    def __init__(self, env, response_timeout, service_t, service_s):
        self.env = env
        self.response_timeout = response_timeout
        self.service_t = service_t
        self.service_s = service_s

    def process_request(self, req_type, req_id, data=None):
        try:
            if req_type == "write":
                # Сначала пишем в T
                yield self.env.process(self.wrap_t_write(req_id, data))
                # Если успешно, пишем в S
                yield self.env.process(self.wrap_s_write(req_id, data))
                return "OK"
            elif req_type == "read":
                # Пробуем читать из T
                try:
                    res_t = yield self.env.process(self.wrap_t_read(req_id))
                    return res_t
                except RuntimeError:
                    # Пробуем читать из S
                    res_s = yield self.env.process(self.wrap_s_read(req_id))
                    return res_s
        except RuntimeError as e:
            return f"ERROR: {str(e)}"

    def wrap_t_read(self, req_id):
        # Чтение из T с таймаутом
        timeout_event = self.env.timeout(self.response_timeout)
        read_proc = self.env.process(self._safe_t_read(req_id))
        res = yield read_proc | timeout_event
        if timeout_event in res:
            raise RuntimeError("T read timeout")
        return list(res.values())[0]

    def wrap_t_write(self, req_id, data):
        # Запись в T с таймаутом
        timeout_event = self.env.timeout(self.response_timeout)
        write_proc = self.env.process(self._safe_t_write(req_id, data))
        res = yield write_proc | timeout_event
        if timeout_event in res:
            raise RuntimeError("T write timeout")
        return True

    def wrap_s_read(self, req_id):
        # Чтение из S с таймаутом
        timeout_event = self.env.timeout(self.response_timeout)
        read_proc = self.env.process(self._safe_s_read(req_id))
        res = yield read_proc | timeout_event
        if timeout_event in res:
            raise RuntimeError("S read timeout")
        return list(res.values())[0]

    def wrap_s_write(self, req_id, data):
        # Запись в S с таймаутом
        timeout_event = self.env.timeout(self.response_timeout)
        write_proc = self.env.process(self._safe_s_write(req_id, data))
        res = yield write_proc | timeout_event
        if timeout_event in res:
            raise RuntimeError("write timeout")
        return True

    def _safe_t_read(self, req_id):
        # Безопасное чтение T: перехватываем RuntimeError и поднимаем с понятным сообщением
        try:
            val = self.service_t.read(req_id)
            yield self.env.timeout(0)
            return val
        except RuntimeError as e:
            # Перехватываем и меняем сообщение, если нужно
            raise RuntimeError(f"T failed: {str(e)}") from e

    def _safe_t_write(self, req_id, data):
        try:
            self.service_t.write(req_id, data)
            yield self.env.timeout(0)
            return True
        except RuntimeError as e:
            raise RuntimeError(f"T failed: {str(e)}") from e

    def _safe_s_read(self, req_id):
        try:
            val = yield self.env.process(self.service_s.read(req_id))
            return val
        except RuntimeError as e:
            raise RuntimeError(f"S failed: {str(e)}") from e

    def _safe_s_write(self, req_id, data):
        try:
            yield self.env.process(self.service_s.write(req_id, data))
            return True
        except RuntimeError as e:
            raise RuntimeError(f"S failed: {str(e)}") from e
