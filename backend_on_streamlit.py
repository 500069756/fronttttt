"""Streamlit wrapper to host the FastAPI backend on Streamlit Cloud.

This script allows you to deploy the recommendation engine to Streamlit Cloud.
It runs the FastAPI server in the background so the Next.js frontend (on Vercel)
can communicate with it.
"""
import streamlit as st
import multiprocessing
import uvicorn
import time
import requests
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.phase3_api.main import app
from config import API_PORT, API_HOST

st.set_page_config(page_title="AI Recommender Backend", page_icon="⚙️")

def run_api():
    """Run the FastAPI server."""
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

def main():
    st.title("🍽️ AI Restaurant Recommender Backend")
    st.info("This Streamlit app hosts the FastAPI recommendation engine in the background.")

    # Status monitoring
    status_placeholder = st.empty()
    
    # Initialize session state for process management
    if 'api_started' not in st.session_state:
        st.session_state.api_started = False

    if not st.session_state.api_started:
        status_placeholder.warning("Initializing Backend...")
        
        # Start uvicorn in a separate process
        # Note: In Streamlit Cloud, we use port 8001 for the internal API 
        # and Streamlit itself runs on the default port.
        p = multiprocessing.Process(target=run_api)
        p.start()
        
        st.session_state.api_started = True
        st.session_state.api_pid = p.pid
        time.sleep(5) # Give it time to start

    # Check health
    try:
        response = requests.get("http://localhost:8001/api/v1/health")
        if response.status_code == 200:
            status_placeholder.success("✅ Backend API is active and healthy on port 8001")
            
            st.subheader("API Status Details")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Status", "Online")
                st.metric("Port", "8001")
            with col2:
                st.metric("Version", "1.0.0")
                st.metric("PID", st.session_state.api_pid)
                
            st.divider()
            st.markdown("""
            ### Deployment Instructions for Frontend
            When deploying your Next.js frontend to **Vercel**, set the following environment variable:
            - `NEXT_PUBLIC_API_BASE_URL`: The URL of **this** Streamlit app + `/api/v1`
            
            *Note: Ensure your Streamlit app is public so Vercel can access the port.*
            """)
        else:
            status_placeholder.error(f"❌ Backend failed health check (Status: {response.status_code})")
    except Exception as e:
        status_placeholder.error(f"❌ Backend is unreachable: {e}")

    if st.button("Re-init Backend"):
        st.session_state.api_started = False
        st.rerun()

if __name__ == "__main__":
    main()
