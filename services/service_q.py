import simpy


class ServiceQ:
    def __init__(self, env, response_timeout, service_t, service_s):
        self.env = env
        self.response_timeout = response_timeout
        self.service_t = service_t
        self.service_s = service_s

    def process_request(self, req_type, req_id, data=None):
        if req_type == "write":
            # Сначала пишем в T
            try:
                res = yield self.env.process(self.wrap_t_write(req_id, data))
                # Если успешно, пишем в S
                res = yield self.env.process(self.wrap_s_write(req_id, data))
                # Если всё ок, возвращаем успех
                return "OK"
            except RuntimeError as e:
                return f"ERROR: {str(e)}"
            except simpy.Interrupt:
                return "ERROR: timeout"

        elif req_type == "read":
            # Пробуем читать из T
            try:
                res_t = yield self.env.process(self.wrap_t_read(req_id))
                return res_t
            except RuntimeError:
                # Пробуем читать из S
                try:
                    res_s = yield self.env.process(self.wrap_s_read(req_id))
                    return res_s
                except RuntimeError as e:
                    return f"ERROR: {str(e)}"
                except simpy.Interrupt:
                    return "ERROR: timeout"
            except simpy.Interrupt:
                return "ERROR: timeout"

    def wrap_t_read(self, req_id):
        # Оборачиваем операцию T чтения с таймаутом
        timeout_event = self.env.timeout(self.response_timeout)
        read_proc = self.env.process(self._t_read(req_id))
        res = yield read_proc | timeout_event
        if timeout_event in res:
            read_proc.interrupt("T read timeout")
            raise simpy.Interrupt("timeout")
        return list(res.values())[0]

    def wrap_t_write(self, req_id, data):
        timeout_event = self.env.timeout(self.response_timeout)
        write_proc = self.env.process(self._t_write(req_id, data))
        res = yield write_proc | timeout_event
        if timeout_event in res:
            write_proc.interrupt("T write timeout")
            raise simpy.Interrupt("timeout")
        return True

    def wrap_s_read(self, req_id):
        timeout_event = self.env.timeout(self.response_timeout)
        read_proc = self.env.process(self._s_read(req_id))
        res = yield read_proc | timeout_event
        if timeout_event in res:
            read_proc.interrupt("S read timeout")
            raise simpy.Interrupt("timeout")
        return list(res.values())[0]

    def wrap_s_write(self, req_id, data):
        timeout_event = self.env.timeout(self.response_timeout)
        write_proc = self.env.process(self._s_write(req_id, data))
        res = yield write_proc | timeout_event
        if timeout_event in res:
            write_proc.interrupt("S write timeout")
            raise simpy.Interrupt("timeout")
        return True

    def _t_read(self, req_id):
        # Выполняем мгновенную операцию чтения из T
        val = self.service_t.read(req_id)
        # Добавим нулевую задержку, чтобы функция была генератором
        yield self.env.timeout(0)
        return val

    def _t_write(self, req_id, data):
        # Выполняем мгновенную операцию записи в T
        self.service_t.write(req_id, data)
        # Добавим нулевую задержку, чтобы функция была генератором
        yield self.env.timeout(0)
        return True

    def _s_read(self, req_id):
        # Вызов службы S (c yield, т.к. асинхронно в simpy)
        val = yield self.env.process(self.service_s.read(req_id))
        return val

    def _s_write(self, req_id, data):
        yield self.env.process(self.service_s.write(req_id, data))
        return True
