import unittest

from app import app


class AppTestCase(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

    def test_home_page(self):
        response = self.client.get("/")
        self.assertIn(response.status_code, [200, 302])

    def test_login_page(self):
        response = self.client.get("/login")
        self.assertIn(response.status_code, [200, 302])


if __name__ == "__main__":
    unittest.main()
