import streamlit as st
import requests
import json

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
    url = "https://api.exa.ai/search"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": EXA_API_KEY
    }
    payload = {
        "query": query,
        "numResults": 10,
        "type": "neural"
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error in Exa search: {str(e)}")
        return None

def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login()
    else:
        st.title("Company Search App")

        company_domain = st.text_input("Enter company domain (e.g., sambasci.com):")
        search_button = st.button("Search")

        if search_button and company_domain:
            with st.spinner("Searching..."):
                # Perform searches
                serper_results = serper_search(company_domain)
                exa_results = exa_search(company_domain)

                # Process and display results
                st.subheader("Serper Results")
                if "organic" in serper_results:
                    for result in serper_results["organic"]:
                        st.checkbox(f"{result['title']} - {result['link']}")
                else:
                    st.warning("No organic results found in Serper search.")

                st.subheader("Exa Search Results")
                if exa_results and "results" in exa_results:
                    for result in exa_results["results"]:
                        st.checkbox(f"{result.get('title', 'No title')} - {result.get('url', 'No URL')}")
                else:
                    st.warning("No results found in Exa search.")

if __name__ == "__main__":
    main()
