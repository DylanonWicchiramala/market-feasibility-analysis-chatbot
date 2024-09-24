from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


# Define the LLM to use (OpenAI in this example)
llm = ChatOpenAI(
    model="gpt-4o-mini-2024-07-18", 
    temperature=0, 
    top_p=0, 
    )
        

def search_optimizer(search_query: str, search_result: str) -> str:
    """
    This function optimizes search results by summarizing them in a way that best matches the search query.
    
    Parameters:
    - search_query (str): The user's search query.
    - search_results (list): A list of search result strings that need to be summarized.

    Returns:
    - str: A summary of the search results optimized to match the search query.
    """


    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a search optimizer agent. Your task is to read search results and provide a shorten summary that related the search query.
                If there are not related, just povide the summary from search results, Then prefix your response with `NOT_MATCH`
                """
            ),
            (
                "human",
                """
                {input}
                """
            )
        ]
    )
    
    agent = prompt | llm
    
    input = f"""
        search_query:
        {search_query}
        search_result:
        {search_result}
    """
    # Run the agent and get the summary
    response = agent.invoke(input)
    
    return response.content