
import requests

url = "https://yvonne-mahilum.onrender.com/skills"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    skills = data["skills"]

    print("My Skills:")

    for i, skill in enumerate(skills[:3], start=1):
        print(f"{i}. {skill}")

else:
    print("Request failed.")
    print("Status Code:", response.status_code)
