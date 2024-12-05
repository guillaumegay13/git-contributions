from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from requests_oauthlib import OAuth2Session
import os
import requests

# Use Streamlit secrets instead of environment variables
IS_PROD = st.secrets.get('IS_PROD', False)

# Use different client IDs and secrets for dev/prod
GITHUB_CLIENT_ID = st.secrets['GITHUB_CLIENT_ID_PROD'] if IS_PROD else st.secrets['GITHUB_CLIENT_ID_DEV']
GITHUB_CLIENT_SECRET = st.secrets['GITHUB_CLIENT_SECRET_PROD'] if IS_PROD else st.secrets['GITHUB_CLIENT_SECRET_DEV']

if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
    raise ValueError("GitHub OAuth credentials not found in Streamlit secrets")

AUTHORIZATION_BASE_URL = 'https://github.com/login/oauth/authorize'
TOKEN_URL = 'https://github.com/login/oauth/access_token'
SCOPE = ['public_repo', 'read:user', 'user:email']
CALLBACK_URL = st.secrets.get('CALLBACK_URL', 'http://localhost:8501')

# Only disable HTTPS requirement in development
if not IS_PROD:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

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
    st.markdown("""
        <div style="display: flex; justify-content: center; margin: 2em 0;">
            <a href="{}" target="_top" style="
                text-decoration: none;
                background-color: #24292e;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: 600;
                display: inline-flex;
                align-items: center;
                transition: background-color 0.2s;
                box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
                ">
                <svg style="margin-right: 8px;" height="20" width="20" viewBox="0 0 16 16" fill="white">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
                Login with GitHub
            </a>
        </div>
    """.format(authorization_url), unsafe_allow_html=True)
    
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