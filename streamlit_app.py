import streamlit as st
import requests
import json
from datetime import datetime, timedelta
from newsapi import NewsApiClient

# Set page config
st.set_page_config(page_title="Company Search App", page_icon="🔍", layout="wide")

# Load credentials from secrets
USERNAME = st.secrets["credentials"]["username"]
PASSWORD = st.secrets["credentials"]["password"]
SERPER_API_KEY = st.secrets["serper"]["api_key"]
EXA_API_KEY = st.secrets["exa"]["api_key"]
NEWSAPI_KEY = st.secrets["newsapi"]["api_key"]

# Initialize NewsAPI client
newsapi = NewsApiClient(api_key=NEWSAPI_KEY)

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
                st.rerun()  # Updated from st.experimental_rerun()
            else:
                st.error("Invalid username or password")

def serper_search(query, num_results, start_date, end_date):
    url = "https://google.serper.dev/search"
    payload = {
        "q": query,
        "num": num_results,
        "tbs": f"cdr:1,cd_min:{start_date},cd_max:{end_date}"
    }
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def exa_search(query, search_type, category, num_results, start_date, end_date):
    url = "https://api.exa.ai/search"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": EXA_API_KEY
    }
    payload = {
        "query": query,
        "type": search_type,
        "category": category,
        "numResults": num_results,
        "startPublishedDate": start_date,
        "endPublishedDate": end_date
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error in Exa search: {str(e)}")
        return None

def newsapi_search(query, sources, from_date, to_date, language='en', sort_by='relevancy', page=1):
    try:
        all_articles = newsapi.get_everything(q=query,
                                              sources=sources,
                                              from_param=from_date,
                                              to=to_date,
                                              language=language,
                                              sort_by=sort_by,
                                              page=page)
        return all_articles
    except Exception as e:
        st.error(f"Error in NewsAPI search: {str(e)}")
        return None

def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login()
    else:
        st.title("Advanced Company Search App")

        # Initialize session state variables
        if "company_domain" not in st.session_state:
            st.session_state["company_domain"] = ""
        if "serper_results" not in st.session_state:
            st.session_state["serper_results"] = None
        if "exa_results" not in st.session_state:
            st.session_state["exa_results"] = None
        if "newsapi_results" not in st.session_state:
            st.session_state["newsapi_results"] = None
        if "selected_companies" not in st.session_state:
            st.session_state["selected_companies"] = set()

        # User input for search parameters
        st.subheader("Search Parameters")
        col1, col2, col3 = st.columns(3)

        with col1:
            company_domain = st.text_input("Enter company domain (e.g., sambasci.com):", value=st.session_state["company_domain"])
            num_results = st.slider("Number of results", 5, 50, 15)
            start_date = st.date_input("Start date", datetime.now() - timedelta(days=365))
            end_date = st.date_input("End date", datetime.now())

        with col2:
            exa_search_type = st.selectbox("Exa Search Type", ["magic", "neural", "keyword"])
            exa_category = st.selectbox("Exa Category", ["company", "news", "research paper", "github", "tweet", "movie", "song", "personal site", "pdf"])

        with col3:
            newsapi_sources = st.text_input("NewsAPI Sources (comma-separated)", "bbc-news,the-verge")
            newsapi_language = st.selectbox("NewsAPI Language", ["en", "de", "fr", "es"])
            newsapi_sort_by = st.selectbox("NewsAPI Sort By", ["relevancy", "popularity", "publishedAt"])

        search_button = st.button("Search")

        if search_button and company_domain:
            st.session_state["company_domain"] = company_domain
            with st.spinner("Searching..."):
                # Format dates for API calls
                formatted_start_date = start_date.strftime("%Y-%m-%d")
                formatted_end_date = end_date.strftime("%Y-%m-%d")
                exa_start_date = f"{formatted_start_date}T00:00:00.000Z"
                exa_end_date = f"{formatted_end_date}T23:59:59.999Z"

                # Perform searches
                st.session_state["serper_results"] = serper_search(company_domain, num_results, formatted_start_date, formatted_end_date)
                st.session_state["exa_results"] = exa_search(company_domain, exa_search_type, exa_category, num_results, exa_start_date, exa_end_date)
                st.session_state["newsapi_results"] = newsapi_search(company_domain, newsapi_sources, formatted_start_date, formatted_end_date, newsapi_language, newsapi_sort_by)

        if st.session_state["serper_results"] or st.session_state["exa_results"] or st.session_state["newsapi_results"]:
            st.subheader("Search Results")
            
            col1, col2, col3 = st.columns(3)
            
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

            with col3:
                st.subheader("NewsAPI Results")
                if st.session_state["newsapi_results"] and "articles" in st.session_state["newsapi_results"]:
                    for article in st.session_state["newsapi_results"]["articles"]:
                        key = f"newsapi_{article['url']}"
                        if st.checkbox(f"{article['title']} - {article['source']['name']}", key=key, value=key in st.session_state["selected_companies"]):
                            st.session_state["selected_companies"].add(key)
                        else:
                            st.session_state["selected_companies"].discard(key)
                else:
                    st.warning("No results found in NewsAPI search.")

        # Display selected companies
        if st.session_state["selected_companies"]:
            st.subheader("Selected Companies")
            for company in st.session_state["selected_companies"]:
                st.write(company)

if __name__ == "__main__":
    main()
