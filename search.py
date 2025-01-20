import streamlit as st
import undetected_chromedriver as uc
import time
import random
from datetime import datetime
import shutil
import os

def get_chrome_binary_path():
    # Common locations for Chrome
    paths = [
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        "/usr/bin/google-chrome",  # Linux
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"  # macOS
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    # Check system PATH
    chrome_path = shutil.which("google-chrome") or shutil.which("chrome")
    if chrome_path:
        return chrome_path
    # Ask user for custom path
    custom_path = input("Chrome executable not found. Please provide the path manually: ")
    if os.path.exists(custom_path):
        return custom_path
    raise FileNotFoundError("Invalid Chrome path provided.")

# Use the detected or user-provided path
options = uc.ChromeOptions()
options.binary_location = get_chrome_binary_path()
options.add_argument('--headless')
driver = uc.Chrome(options=options)



def initialize_session_state():
    if 'is_paused' not in st.session_state:
        st.session_state.is_paused = False
    if 'driver' not in st.session_state:
        st.session_state.driver = None
    if 'search_running' not in st.session_state:
        st.session_state.search_running = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    if 'found_pages' not in st.session_state:
        st.session_state.found_pages = []
    if 'current_url' not in st.session_state:
        st.session_state.current_url = None

def reset_session():
    st.session_state.is_paused = False
    st.session_state.search_running = False
    st.session_state.current_page = 1
    st.session_state.found_pages = []
    st.session_state.current_url = None
    if st.session_state.driver:
        st.session_state.driver.quit()
        st.session_state.driver = None

def run_search(search_term, target_name, max_pages, progress_bar, status_text):
    try:
        # Initialize driver if not exists
        if not st.session_state.driver:
            options = uc.ChromeOptions()
            options.add_argument('--disable-blink-features=AutomationControlled')
            st.session_state.driver = uc.Chrome(options=options)
            # Visit homepage first
            status_text.text("Visiting Fiverr homepage...")
            st.session_state.driver.get("https://www.fiverr.com")
            time.sleep(10)

        # Start/Resume search from current page
        while st.session_state.current_page <= max_pages:
            if not st.session_state.search_running:
                break

            if st.session_state.is_paused:
                status_text.text("⏸️ Search paused. Click Resume to continue...")
                time.sleep(1)
                continue

            # Update progress
            progress = st.session_state.current_page / max_pages
            progress_bar.progress(progress)
            status_text.text(f"Checking page {st.session_state.current_page} of {max_pages}...")
            
            # Only load new URL if we're not resuming from a pause or it's a new page
            url = f"https://www.fiverr.com/search/gigs?query={search_term}&page={st.session_state.current_page}"
            if st.session_state.current_url != url:
                st.session_state.driver.get(url)
                st.session_state.current_url = url
            
            # Wait and scroll
            time.sleep(5)
            for _ in range(3):
                st.session_state.driver.execute_script(f"window.scrollTo(0, {random.randint(300, 700)});")
                time.sleep(1)
            time.sleep(4)
            
            # Check for target name
            if target_name.lower() in st.session_state.driver.page_source.lower():
                st.session_state.found_pages.append(st.session_state.current_page)
                st.success(f"Found '{target_name}' on page {st.session_state.current_page}")
            
            st.session_state.current_page += 1

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        reset_session()

def main():
    st.title("Fiverr Search Tool 🔍")
    st.write("This tool helps you find specific names in Fiverr search results. By Poegod")
    
    # Initialize session state
    initialize_session_state()
    
    # Create input form
    with st.form("search_form"):
        search_term = st.text_input("Enter search term (e.g., 'website design')")
        target_name = st.text_input("Enter name to find")
        max_pages = st.number_input("Number of pages to check", min_value=1, max_value=50, value=20)
        
        # Submit button
        submitted = st.form_submit_button("Start Search")
    
    # Create containers for progress and results
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Control buttons container - Placed before run_search
    control_col1, control_col2 = st.columns([1, 4])
    
    # Handle search start
    if submitted and search_term and target_name:
        reset_session()
        st.session_state.search_running = True
    
    # Show controls if search is running
    if st.session_state.search_running:
        with control_col1:
            # Toggle button with dynamic text
            button_label = "▶️ Resume" if st.session_state.is_paused else "⏸️ Pause"
            if st.button(button_label, key="toggle_button"):
                st.session_state.is_paused = not st.session_state.is_paused
                st.rerun()
        
        with control_col2:
            st.info("Use the Pause button if you need to solve a CAPTCHA or take any other action.")
    
    # Results container
    results_container = st.container()
    
    # Run search if active
    if st.session_state.search_running:
        run_search(search_term, target_name, max_pages, progress_bar, status_text)
        
        # Show results when search is complete
        if st.session_state.current_page > max_pages:
            with results_container:
                st.markdown("### Search Results")
                if st.session_state.found_pages:
                    st.success(f"Found '{target_name}' on pages: {', '.join(map(str, st.session_state.found_pages))}")
                else:
                    st.info(f"Did not find '{target_name}' on any page")
                
                # Display statistics
                st.markdown("### Search Statistics")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Pages Checked", max_pages)
                with col2:
                    st.metric("Matches Found", len(st.session_state.found_pages))
            
            # Reset session after completing
            reset_session()

if __name__ == "__main__":
    main()
