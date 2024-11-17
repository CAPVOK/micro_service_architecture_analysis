class ServiceP:
    def __init__(self, service_q, expect_404=False):
        self.service_q = service_q
        self.expect_404 = expect_404

    def request_data(self, user_id):
        response = self.service_q.get_data(user_id)
        if response == 404 and not self.expect_404:
            # P не ожидает 404 и падает
            raise Exception("Unexpected 404 error in Service P")
        else:
            return response
