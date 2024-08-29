import gplace
from typing import TypedDict, Optional, NotRequired
import utils
## Document vector store for context
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import CSVLoader
from langchain_openai import OpenAIEmbeddings
import glob
from langchain_core.tools import tool
import functools
from copy import copy


utils.load_env()

class NearbySearchInput(TypedDict):
    keyword: str
    location_name: str
    radius: NotRequired[int]
    
    
class NearbyDenseCommunityInput(TypedDict):
    location_name: str
    radius: NotRequired[int]
    
    
tools_outputs=""


def get_tools_output():
    global tools_outputs
    result = copy(tools_outputs)
    tools_outputs = ""
    return result


def save_tools_output(func):
    @functools.wraps(func) 
    def wrapper(*args, **kwargs):
        global tools_outputs
        # Call the original function and get its return value
        result = func(*args, **kwargs)
        # Append the result to tools_outputs
        tools_outputs += str(result) + "\n"
        # Return the original result
        return result
    return wrapper
    

# %%
# @tool
def find_place_from_text(location:str):
    """Finds a place location and related data from the query text"""
    result = gplace.find_place_from_text(location)
    r = result['candidates'][0]
    # location: {r['geometry']['location']}\n
    return f"""
    # address: {r['formatted_address']}\n
    location_name: {r['name']}\n
    """


# @tool
def nearby_search(input_dict: NearbySearchInput):
    """Searches for many places nearby the location based on a keyword. using keyword like \"coffee shop\", \"restaurants\". radius is the range to search from the location."""
    max_results = 5
    keyword = input_dict['keyword']
    location = input_dict['location_name']
    radius = input_dict.get('radius', 2000)

    # Call the internal function to find location
    location_coords = gplace.find_location(location, radius=radius)
    result = gplace.nearby_search(keyword, location_coords, radius)
    
    number_results = len(result)
    strout = "number of results more than {}\n".format(number_results) if number_results==60 else "number of results: {}\n".format(number_results)
    for r in result[:max_results]:
        # Use .get() to handle missing keys
        address = r.get('vicinity', 'N/A')
        location_info = r.get('geometry', {}).get('location', 'N/A')
        name = r.get('name', 'N/A')
        opening_hours = r.get('opening_hours', 'N/A')
        rating = r.get('rating', 'N/A')
        plus_code = r.get('plus_code', {}).get('global_code', 'N/A')
        
        strout += f"""
        **{name}**
        address: {address}
        rating: {rating}
        """
    return strout[:800]


# @tool
def nearby_dense_community(input_dict: NearbyDenseCommunityInput) -> str:
    """ getting nearby dense community such as (community mall, hotel, school, etc), by location name, radius(in meters)
    return list of location community nearby, name, community type.
    """
    max_results = 5
    location = input_dict['location_name']
    radius = input_dict.get('radius', 2000)
    
    location_coords = gplace.find_location(location, radius=radius)
    result = gplace.nearby_dense_community(location_coords, radius)
    
    strout = ""
    for r in result[:max_results]:
        # Use .get() to handle missing keys
        address = r.get('vicinity', 'N/A')
        location_types = r.get('types', 'N/A')
        name = r.get('name', 'N/A')
        opening_hours = r.get('opening_hours', 'N/A')
        rating = r.get('rating', 'N/A')
        plus_code = r.get('plus_code', {}).get('global_code', 'N/A')
        
        strout += f"""
        name: {name}
        types: {location_types}
        """
    return strout.strip()[:800]


# @tool
# def google_search(keyword:str):
#     """Search Google for recent results. Using keyword as a text query search in google."""
#     try:
#         text = search.run(keyword)
#     except Exception as e:
#         return "google search not available at this time. please try again later"
#     unicode_chars_to_remove = ["\U000f1676", "\u2764", "\xa0", "▫️", "Δ"]
#     for char in unicode_chars_to_remove:
#         text = text.replace(char, "")
#     return text[:800]


## Document csv
def get_documents(file_pattern="document/*.csv"):
    file_paths = tuple(glob.glob(file_pattern))

    all_docs = []

    for file_path in file_paths:
        loader = CSVLoader(file_path=file_path)
        docs = loader.load()
        all_docs.extend(docs)  # Add the documents to the list
        
    return all_docs


def get_retriver_from_docs(docs):
    # Split text into chunks separated.
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    splits = text_splitter.split_documents(docs)

    # Text Vectorization.
    vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())

    # Retrieve and generate using the relevant snippets of the blog.
    retriever = vectorstore.as_retriever()
    
    return retriever


from langchain.tools.retriever import create_retriever_tool
from langchain_core.tools import Tool
from langchain_community.tools import DuckDuckGoSearchRun


docs = get_documents()
retriever = get_retriver_from_docs(docs)

population_doc_retriever = create_retriever_tool(
    retriever,
    "search_population_community_household_expenditures_data",
    "Use this tool to retrieve information about population, community and household expenditures. by searching distinct or province"
)
duckduckgo_search = DuckDuckGoSearchRun()
find_place_from_text = tool(find_place_from_text)
nearby_search = tool(save_tools_output(nearby_search))
nearby_dense_community = tool(save_tools_output(nearby_dense_community))