import requests

class Requester:
    """Simple HTTP requester wrapper around requests.

    Methods:
    - send(method, url, headers=None, data=None, params=None, timeout=30)
      returns requests.Response
    """

    def __init__(self):
        self.session = requests.Session()

    def send(self, method: str, url: str, headers: dict | None = None, data: str | None = None, params: dict | None = None, timeout: int = 30):
        method = method.upper()
        try:
            resp = self.session.request(method=method, url=url, headers=headers, data=data, params=params, timeout=timeout)
            return resp
        except requests.RequestException as e:
            # Re-raise for callers to handle; include message for UI display
            raise
