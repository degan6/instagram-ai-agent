import base64
import os
import urllib.request

credentials = base64.b64encode(f"{os.environ['DASH_USER']}:{os.environ['DASH_PASS']}".encode()).decode()
request = urllib.request.Request("http://127.0.0.1:8080/api/state", headers={"Authorization": "Basic " + credentials})
with urllib.request.urlopen(request, timeout=4) as response:
    assert response.status == 200
