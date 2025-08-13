# test_login.py
from rest_framework.test import APIClient

client = APIClient()
url = "https://hotel-porter-d25ad83b12cf.herokuapp.com/api/staff/login/"
data = {
    "username": "nikola",
    "password": "sanja1234",
    "fcm_token": "cxYWCazU2dsvgm1vQ5AU9S:APA91bGVSpHbjmLsWd6kIti0KpwWyZB4fFCKnhN1jPnYUeUpSTWCzIEjBwWzVGL3BnzQ_W1S4Dt3HGT-C053FG5tYVgXLszv6aBD2v-P365ErKTqF5zOvsA"
}
response = client.post(url, data, format='json')
print(response.status_code)
print(response.json())
