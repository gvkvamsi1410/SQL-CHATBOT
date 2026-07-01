from dotenv import load_dotenv
import os
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st

load_dotenv()

def get_llm():
    # Uses the free tier of Google Gemini API
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("🔑 GEMINI_API_KEY not found in environment variables. Please add it to your .env file.")
        st.stop()
    return ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0.5, google_api_key=api_key)

def init_database(user: str, password: str, host: str, port: str, database: str) -> SQLDatabase:
  db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
  return SQLDatabase.from_uri(db_uri)

def get_sql_chain(db, llm):
  template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
    Based on the table schema below, write a SQL query as a normal text that would answer the user's question. Take the conversation history into account.
    
    <SCHEMA>{schema}</SCHEMA>
    
    Conversation History: {chat_history}
    
    Write only the SQL query as a normal text and nothing else. Do not wrap the SQL query in any other text, not even backticks.
    
    For example:
    Question: which 3 artists have the most tracks?
    SQL Query: SELECT ArtistId, COUNT(*) as track_count FROM Track GROUP BY ArtistId ORDER BY track_count DESC LIMIT 3;
    Question: Name 10 artists
    SQL Query: SELECT Name FROM Artist LIMIT 10;
    
    Your turn:
    
    Question: {question}
    SQL Query:
    """
    
  prompt = ChatPromptTemplate.from_template(template)
  
  def get_schema(_):
    return db.get_table_info()
  
  return (
    RunnablePassthrough.assign(schema=get_schema)
    | prompt
    | llm
    | StrOutputParser()
  )
    
def get_response(user_query: str, db: SQLDatabase, chat_history: list, llm):
  sql_chain = get_sql_chain(db, llm)
  
  template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
    Based on the table schema below, question, sql query, and sql response, write a natural language response.
    <SCHEMA>{schema}</SCHEMA>

    Conversation History: {chat_history}
    SQL Query: <SQL>{query}</SQL>
    User question: {question}
    SQL Response: {response}"""
  
  prompt = ChatPromptTemplate.from_template(template)
  
  chain = (
    RunnablePassthrough.assign(query=sql_chain).assign(
      schema=lambda _: db.get_table_info(),
      response=lambda vars: db.run(vars["query"]),
    )
    | prompt
    | llm
    | StrOutputParser()
  )
  
  return chain.invoke({
    "question": user_query,
    "chat_history": chat_history,
  })

st.set_page_config(page_title="Chat with MySQL Database", page_icon="💬")
st.title("💬 Chat with MySQL Database")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
      AIMessage(content="Hello! I'm a data analyst assistant. Ask me anything about your database."),
    ]

with st.sidebar:
    st.subheader("⚙️ Database Settings")
    st.write("Connect to your MySQL database.")
    
    host = st.text_input("Host", value="localhost", key="Host")
    port = st.text_input("Port", value="3306", key="Port")
    user = st.text_input("User", value="root", key="User")
    password = st.text_input("Password", type="password", value="Admin1234", key="Password")
    database = st.text_input("Database", value="metro_scheduling", key="Database")
    
    if st.button("Connect"):
        with st.spinner("🔗 Connecting to database..."):
            try:
              db = init_database(user, password, host, port, database)
              st.session_state.db = db
              st.success("✅ Connected to database!")
            except Exception as e:
              st.error(f"❌ Failed to connect to database: {e}")

for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.markdown(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.markdown(message.content)

user_query = st.chat_input("Type a message...")
if user_query is not None and user_query.strip() != "":
    if "db" not in st.session_state:
        st.error("⚠️ Please connect to the database first!")
    else:
        st.session_state.chat_history.append(HumanMessage(content=user_query))
        
        with st.chat_message("Human"):
            st.markdown(user_query)
            
        with st.chat_message("AI"):
            llm = get_llm()
            with st.spinner("Generating response..."):
                try:
                    response = get_response(user_query, st.session_state.db, st.session_state.chat_history, llm)
                    st.markdown(response)
                    st.session_state.chat_history.append(AIMessage(content=response))
                except Exception as e:
                    st.error(f"An error occurred: {e}")