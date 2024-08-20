import gplace

# %%
def find_place_from_text(location:str):
    """Finds a place and related data from the query text"""
    
    result = gplace.find_place_from_text(location)
    r = result['candidates'][0]
    return f"""
    address: {r['formatted_address']}\n
    location: {r['geometry']['location']}\n
    name: {r['name']}\n
    opening hours: {r['opening_hours']}\n
    rating: {r['rating']}\n
    """
    
def nearby_search(keyword:str, location:str, radius=2000, place_type=None):
    """Searches for many places nearby the location based on a keyword. using keyword like \"coffee shop\", \"restaurants\". radius is the range to search from the location"""
    location = gplace.find_location(location, radius=radius)
    result = gplace.nearby_search(keyword, location, radius)
    
    strout = ""
    for r in result:
        strout = strout + f"""
        address: {r['vicinity']}\n
        location: {r['geometry']['location']}\n
        name: {r['name']}\n
        opening hours: {r['opening_hours']}\n
        rating: {r['rating']}\n
        plus code: {r['plus_code']['global_code']}\n\n
        """
    return strout

# %%
# gplace_tools.py
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

find_place_from_text = tool(find_place_from_text)
nearby_search = tool(nearby_search)

tools = [find_place_from_text, nearby_search]

# Create ToolNodes for each tool
tool_node = ToolNode(tools)


