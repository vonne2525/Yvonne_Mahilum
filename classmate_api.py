
import requests

url = "https://gwynethjoylaud-1.onrender.com/skills"

try:
    response = requests.get(url, timeout=30)

    print("Status Code:", response.status_code)

    if response.status_code == 200:
        data = response.json()

        print("Classmate's API Response:")

        if isinstance(data, dict):
            for key, value in data.items():
                print(f"{key}: {value}")
        elif isinstance(data, list):
            for item in data:
                print(item)
        else:
            print(data)

    else:
        print("Request failed.")
        print(response.text)

except requests.exceptions.RequestException as error:
    print("Connection error:", error)
