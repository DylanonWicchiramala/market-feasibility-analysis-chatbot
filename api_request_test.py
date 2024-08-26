import requests

url = "http://localhost:5000"
headers = {"Content-Type": "application/json"}
data = {"message": "Hello, chatbot!"}

response = requests.post(url, json=data, headers=headers)

if response.status_code == 200:
    print("Chatbot response:", response.json().get("response"))
else:
    print("Error:", response.json())