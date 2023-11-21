import openai
import streamlit as st
from instructions import get_content
import ssl
import sqlite3

# Disable SSL certificate verification (not recommended for production)
ssl._create_default_https_context = ssl._create_unverified_context


st.set_page_config(
    page_title="Your App",
    page_icon=":memo:",
)


st.title("Meet the Experience Innovation Team ///")
"""Ask me anything :)"""

openai.api_key = st.secrets["OPENAI_API_KEY"]

content = get_content()


if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

    # Function to create a SQLite connection and table if not exists
def create_connection():
    connection = sqlite3.connect("conversation_history.db")
    cursor = connection.cursor()

    # Create a table if not exists
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS conversation_history
          (id INTEGER PRIMARY KEY AUTOINCREMENT,
           role TEXT NOT NULL,
           content TEXT NOT NULL)'''
    )

    connection.commit()
    print("Table created successfully")  # Add this line to check if the table is created
    return connection

# Function to save a message to the SQLite database
def save_message_to_db(role, content):
    try:
        with create_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO conversation_history (role, content) VALUES (?, ?)",
                (role, content),
            )
            connection.commit()
            print(f"Message saved to database: {role}: {content}")
    except Exception as e:
        print(f"Error saving message to database: {e}")


# Create a connection to the database
db_connection = create_connection()


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
                   {"role": "system", "content": content} #"You are Adi, a friendly team member from the Experience Innovation team in Adidas. You have to ask to user his name and role in the company."},
                      ]

# Display existing conversation history
for message in st.session_state.messages:
    if message["role"] != "system":
      with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Hello, how are you today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

# Assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for response in openai.ChatCompletion.create(
            model=st.session_state["openai_model"],
            messages=[
               {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        ):
            full_response += response.choices[0].delta.get("content", "")
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})

  # Save the user and assistant messages to the database
    save_message_to_db("user", prompt)
    save_message_to_db("assistant", full_response)


    # Close the database connection
db_connection.close()