from gplace import find_place_from_text, find_location, nearby_search
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

find_place_from_text = tool(find_place_from_text)
find_location = tool(find_location)
nearby_search = tool(nearby_search)

tools = [find_place_from_text, find_location, nearby_search]

# Create ToolNodes for each tool
tool_node = ToolNode(tools)


