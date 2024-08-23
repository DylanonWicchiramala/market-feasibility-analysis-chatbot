import gplace
from typing import TypedDict, Optional
from langchain_google_community import GoogleSearchAPIWrapper
import utils

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
    """Search Google for recent results."""
    return search.run(input_dict['keyword'])


# %%
# gplace_tools.py
from langchain_core.tools import Tool
from langchain_core.tools import tool

google_search = tool(google_search)
find_place_from_text = tool(find_place_from_text)
nearby_search = tool(nearby_search)
nearby_dense_community = tool(nearby_dense_community)