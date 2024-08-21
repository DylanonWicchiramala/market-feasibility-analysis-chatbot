from dotenv import load_dotenv
import os
import json


def load_agent_meta():
    with open('./prompt.json', 'r') as file:
        prompt_data = json.load(file)
    return prompt_data


def load_env():
    # Load environment variables from the .env file
    load_dotenv("./API_keys.env")
    # os.getenv('OPENAI_API_KEY')