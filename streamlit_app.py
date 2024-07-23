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
        response.raise_for_status()
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

        # Initialize session state variables
        if "company_domain" not in st.session_state:
            st.session_state["company_domain"] = ""
        if "serper_results" not in st.session_state:
            st.session_state["serper_results"] = None
        if "exa_results" not in st.session_state:
            st.session_state["exa_results"] = None
        if "selected_companies" not in st.session_state:
            st.session_state["selected_companies"] = set()

        company_domain = st.text_input("Enter company domain (e.g., sambasci.com):", value=st.session_state["company_domain"])
        search_button = st.button("Search")

        if search_button and company_domain:
            st.session_state["company_domain"] = company_domain
            with st.spinner("Searching..."):
                # Perform searches
                st.session_state["serper_results"] = serper_search(company_domain)
                st.session_state["exa_results"] = exa_search(company_domain)

        if st.session_state["serper_results"] or st.session_state["exa_results"]:
            st.subheader("Search Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Serper Results")
                if "organic" in st.session_state["serper_results"]:
                    for result in st.session_state["serper_results"]["organic"]:
                        key = f"serper_{result['link']}"
                        if st.checkbox(f"{result['title']} - {result['link']}", key=key, value=key in st.session_state["selected_companies"]):
                            st.session_state["selected_companies"].add(key)
                        else:
                            st.session_state["selected_companies"].discard(key)
                else:
                    st.warning("No organic results found in Serper search.")

            with col2:
                st.subheader("Exa Search Results")
                if st.session_state["exa_results"] and "results" in st.session_state["exa_results"]:
                    for result in st.session_state["exa_results"]["results"]:
                        key = f"exa_{result.get('url', '')}"
                        if st.checkbox(f"{result.get('title', 'No title')} - {result.get('url', 'No URL')}", key=key, value=key in st.session_state["selected_companies"]):
                            st.session_state["selected_companies"].add(key)
                        else:
                            st.session_state["selected_companies"].discard(key)
                else:
                    st.warning("No results found in Exa search.")

        # Display selected companies
        if st.session_state["selected_companies"]:
            st.subheader("Selected Companies")
            for company in st.session_state["selected_companies"]:
                st.write(company)

if __name__ == "__main__":
    main()
