import gplace
from typing import TypedDict, Optional
from langchain_google_community import GoogleSearchAPIWrapper
import utils
## Document vector store for context
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import CSVLoader
from langchain_openai import OpenAIEmbeddings
import glob

utils.load_env()

search = GoogleSearchAPIWrapper()


class NearbySearchInput(TypedDict):
    keyword: str
    location_name: str
    radius: int
    place_type: Optional[str]
    
    
class NearbyDenseCommunityInput(TypedDict):
    location_name: str
    radius: int
    
    
class GoogleSearchInput(TypedDict):
    keyword: str


# %%
def find_place_from_text(location:str):
    """Finds a place and related data from the query text"""
    
    result = gplace.find_place_from_text(location)
    r = result['candidates'][0]
    return f"""
    address: {r['formatted_address']}\n
    location: {r['geometry']['location']}\n
    location_name: {r['name']}\n
    """
    # return f"""
    # address: {r['formatted_address']}\n
    # location: {r['geometry']['location']}\n
    # location_name: {r['name']}\n
    # """
    
# def nearby_search(keyword:str, location:str, radius=2000, place_type=None):
#     """Searches for many places nearby the location based on a keyword. using keyword like \"coffee shop\", \"restaurants\". radius is the range to search from the location"""
#     location = gplace.find_location(location, radius=radius)
#     result = gplace.nearby_search(keyword, location, radius)
    
#     strout = ""
#     for r in result:
#         strout = strout + f"""
#         address: {r['vicinity']}\n
#         location: {r['geometry']['location']}\n
#         name: {r['name']}\n
#         opening hours: {r['opening_hours']}\n
#         rating: {r['rating']}\n
#         plus code: {r['plus_code']['global_code']}\n\n
#         """
#     return strout


def nearby_search(input_dict: NearbySearchInput):
    """Searches for many places nearby the location based on a keyword. using keyword like \"coffee shop\", \"restaurants\". radius is the range to search from the location."""
    
    max_results = 10
    keyword = input_dict['keyword']
    location = input_dict['location_name']
    radius = input_dict.get('radius', 2000)
    place_type = input_dict.get('place_type', None)

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
        
        # strout += f"""
        # address: {address}\n
        # location: {location_info}\n
        # lacation_name: {name}\n
        # opening hours: {opening_hours}\n
        # rating: {rating}\n
        # plus code: {plus_code}\n\n
        # """
        
        strout += f"""
        **{name}**\n
        address: {address}\n
        rating: {rating}\n\n
        """
    return strout


def nearby_dense_community(input_dict: NearbyDenseCommunityInput) -> str:
    """ getting nearby dense community such as (community mall, hotel, school, etc), by location name, radius(in meters)
    return list of location community nearby, name, community type.
    """
    location = input_dict['location_name']
    radius = input_dict['radius']
    
    location_coords = gplace.find_location(location, radius=radius)
    result = gplace.nearby_dense_community(location_coords, radius)
    
    strout = ""
    for r in result:
        # Use .get() to handle missing keys
        address = r.get('vicinity', 'N/A')
        location_types = r.get('types', 'N/A')
        name = r.get('name', 'N/A')
        opening_hours = r.get('opening_hours', 'N/A')
        rating = r.get('rating', 'N/A')
        plus_code = r.get('plus_code', {}).get('global_code', 'N/A')
        
        strout += f"""
        name: {name}\n
        types: {location_types}\n
        """
    return strout


def google_search(input_dict: GoogleSearchInput):
    """Search Google for a keyword."""
    return search.run(input_dict['keyword'])


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
from langchain_core.tools import tool
from langchain_core.tools import Tool


docs = get_documents()
retriever = get_retriver_from_docs(docs)

population_doc_retriever = create_retriever_tool(
    retriever,
    "search_population_community_household_expenditures_data",
    "Use this tool to retrieve information about population, community and household expenditures. by searching distinct or province"
)
# google_search = Tool(
#     name="google_search",
#     description="Search Google for recent results.",
#     func=search.run,
# )
google_search = tool(google_search)
find_place_from_text = tool(find_place_from_text)
nearby_search = tool(nearby_search)
nearby_dense_community = tool(nearby_dense_community)