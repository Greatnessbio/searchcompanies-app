import streamlit as st
import requests
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from exa_py import Exa

st.set_page_config(page_title="Company Search App", page_icon="🔍", layout="wide")

# Load credentials from secrets
USERNAME = st.secrets["credentials"]["username"]
PASSWORD = st.secrets["credentials"]["password"]
SERPER_API_KEY = st.secrets["serper"]["api_key"]
EXA_API_KEY = st.secrets["exa"]["api_key"]
NEWSAPI_KEY = st.secrets["newsapi"]["api_key"]

# Initialize API clients
newsapi = NewsApiClient(api_key=NEWSAPI_KEY)
exa = Exa(api_key=EXA_API_KEY)

@st.cache_data(ttl=3600)
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

@st.cache_data(ttl=3600)
def exa_search(query, search_type, num_results, start_date, end_date):
    try:
        result = exa.search_and_contents(
            query,
            type=search_type,
            use_autoprompt=True,
            num_results=num_results,
            start_published_date=start_date,
            end_published_date=end_date,
            text={
                "max_characters": 300,
                "include_html_tags": True
            },
            highlights=True
        )
        return result
    except Exception as e:
        st.error(f"Error in Exa search: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def newsapi_search(query, sources, from_date, to_date, language='en', sort_by='relevancy'):
    try:
        all_articles = newsapi.get_everything(
            q=query,
            sources=sources,
            from_param=from_date,
            to=to_date,
            language=language,
            sort_by=sort_by,
            page_size=100
        )
        return all_articles
    except Exception as e:
        st.error(f"Error in NewsAPI search: {str(e)}")
        return None

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
                st.rerun()
            else:
                st.error("Invalid username or password")

def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login()
    else:
        st.title("Advanced Company Search App")

        st.sidebar.header("Search Parameters")
        company_domain = st.sidebar.text_input("Enter company domain (e.g., apple.com):")
        num_results = st.sidebar.slider("Number of results", 5, 50, 15)
        start_date = st.sidebar.date_input("Start date", datetime.now() - timedelta(days=30))
        end_date = st.sidebar.date_input("End date", datetime.now())

        exa_search_type = st.sidebar.selectbox("Exa Search Type", ["neural", "keyword", "semantic"])

        newsapi_sources = st.sidebar.text_input("NewsAPI Sources (comma-separated)", "")
        newsapi_language = st.sidebar.selectbox("NewsAPI Language", ["en", "de", "fr", "es"])
        newsapi_sort_by = st.sidebar.selectbox("NewsAPI Sort By", ["relevancy", "popularity", "publishedAt"])

        search_button = st.sidebar.button("Search")

        if search_button and company_domain:
            with st.spinner("Searching..."):
                formatted_start_date = start_date.strftime("%Y-%m-%d")
                formatted_end_date = end_date.strftime("%Y-%m-%d")

                serper_results = serper_search(company_domain, num_results, formatted_start_date, formatted_end_date)
                exa_results = exa_search(company_domain, exa_search_type, num_results, formatted_start_date, formatted_end_date)
                newsapi_results = newsapi_search(company_domain, newsapi_sources, formatted_start_date, formatted_end_date, newsapi_language, newsapi_sort_by)

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.subheader("Serper Results")
                    if "organic" in serper_results:
                        for result in serper_results["organic"]:
                            st.write(f"**{result['title']}**")
                            st.write(result['snippet'])
                            st.write(f"[Link]({result['link']})")
                            st.write("---")
                    else:
                        st.warning("No organic results found in Serper search.")

                with col2:
                    st.subheader("Exa Search Results")
                    if exa_results and "results" in exa_results:
                        for result in exa_results["results"]:
                            st.write(f"**{result.get('title', 'No title')}**")
                            if result.get('highlights'):
                                st.write("Highlights:")
                                for highlight in result['highlights']:
                                    st.markdown(f"- {highlight}", unsafe_allow_html=True)
                            else:
                                st.write(result.get('text', 'No description available'))
                            st.write(f"[Link]({result.get('url', '#')})")
                            st.write("---")
                    else:
                        st.warning("No results found in Exa search.")

                with col3:
                    st.subheader("NewsAPI Results")
                    if newsapi_results and "articles" in newsapi_results:
                        st.write(f"Total results: {newsapi_results['totalResults']}")
                        for article in newsapi_results["articles"]:
                            st.write(f"**{article['title']}**")
                            st.write(article['description'])
                            st.write(f"[Link]({article['url']})")
                            st.write("---")
                    else:
                        st.warning("No results found in NewsAPI search.")
                        st.write("NewsAPI response:", newsapi_results)

if __name__ == "__main__":
    main()
