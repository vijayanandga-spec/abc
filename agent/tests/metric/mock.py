
class MockResponse:

    def __init__(self, code):
        self.status_code = code


def mock_function(factor):
    def wrapper(self):
        return factor

    return wrapper