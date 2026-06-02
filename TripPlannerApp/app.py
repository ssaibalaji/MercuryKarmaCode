import streamlit as st
from dotenv import load_dotenv

# Core LangChain components
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

# Chain helpers live in langchain-classic since LangChain 1.0
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains import create_retrieval_chain

# 1. INITIAL SETUP
load_dotenv()
st.set_page_config(page_title="Pro Trip Planner", page_icon="✈️", layout="wide")

# Connect to the Vector DB created in Step 7
embeddings = OpenAIEmbeddings()
vector_db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

# 2. SIDEBAR FOR TRIP CONTEXT
with st.sidebar:
    st.header("📍 Trip Preferences")
    destination = st.text_input("Where to?", value="Tokyo")
    budget = st.selectbox("Budget Tier", ["Economy", "Standard", "Luxury"])
    if st.button("Clear History"):
        st.session_state.chat_history = []
        st.rerun()

st.title("✈️ AI Travel Agent (LCEL RAG)")

# 3. CONSTRUCT THE RAG CHAIN (The modern way)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

system_prompt = (
    "You are a professional Travel Concierge. Use the provided context to answer the user's question."
    "\n\n"
    "STRICT RULES:"
    "1. SCOPE: If the user asks about topics unrelated to travel, hotels, or trip planning, "
    "politely decline and redirect them back to travel."
    "2. SAFETY: If the user asks for a destination flagged as 'Level 4: Do Not Travel' in the context, "
    "you MUST warn them and refuse to generate an itinerary for that location."
    "3. HONESTY: If the answer is not in the context, say 'I'm sorry, I don't have our official policy on that, "
    "but based on general travel standards...' then provide a general answer."
    "4. FORMATTING: Use bullet points for readability."
    "\n\n"
    "Context: {context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

question_answer_chain = create_stuff_documents_chain(llm, prompt)
# We add 'return_source_documents=True' to see where the info came from
rag_chain = create_retrieval_chain(
    vector_db.as_retriever(search_kwargs={"k": 3}), 
    question_answer_chain
)

# 4. CHAT INTERFACE & LOGIC
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Render chat history
for message in st.session_state.chat_history:
    with st.chat_message("AI" if isinstance(message, AIMessage) else "Human"):
        st.write(message.content)

# Handle new user input
if user_query := st.chat_input("Ask about our policies..."):
    st.chat_message("Human").write(user_query)
    st.session_state.chat_history.append(HumanMessage(content=user_query))
    
    with st.chat_message("AI"):
        response = rag_chain.invoke({"input": user_query})
        answer = response["answer"]
        st.write(answer)
        
        # --- NEW: SOURCE EXPANDER ---
        # This shows the user the exact snippets the AI read
        with st.expander("🔍 View Official Sources"):
            for doc in response["context"]:
                st.info(f"Source: {doc.page_content[:200]}...")
        
    st.session_state.chat_history.append(AIMessage(content=answer))