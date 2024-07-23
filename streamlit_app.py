import streamlit as st
import requests
import json
from exa_py import Exa

# Set page config
st.set_page_config(page_title="Company Search App", page_icon="🔍", layout="wide")

# Load credentials from secrets
USERNAME = st.secrets["credentials"]["username"]
PASSWORD = st.secrets["credentials"]["password"]
SERPER_API_KEY = st.secrets["serper"]["api_key"]
EXA_API_KEY = st.secrets["exa"]["api_key"]

def login():
    st.title("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            if username == USERNAME and password == PASSWORD:
                st.session_state["logged_in"] = True
                st.success("Logged in successfully!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

def serper_search(query):
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    response = requests.post(url, headers=headers, data=payload)
    return response.json()

def exa_search(query):
    exa = Exa(api_key=EXA_API_KEY)
    result = exa.search_and_contents(
        query,
        type="auto",
        num_results=25,
        text=True
    )
    return result

def exa_similar_search(domain):
    exa = Exa(api_key=EXA_API_KEY)
    result = exa.find_similar_and_contents(
        f"https://{domain}",
        num_results=10,
        text=True,
        exclude_domains=[domain],
        start_published_date="2024-01-23T16:01:08.902Z",
        end_published_date="2024-07-23T15:01:08.902Z",
        highlights=True
    )
    return result

def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login()
    else:
        st.title("Company Search App")

        company_domain = st.text_input("Enter company domain (e.g., apple.com):")
        search_button = st.button("Search")

        if search_button and company_domain:
            with st.spinner("Searching..."):
                # Perform searches
                serper_results = serper_search(company_domain)
                exa_results = exa_search(company_domain)
                exa_similar_results = exa_similar_search(company_domain)

                # Process and display results
                st.subheader("Serper Results")
                if "organic" in serper_results:
                    for result in serper_results["organic"]:
                        st.checkbox(f"{result['title']} - {result['link']}")

                st.subheader("Exa Search Results")
                for result in exa_results:
                    st.checkbox(f"{result['title']} - {result['url']}")

                st.subheader("Exa Similar Results")
                for result in exa_similar_results:
                    st.checkbox(f"{result['title']} - {result['url']}")

if __name__ == "__main__":
    main()
