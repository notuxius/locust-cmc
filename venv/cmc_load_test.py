from locust import HttpLocust, TaskSet, task, runners
from locust.clients import HttpSession
from locust.log import console_logger
from requests import ReadTimeout, ConnectTimeout
from json.decoder import JSONDecodeError


class CMCUserSession(HttpSession):

    def login(self):
        try:

            # Login with API key, accept JSON in response
            global _resp
            _resp = self.client.request(method="GET",
                                        url="/v1/cryptocurrency/listings/latest?start=1&limit=10&sort=volume_24h",
                                        headers={"Accepts": "application/json",
                                                 "X-CMC_PRO_API_KEY": "942855f9-6ddf-4e60-a659-e6d072eddf5d"},
                                        timeout=0.5)

            if _resp:
                if _resp.status_code != 200:
                    console_logger.error("ERROR: Bad response")
                    console_logger.error(_resp.status_code)
                    runners.locust_runner.quit()

                if len(_resp.content) > 10000:
                    console_logger.error("ERROR: Response object is bigger than 10KB")
                    console_logger.error(len(_resp.content))
                    runners.locust_runner.quit()

                # elif len(resp.content) < 500:
                #     print("Response object is less than 500B")

        except ConnectTimeout:
            console_logger.error("ERROR: Response connection time is more than 500ms")
            runners.locust_runner.quit()

        except ReadTimeout:
            console_logger.error("ERROR: Response read time is more than 500ms")
            runners.locust_runner.quit()


class CMCUserTasks(TaskSet):

    @task
    def on_start(self):
        CMCUserSession.login(self)

    global _resp_number
    _resp_number = 0

    @task
    def list_top_10_currencies_by_volume_24h(self):
        try:
            resp_json = _resp.json()
            # console_logger.info(resp_json)

            global _resp_number

            # Receive 8 responses
            if _resp_number < 8:
                _resp_number += 1
                console_logger.info("Response #{}".format(_resp_number))
                console_logger.info("Top 10 currencies in past 24 hours by volume:")

            # Display top 10 currencies
                for number_of_currency in range(10):
                    console_logger.info(resp_json['data'][number_of_currency]['name'])
                    # console_logger.info(round(resp_json['data'][number_of_currency]['quote']['USD']['volume_24h'], 1))

            else:
                runners.locust_runner.quit()

        except JSONDecodeError:
            console_logger.error("ERROR: Failed to decode response into JSON")

    @task
    def test_rps_time(self):
        if 0 < runners.locust_runner.stats.total.current_rps < 5:
            console_logger.error("ERROR: RPS is less than 5")
            console_logger.error(round(runners.locust_runner.stats.total.current_rps, 1))
            runners.locust_runner.quit()

        if isinstance(runners.locust_runner.stats.total.get_current_response_time_percentile(0.8), int):
            resp_time_80_perc = runners.locust_runner.stats.total.get_current_response_time_percentile(0.8)

            if resp_time_80_perc > 450:
                console_logger.error("ERROR: 80 percents of response time is more than 450ms")
                console_logger.error(resp_time_80_perc)
                runners.locust_runner.quit()


class CMCHttpUser(HttpLocust):
    task_set = CMCUserTasks
    host = "https://pro-api.coinmarketcap.com"
    min_wait = 3000
    max_wait = 3000
    stop_timeout = 60
