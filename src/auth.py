from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from requests_oauthlib import OAuth2Session
import os
import requests

# Enable non-HTTPS for development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Debug print to verify environment variables
print("Environment variables:")
print(f"IS_PROD: {os.getenv('IS_PROD')}")
print(f"GITHUB_CLIENT_ID_DEV: {os.getenv('GITHUB_CLIENT_ID_DEV')}")

# Get the current environment
IS_PROD = os.getenv('IS_PROD', 'false').lower() == 'true'

# Use different client IDs and secrets for dev/prod
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID_PROD' if IS_PROD else 'GITHUB_CLIENT_ID_DEV')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET_PROD' if IS_PROD else 'GITHUB_CLIENT_SECRET_DEV')

if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
    raise ValueError("GitHub OAuth credentials not found in environment variables")

AUTHORIZATION_BASE_URL = 'https://github.com/login/oauth/authorize'
TOKEN_URL = 'https://github.com/login/oauth/access_token'
SCOPE = ['public_repo', 'read:user', 'user:email']
CALLBACK_URL = 'http://localhost:8501'

# Initialize session state at module level
def init_session_state():
    st.session_state.setdefault('oauth_token', None)
    st.session_state.setdefault('oauth_state', None)
    st.session_state.setdefault('github_user', None)

def init_github_oauth():
    init_session_state()
    
    # Check if already authenticated
    if st.session_state.oauth_token is not None:
        return st.session_state.oauth_token
    
    # Create OAuth session
    github = OAuth2Session(
        GITHUB_CLIENT_ID, 
        scope=SCOPE,
        redirect_uri=CALLBACK_URL
    )
    
    # Get authorization URL
    authorization_url, state = github.authorization_url(AUTHORIZATION_BASE_URL)
    
    # Store state
    st.session_state.oauth_state = state
    
    # Show login button
    st.markdown(f"""
    ### GitHub Authentication Required
    Please click the button below to authenticate with GitHub:
    
    <a href="{authorization_url}" target="_self"><img src="https://img.shields.io/badge/Login%20with-GitHub-black?logo=github" alt="Login with GitHub"></a>
    """, unsafe_allow_html=True)
    
    return None

def get_user_info(token):
    try:
        headers = {
            'Authorization': f'Bearer {token["access_token"]}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Get user profile
        response = requests.get('https://api.github.com/user', headers=headers)
        response.raise_for_status()
        user_data = response.json()
        
        # Get user emails
        emails_response = requests.get('https://api.github.com/user/emails', headers=headers)
        emails_response.raise_for_status()
        emails = [email['email'] for email in emails_response.json() if email['verified']]
        
        return {
            'login': user_data['login'],
            'name': user_data.get('name', ''),
            'emails': emails
        }
    except Exception as e:
        st.error(f"Failed to retrieve user information: {str(e)}")
        return None

def handle_oauth_callback():
    init_session_state()
    
    if 'code' in st.query_params and st.session_state.oauth_token is None:
        try:
            github = OAuth2Session(
                GITHUB_CLIENT_ID,
                state=st.session_state.oauth_state,
                redirect_uri=CALLBACK_URL
            )
            
            full_url = f"{CALLBACK_URL}?code={st.query_params['code']}"
            if 'state' in st.query_params:
                full_url += f"&state={st.query_params['state']}"
            
            token = github.fetch_token(
                TOKEN_URL,
                client_secret=GITHUB_CLIENT_SECRET,
                authorization_response=full_url
            )
            
            # Store token and user info
            st.session_state.oauth_token = token
            st.session_state.github_user = get_user_info(token)
            st.query_params.clear()
            st.rerun()
            
        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            # Clear everything on error
            st.session_state.oauth_token = None
            st.session_state.oauth_state = None
            st.query_params.clear()

def logout():
    # Clear all session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    # Rerun the app to show the login screen
    st.rerun()