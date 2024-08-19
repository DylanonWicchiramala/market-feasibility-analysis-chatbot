from dotenv import load_dotenv
import os


def load_env():
    # Load environment variables from the .env file
    load_dotenv("./API_keys.env")
    # os.getenv('OPENAI_API_KEY')