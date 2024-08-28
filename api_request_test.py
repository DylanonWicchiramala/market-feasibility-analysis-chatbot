import requests

url = "https://market-feasibility-analysis-chatbot-2-jelvbvjqna-uc.a.run.app/test"
headers = {"Content-Type": "application/json"}
data = {"message": "วิเคราะห์การเปิดร้านอาหารแถวนวลจันทร์"}

response = requests.post(url, json=data, headers=headers)

if response.status_code == 200:
    print("Chatbot response:", response.json().get("response"))
else:
    print("Error:", response)