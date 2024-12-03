#import pytest
#from unittest.mock import patch, Mock
#from fastapi.testclient import TestClient
#
## Assume your FastAPI app is defined in src.app
#from src.app import app
#
#client = TestClient(app)
#
#def mock_post(url, files=None, data=None):
#    class MockResponse:
#        def __init__(self):
#            self.status_code = 200
#
#    return MockResponse()
#
#def mock_get(url):
#    class MockResponse:
#        def __init__(self):
#            self.status_code = 200
#
#        def json(self):
#            return {"health": "ok"}
#
#    return MockResponse()

# Mock the service account credentials
# @patch('google.oauth2.service_account.Credentials.from_service_account_file', return_value=Mock())
# @patch('fastapi.testclient.TestClient.post', side_effect=mock_post)
# def test_file_upload(mock_post, mock_credentials):
#     payload = {'chatId': '1234'}
#     files = [
#         ('files', ('Voluntary Consent.pdf', open('/Users/sajeed/Downloads/Voluntary Consent.pdf', 'rb'), 'application/pdf'))
#     ]
#     response = client.post("/upload", files=files, data=payload)
#     assert response.status_code == 200

#@patch('fastapi.testclient.TestClient.get', side_effect=mock_get)
#@patch('google.oauth2.service_account.Credentials.from_service_account_file', return_value=Mock())
#def test_read_item(mock_get, mock_credentials):
#    response = client.get("/health")
#    assert response.status_code == 200
#    assert response.json() == {
#        "health": "ok",
#    }

def func(x):
    return x + 1

def test_answer():
    assert func(4) == 5