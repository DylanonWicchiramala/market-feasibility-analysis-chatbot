import requests

url = "https://market-feasibility-analysis-chatbot-2-jelvbvjqna-uc.a.run.app/test"
# url = "http://127.0.0.1:8080/test"

headers = {"Content-Type": "application/json"}
data = {"message": "สวัสดี"}

response = requests.post(url, json=data, headers=headers)

if response.status_code == 200:
    print("Chatbot response:", response.json().get("response"))
else:
    print("Error:", response)