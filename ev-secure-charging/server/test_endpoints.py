import requests
import json
import time

def test_endpoint(url, method="GET", json_data=None, headers=None):
    try:
        if method == "GET":
            res = requests.get(url, headers=headers)
        else:
            res = requests.post(url, json=json_data, headers=headers)
        return res.status_code, res.text[:200]
    except Exception as e:
        return "ERROR", str(e)

print(test_endpoint("http://localhost:5000/status"))
print(test_endpoint("http://localhost:5000/api/security/threat-level"))
print(test_endpoint("http://localhost:5000/analytics/dashboard"))

