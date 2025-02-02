import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from exa_py import Exa
import exa_py

st.set_page_config(page_title="Search App", page_icon="🔍", layout="wide")

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
    url = "https://api.exa.ai/search"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": EXA_API_KEY
    }
    payload = {
        "query": query,
        "type": search_type,
        "numResults": num_results,
        "startPublishedDate": start_date,
        "endPublishedDate": end_date,
        "highlights": True,
        "useAutoprompt": True,
        "text": {
            "max_characters": 13000,
            "include_html_tags": True
        }
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error in Exa search: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def newsapi_search(query, sources, from_date, to_date, num_results, language='en', sort_by='relevancy'):
    try:
        all_articles = newsapi.get_everything(
            q=query,
            sources=sources,
            from_param=from_date,
            to=to_date,
            language=language,
            sort_by=sort_by,
            page_size=num_results
        )
        return all_articles
    except Exception as e:
        st.error(f"Error in NewsAPI search: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def get_url_contents(urls):
    results = {}
    try:
        batch_results = exa.get_contents(
            urls,
            text=True,
            highlights={
                "num_sentences": 4
            }
        )
        if isinstance(batch_results, exa_py.api.SearchResponse):
            for result in batch_results.results:
                results[result.url] = {
                    'title': result.title,
                    'text': result.text[:300] + "..." if result.text else "No text available",
                    'highlights': result.highlights if hasattr(result, 'highlights') else []
                }
        else:
            st.warning(f"Unexpected response type: {type(batch_results)}")
            st.write("Response:", batch_results)
    except Exception as e:
        st.error(f"Error in getting URL contents: {str(e)}")
    return results

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
        st.title("Advanced Search App")

        st.sidebar.header("Search Parameters")
        company_domain = st.sidebar.text_input("Enter search term")
        num_results = st.sidebar.slider("Number of results", 5, 50, 15)
        start_date = st.sidebar.date_input("Start date", datetime.now() - timedelta(days=30))
        end_date = st.sidebar.date_input("End date", datetime.now())

        exa_search_type = st.sidebar.selectbox("Exa Search Type", ["keyword", "neural"])

        newsapi_sources = st.sidebar.text_input("NewsAPI Sources (comma-separated)", "")
        newsapi_language = st.sidebar.selectbox("NewsAPI Language", ["en", "de", "fr", "es"])
        newsapi_sort_by = st.sidebar.selectbox("NewsAPI Sort By", ["relevancy", "popularity", "publishedAt"])

        search_button = st.sidebar.button("Search")

        if search_button and company_domain:
            with st.spinner("Searching..."):
                formatted_start_date = start_date.strftime("%Y-%m-%d")
                formatted_end_date = end_date.strftime("%Y-%m-%d")
                exa_start_date = f"{formatted_start_date}T00:00:00.000Z"
                exa_end_date = f"{formatted_end_date}T23:59:59.999Z"

                serper_results = serper_search(company_domain, num_results, formatted_start_date, formatted_end_date)
                exa_results = exa_search(company_domain, exa_search_type, num_results, exa_start_date, exa_end_date)
                newsapi_results = newsapi_search(company_domain, newsapi_sources, formatted_start_date, formatted_end_date, num_results, newsapi_language, newsapi_sort_by)

                col1, col2, col3 = st.columns(3)

                urls = []

                with col1:
                    st.subheader("Serper Results")
                    if isinstance(serper_results, dict) and "organic" in serper_results:
                        for result in serper_results["organic"][:num_results]:
                            st.write(f"**{result['title']}**")
                            st.write(result['snippet'])
                            st.write(f"[Link]({result['link']})")
                            st.write("---")
                            urls.append(result['link'])
                    else:
                        st.warning("No organic results found in Serper search.")

                with col2:
                    st.subheader("Exa Search Results")
                    if isinstance(exa_results, dict) and "results" in exa_results:
                        for result in exa_results["results"][:num_results]:
                            st.write(f"**{result.get('title', 'No title')}**")
                            if "highlights" in result and result["highlights"]:
                                st.write("Highlights:")
                                for highlight in result["highlights"]:
                                    clean_highlight = highlight.replace("<em>", "**").replace("</em>", "**")
                                    st.markdown(f"- {clean_highlight}")
                            else:
                                st.write(result.get('text', 'No description available')[:300] + "...")
                            st.write(f"[Link]({result.get('url', '#')})")
                            st.write("---")
                            urls.append(result.get('url', '#'))
                    else:
                        st.warning("No results found in Exa search.")
                        st.write("Exa response:", exa_results)

                with col3:
                    st.subheader("NewsAPI Results")
                    if isinstance(newsapi_results, dict) and "articles" in newsapi_results:
                        st.write(f"Total results: {min(newsapi_results['totalResults'], num_results)}")
                        for article in newsapi_results["articles"][:num_results]:
                            st.write(f"**{article['title']}**")
                            st.write(article['description'])
                            st.write(f"[Link]({article['url']})")
                            st.write("---")
                            urls.append(article['url'])
                    else:
                        st.warning("No results found in NewsAPI search.")
                        st.write("NewsAPI response:", newsapi_results)

                st.subheader("URL Contents and Highlights")
                with st.spinner("Fetching URL contents..."):
                    url_contents = get_url_contents(urls)
                    if url_contents:
                        for url, content in url_contents.items():
                            st.write(f"**URL: {url}**")
                            st.write(f"**Title:** {content['title']}")
                            st.write("**Text:**")
                            st.write(content['text'])
                            if content['highlights']:
                                st.write("**Highlights:**")
                                for highlight in content['highlights']:
                                    st.markdown(f"- {highlight}")
                            st.write("---")
                    else:
                        st.warning("No URL contents could be fetched.")

                # Debug information
                st.subheader("Debug Information")
                st.write("URLs processed:", urls)
                st.write("URL contents:", url_contents)

if __name__ == "__main__":
    main()
