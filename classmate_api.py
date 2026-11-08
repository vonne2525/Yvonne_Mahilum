import requests

url = "https://gwynethjoylaudv1.onrender.com/api/students"

try:
    response = requests.get(url, timeout=30)

    if response.status_code == 200:
        data = response.json()

        print("Classmate API Response:")

        if isinstance(data, dict):
            for key, value in data.items():
                print(f"{key}: {value}")
        else:
            print(data)

    else:
        print("Request failed.")
        print("Status Code:", response.status_code)

except requests.exceptions.RequestException as e:
    print("Connection error:", e)