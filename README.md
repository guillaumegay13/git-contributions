# GitHub Line Contribution Analyzer

A Streamlit application that analyzes GitHub users' line contributions across their repositories.

## Features
- OAuth authentication with GitHub
- Detailed analysis of line additions and deletions
- Visual representation of contributions using charts
- Support for multiple email addresses
- Repository-specific statistics

## Setup
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env`:
   ```
   GITHUB_CLIENT_ID_DEV=your_client_id
   GITHUB_CLIENT_SECRET_DEV=your_client_secret
   IS_PROD=false
   ```
4. Run the application:
   ```bash
   streamlit run src/main.py
   ```

## Requirements
See `requirements.txt` for a full list of dependencies. 