class ServiceQ:
    def __init__(self, service_t, service_s):
        self.service_t = service_t
        self.service_s = service_s

    def get_data(self, user_id):
        try:
            # Попытка получить данные из кеша T
            return self.service_t.get_data(user_id)
        except:
            try:
                # Если T недоступен, обращаемся к S
                return self.service_s.get_data(user_id)
            except:
                # Если S тоже недоступен, возвращаем 404
                return 404
