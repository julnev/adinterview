import openai
import streamlit as st
from instructions import get_content
from google.cloud import storage
from google.auth import exceptions
from google.auth.transport.requests import Request
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account
import os
import ssl
from datetime import datetime


# Disable SSL certificate verification (not recommended for production)
ssl._create_default_https_context = ssl._create_unverified_context


st.set_page_config(
    page_title="Your App",
    page_icon=":memo:",
)

st.title("Meet the Experience Innovation Team ///")
"""Ask me anything :)"""

openai.api_key = st.secrets["OPENAI_API_KEY"]

# Accéder aux secrets Streamlit
google_cloud_storage_secrets = st.secrets["google_cloud_storage"]

# Accéder aux valeurs individuelles
project_id = google_cloud_storage_secrets["project_id"]
private_key_id = google_cloud_storage_secrets["private_key_id"]
private_key = google_cloud_storage_secrets["private_key"]
client_email = google_cloud_storage_secrets["client_email"]
client_id = google_cloud_storage_secrets["client_id"]
auth_uri = google_cloud_storage_secrets["auth_uri"]
token_uri = google_cloud_storage_secrets["token_uri"]
auth_provider_x509_cert_url = google_cloud_storage_secrets["auth_provider_x509_cert_url"]
client_x509_cert_url = google_cloud_storage_secrets["client_x509_cert_url"]

# Créer un objet de type ServiceAccountCredentials
credentials = ServiceAccountCredentials.from_json_keyfile_dict({
    "client_email": client_email,
    "private_key": private_key,
    "private_key_id": private_key_id,
    "client_id": client_id,
    "type": google_cloud_storage_secrets["type"]
}, ["https://www.googleapis.com/auth/cloud-platform"])

try:
    # Utiliser le client de stockage
    storage_client = storage.Client(credentials=credentials)
except exceptions.GoogleAuthError as e:
    # Handle authentication error
    print(f"Authentication failed: {e}")


content = get_content()


if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"


def save_message_to_storage(messages, conversation_id):
    bucket_name = "adinterviews"
    object_path = f"conversations/{conversation_id}.txt"

    # Check if the file already exists, and create it if it doesn't
    try:
        bucket = storage_client.get_bucket(bucket_name)
    except NotFound:
        bucket = storage_client.create_bucket(bucket_name)

    # Concatenate all non-system messages into a single string
    conversation_content = ""
    for message in messages:
        if message['role'] != 'system':
            conversation_content += f"{message['role']}: {message['content']}\n"

    # Upload the entire conversation to the file
    blob = bucket.blob(object_path)
    blob.upload_from_string(conversation_content, content_type="text/plain")

    print(f"Conversation saved to Google Cloud Storage for conversation ID {conversation_id}")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
                   {"role": "system", "content": content} #"You are Adi, a friendly team member from the Experience Innovation team in Adidas. You have to ask to user his name and role in the company."},
                      ]

# Determine the conversation ID based on the current timestamp
conversation_id = datetime.now().strftime("%Y%m%d%H%M%S")

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

 # Save the user and assistant messages to Google Cloud Storage
save_message_to_storage(st.session_state.messages, conversation_id)
