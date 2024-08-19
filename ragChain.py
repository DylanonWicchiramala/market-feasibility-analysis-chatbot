from dotenv import load_dotenv
import os
from langchain_community.document_loaders import TextLoader, WebBaseLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI


            
# Load environment variables from the .env file
load_dotenv("./API_keys.env")
os.getenv('OPENAI_API_KEY')

os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_PROJECT"] = "Multi-agent Collaboration"

def get_document():
    # Getting data for QA.
    loader = TextLoader("./data_source.txt")
    docs = loader.load()
    return docs


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# Getting document for QA.
docs = get_document()

# Split documents into chunks separated.
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
splits = text_splitter.split_documents(docs)

# Text Vectorization.
vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())

# Import chat gpt model.
llm = ChatOpenAI(model="gpt-4o-mini")

# Retrieve and generate using the relevant snippets of the blog.
retriever = vectorstore.as_retriever()
prompt = ChatPromptTemplate.from_messages(
        [
            (
                "assistant",
                """You are an assistant for question-answering tasks. Use the provided context to answer the question. If you don’t know the answer, simply state that you don’t know. Keep your response concise, using no more than three sentences. Please reply using in the same language as the question. Note: You are a male.
                Question: {question} 
                Context: {context} 
                Answer:"""
                
            ),
        ]
    )

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)


def submitUserMessage(message:str):
    ans = rag_chain.invoke(message)
    return ans