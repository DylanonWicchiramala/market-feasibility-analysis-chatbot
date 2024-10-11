# Internal module
import ratelimit
from tools.search_optimizer import search_optimizer
from tools import sale_forecasting
from tools import gplace
import utils

from typing import Any, TypedDict, Optional, NotRequired, Literal
## Document vector store for context
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import CSVLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.tools import DuckDuckGoSearchRun, DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
# from langchain_google_community import GoogleSearchAPIWrapper
from langchain_experimental.utilities import PythonREPL
import glob
from langchain_core.tools import tool
import functools
from copy import copy
import os 
import itertools

utils.load_env()

class GetGeometricDataInput(TypedDict):
    keyword: str
    location_name: str
    radius: NotRequired[int]


class NearbySearchInput(TypedDict):
    keyword: str
    location_name: str
    radius: NotRequired[int]
    
    
class NearbyDenseCommunityInput(TypedDict):
    location_name: str
    radius: NotRequired[int]
    

class RestaurantSaleProject(TypedDict):
    base_price_per_unit: float|int
    category: Literal['Beverages', 'Biryani', 'Dessert', 'Extras', 'Fish', 'Other Snacks', 'Pasta', 'Pizza', 'Rice Bowl', 'Salad', 'Sandwich', 'Seafood', 'Soup', 'Starters']
    human_traffic:int
    cost_per_unit:NotRequired[int]
    monthly_fix_cost:NotRequired[int]
    
    
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
    address: {r['formatted_address']}\n
    location_name: {r['name']}\n
    """


# @tool
def nearby_search(input_dict: NearbySearchInput):
    """Searches for many places nearby the location based on a keyword. using keyword like \"coffee shop\", \"restaurants\". radius is the range to search from the location."""
    max_results = 10
    keyword = input_dict['keyword']
    location = input_dict['location_name']
    radius = int(input_dict.get('radius', 2000))

    # Call the internal function to find location
    location_coords = gplace.find_location(location, radius=radius)
    result = gplace.nearby_search(keyword, location_coords, radius)
    
    number_results = len(result)
    strout = f"number of {keyword} more than {number_results}\n" if number_results==60 else f"number of {keyword}: {number_results}\n"
    for r in result[:max_results]:
        # Use .get() to handle missing keys
        address = r.get('vicinity', 'N/A')
        location_info = r.get('geometry', {}).get('location', 'N/A')
        name = r.get('name', 'N/A')
        opening_hours = r.get('opening_hours', 'N/A')
        rating = r.get('rating', 'N/A')
        plus_code = r.get('plus_code', {}).get('global_code', 'N/A')
        
        strout += f"""
        - **{name}**
        \taddress: {address}
        \trating: {rating}
        """
    return strout[:800]


# @tool
def nearby_dense_community(input_dict: NearbyDenseCommunityInput) -> str:
    """ getting nearby dense community such as (community mall, hotel, school, etc), by location name, radius(in meters)
    return list of location community nearby, name, community type.
    """
    max_results = 10
    location = input_dict['location_name']
    radius = input_dict.get('radius', 2000)
    
    location_coords = gplace.find_location(location, radius=radius)
    result = gplace.nearby_dense_community(location_coords, radius)
    
    # Initializing the total sum
    sum = 0

    # Sample traffic_score dictionary
    traffic_score = {
        "lodging": 400,
        "mall": 1000,
        "school": 3000
    }

    for item in result:
        # Check if any type in 'types' matches the keys in traffic_score
        for place_type in item['types']:
            if place_type in traffic_score:
                sum += traffic_score[place_type]

    strout = f"There are {sum} people traffic nearby in the dense community."
    for r in result[:max_results]:
        # Use .get() to handle missing keys
        address = r.get('vicinity', 'N/A')
        location_types = r.get('types', 'N/A')
        name = r.get('name', 'N/A')
        opening_hours = r.get('opening_hours', 'N/A')
        rating = r.get('rating', 'N/A')
        plus_code = r.get('plus_code', {}).get('global_code', 'N/A')
        
        strout += f"""
        - **{name}**
        \ttypes: {location_types}
        """
    return strout.strip()[:800]
    


# search = GoogleSearchAPIWrapper()
# @tool
# @ratelimit.limits(calls=20, period=1)
# def google_search(keyword:str):
#     """Search Google for recent results. Using keyword as a text query search in google."""
#     try:
#         text = search.run(keyword)
#     except Exception as e:
#         return "google search not available at this time. please try again later"
#     unicode_chars_to_remove = ["\U000f1676", "\u2764", "\xa0", "▫️", "Δ"]
#     for char in unicode_chars_to_remove:
#         text = text.replace(char, "")
#     return search_optimizer(keyword, text)


# @tool
@ratelimit.limits(calls=15, period=1)
def duckduckgo_search(query:str):
    """A wrapper around DuckDuckGo Search. Useful for when you need to answer questions about current events. Input should be a search query."""
    engine = DuckDuckGoSearchRun()
    result = engine.invoke(query)
    unicode_chars_to_remove = ["\U000f1676", "\u2764", "\xa0", "▫️", "Δ", "#"]
    for char in unicode_chars_to_remove:
        result = result.replace(char, "")
    result = search_optimizer(query, result).replace("NOT_MATCH", "").strip()
    return result


# @tool
def python_repl(cmd:str):
    """A Python shell. Use this if you want to calculate something. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`."""
    return PythonREPL().run(cmd),


# @tool
def restaurant_sale_projection(input_dict:RestaurantSaleProject) -> str:
    """ create a sale, profit and number of orders projection forcast report of restaurant based on.
        category of food (category:str), 
        price of food (base_price_per_unit:float), 
        estimate number of human around dense communities(human_traffic:int).
        (this argument below are optional, use to calcualte profit)
        cost per unit sale (cost_per_unit:optional int) assign cost_per_unit=0 if you don't know the cost
        monthly fix cost such as rent (monthly_fix_cost:optinoal int) assign monthly_fix_cost=0 if you don't know the cost
    """
    base_price = input_dict['base_price_per_unit']
    category = input_dict['category']
    human_traffic = input_dict['human_traffic']
    cost_per_unit = input_dict.get("cost_per_unit", 0)
    monthly_fix_cost = input_dict.get("monthly_fix_cost", 0)
    
    result = sale_forecasting.restaurant_sale_project(base_price, category, human_traffic)
    
    if (cost_per_unit!=0 or monthly_fix_cost!=0):
        report = f"sale projection of {input_dict['category']}:\nweek\tnumber of order\tsale(forecast)\tprofit\n"
    else:
        report = f"sale projection of {input_dict['category']}:\nweek\tnumber of order\tsale(forecast)\n"
    
    for week, num_order in result.items():
        sale = num_order*base_price
        report += f"{week}\t{num_order:,.0f}\t\t{sale:,.0f}"
        
        # creat a profit report
        if cost_per_unit:
            cost = num_order*cost_per_unit + monthly_fix_cost/4.5
            profit = sale - cost
            report += f"\t{profit:,.0f}\n"
        else:
            report += "\n"
    
    return report


## Document csv
def get_documents(doc_dir="./document/"):
    get_path = lambda a: os.path.join(doc_dir, a)
    all_docs = [
        CSVLoader(
            file_path=get_path("community type by district.csv"),
            source_column="เขต",
            # metadata_columns=,
            
        ).load(),
        CSVLoader(
            file_path=get_path("thailand household expenditures by province.csv"),
            source_column="จังหวัด",
            # metadata_columns=,
            
        ).load(),
        CSVLoader(
            file_path=get_path("thailand population data by district.csv"),
            source_column="เขต",
            # metadata_columns=,
            
        ).load()
    ]
    all_docs = list(itertools.chain(*all_docs))

    return all_docs


def get_retriver_from_docs(docs):
    # Split text into chunks separated.
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=150)
    splits = text_splitter.split_documents(docs)

    # Text Vectorization.
    vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())

    # Retrieve and generate using the relevant snippets of the blog.
    retriever = vectorstore.as_retriever()
    
    return retriever


from langchain.tools.retriever import create_retriever_tool
from langchain_core.tools import Tool


docs = get_documents()
retriever = get_retriver_from_docs(docs)


# @tool
def search_population_community_household_expenditures_data(query:str):
    """Use this tool to retrieve information about population, community and household expenditures. by searching distinct or province"""
    result = retriever.invoke(query)
    output = result[0].page_content
    return output


# @tool
def get_geometric_data(input_dict:NearbySearchInput):
    """ this function is to get all geometric related data such as nearby competitor, dense community nearby, community type in distrinct, etc.
    """
    keyword = input_dict['keyword']
    location_name = input_dict['location_name']
    radius = int(input_dict.get('radius', 2000))
    
    result = gplace.find_place_from_text(location_name)
    r = result['candidates'][0]
    address:str = r['formatted_address']
    completed_location_name:str = r['name']
    
    nearby_competitor:str = nearby_search({
        "keyword": keyword,
        "location_name": location_name,
        "radius": int(radius),
    })
    dense_community:str = nearby_dense_community({
        'location_name': location_name,
        'radius': radius,
    })
    community_type = search_population_community_household_expenditures_data("community type " + address)
    household_expenditures = search_population_community_household_expenditures_data("household expenditures by province " + address)
    population = search_population_community_household_expenditures_data("population data by district " + address)
    
    return f"""
    location: {completed_location_name}

    **nearby competitors**
    {nearby_competitor}
    
    **nearby dense communities**
    {dense_community}
    
    **commnity type**
    {community_type}
    
    **household expenditures**
    {household_expenditures}
    
    **population**
    {population}
    """

# python_repl = tool(python_repl)
# search_population_community_household_expenditures_data = tool(save_tools_output(search_population_community_household_expenditures_data))
# nearby_search = tool(save_tools_output(nearby_search))
# nearby_dense_community = tool(save_tools_output(nearby_dense_community))
get_geometric_data = tool(get_geometric_data)
restaurant_sale_projection = tool(save_tools_output(restaurant_sale_projection))
duckduckgo_search = tool(duckduckgo_search)
find_place_from_text = tool(find_place_from_text)

all_tools = [restaurant_sale_projection, find_place_from_text, get_geometric_data, duckduckgo_search]  # Include both tools if needed