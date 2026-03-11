import streamlit as st
import feedparser
import urllib.parse
from datetime import datetime, timedelta
import time
import google.generativeai as genai

# --- Configuration ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

# Using the active, correct model
model = genai.GenerativeModel('gemini-2.5-flash')

# --- Page Setup ---
st.set_page_config(page_title="Professional Cocoa Terminal Tracker", layout="wide")
st.title("🍫 Professional Cocoa Terminal & Demand Tracker")
st.markdown("Direct RSS aggregation with **Lightning-Fast Batch AI Sentiment Analysis**.")

# --- RSS Feed URLs ---
macro_search = 'cocoa AND ("Ivory Coast" OR CCC OR "mid-crop" OR terminal OR futures OR export OR Reuters)'
demand_search = '(Lindt OR Hershey OR "Barry Callebaut" OR "Guan Chong" OR Cargill) AND (profit OR margin OR cocoa OR grindings)'

MACRO_RSS_URL = f"https://news.google.com/rss/search?q={urllib.parse.quote(macro_search)}&hl=en-US&gl=US&ceid=US:en"
DEMAND_RSS_URL = f"https://news.google.com/rss/search?q={urllib.parse.quote(demand_search)}&hl=en-US&gl=US&ceid=US:en"

# --- AI Batch Sentiment Analyst ---
@st.cache_data(ttl=86400) 
def analyze_batch_sentiments(headlines_tuple):
    # Failsafe for the API Key
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
         return ["🤖 (API Key Needed)"] * len(headlines_tuple)
    
    if not headlines_tuple:
        return []
        
    # Create a numbered list of all headlines to send to the AI
    numbered_list = "\n".join([f"{i+1}. {headline}" for i, headline in enumerate(headlines_tuple)])
    
    prompt = f"""
    You are a professional physical cocoa trader. Read this numbered list of news headlines and determine the likely impact of EACH on ICE cocoa terminal futures prices.
    - Reply ONLY with a numbered list matching the input, using "Bullish", "Bearish", or "Neutral".
    - Rule 1: Supply shortages, port delays, disease, or heavy rains in West Africa are Bullish.
    - Rule 2: Strong grinder margins, high demand, or high processing numbers are Bullish.
    - Rule 3: Bumper crops, perfect weather, or collapsing chocolate demand are Bearish.
    
    Headlines:
    {numbered_list}
    
    Output format must be exactly like this:
    1. Bullish
    2. Bearish
    3. Neutral
    """
    
    try:
        response = model.generate_content(prompt)
        lines = response.text.strip().split('\n')
        
        sentiments = []
        for line in lines:
            lower_line = line.lower()
            if "bullish" in lower_line: sentiments.append("🐂 Bullish")
            elif "bearish" in lower_line: sentiments.append("🐻 Bearish")
            else: sentiments.append("➖ Neutral")
            
        # Failsafe in case the AI skips a line
        if len(sentiments) < len(headlines_tuple):
            sentiments.extend(["➖ Neutral"] * (len(headlines_tuple) - len(sentiments)))
            
        return sentiments[:len(headlines_tuple)]
        
     except Exception as e:
        error_msg = str(e).lower()
        # If the error is about quotas or limits, show a clean message
        if "quota" in error_msg or "limit" in error_msg or "429" in error_msg:
            return ["⚠️ Limit Hit"] * len(headlines_tuple)
        
        # Otherwise, show the actual error for troubleshooting
        return [f"⚠️ {str(e)}"] * len(headlines_tuple)
        
@st.cache_data(ttl=900) 
def fetch_rss_news(rss_url):
    feed = feedparser.parse(rss_url)
    articles = []
    one_week_ago = datetime.now() - timedelta(days=7)
    
    for entry in feed.entries:
        try:
            if hasattr(entry, 'published_parsed'):
                dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                if dt >= one_week_ago:
                    articles.append({
                        'title': entry.title,
                        'link': entry.link,
                        'publishedAt': dt.strftime("%b %d, %Y - %H:%M"),
                        'source': entry.source.title if hasattr(entry, 'source') else 'News Source',
                        'dt_obj': dt
                    })
        except Exception:
            continue
            
    articles.sort(key=lambda x: x['dt_obj'], reverse=True)
    return articles[:10] # Bumped back up to 10 articles per column since we fixed the limit

# --- Dashboard Layout ---
col1, col2 = st.columns(2)

with col1:
    st.header("🌍 Macro, CCC & Terminal News")
    supply_news = fetch_rss_news(MACRO_RSS_URL)
    
    if supply_news:
        # Extract just the titles, turn into a tuple for the cache, and grade them all at once
        headlines = tuple([article['title'] for article in supply_news])
        sentiments = analyze_batch_sentiments(headlines)
        
        # Zip pairs the article with its corresponding sentiment score
        for article, sentiment in zip(supply_news, sentiments):
            with st.expander(f"{sentiment} | **{article['title']}** ({article['publishedAt']})"):
                st.markdown(f"**Source:** {article['source']}")
                st.markdown(f"[Read full article]({article['link']})")
    else:
        st.write("No supply news found in the last 7 days.")

with col2:
    st.header("🏭 Chocolatiers & Grinders")
    demand_news = fetch_rss_news(DEMAND_RSS_URL)
    
    if demand_news:
        headlines = tuple([article['title'] for article in demand_news])
        time.sleep(5) # <-- ADD THIS LINE: Gives Google 3 seconds to breathe
        sentiments = analyze_batch_sentiments(headlines)
        
        for article, sentiment in zip(demand_news, sentiments):
            with st.expander(f"{sentiment} | **{article['title']}** ({article['publishedAt']})"):
                st.markdown(f"**Source:** {article['source']}")
                st.markdown(f"[Read full article]({article['link']})")
    else:

        st.write("No chocolatier news found in the last 7 days.")





