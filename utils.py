from dotenv import load_dotenv
import os
import json
import functools
from typing import Any, List, Union, Tuple

def append_output(func):
    @functools.wraps(func)  # Preserve the original function's metadata
    def wrapper(input: Union[Any, List[Any], Tuple[Any]], *args, **kwargs):
        
        # Check if the input is a list
        if isinstance(input, list) or isinstance(input, tuple):
            # Apply the function to each item in the list
            results = [func(item, *args, **kwargs) for item in input]
            return results
        else:
            # Apply the function to the single input object
            result = func(input, *args, **kwargs)
            return result

    return wrapper


def load_agent_meta():
    with open('./prompt.json', 'r') as file:
        prompt_data = json.load(file)
    return prompt_data


def load_env():
    # Load environment variables from the .env file
    load_dotenv("./.env")
    
    
@append_output 
def remove_markdown(text:str):
    md_symbol = "#*"
    for sym in md_symbol:
        text = text.replace(sym,"")
    
    return text


@append_output
def strip(text:str):
    return text.strip()


@append_output
def format_bot_response(text:str, remove_markdown:bool=False):
    text = remove_markdown(text) if remove_markdown else text
    text = strip(text)
    return text