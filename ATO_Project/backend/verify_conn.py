import http.client
import json

def check_server():
    try:
        conn = http.client.HTTPConnection("127.0.0.1", 8000, timeout=10)
        conn.request("GET", "/api/health")
        res = conn.getresponse()
        data = res.read().decode()
        print(f"Status: {res.status}")
        print(f"Data: {data}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_server()
