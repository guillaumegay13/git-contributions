import streamlit as st
import pandas as pd
from github_client import GitHubClient
from visualization import create_metrics_display, create_contribution_charts, create_social_share_image
from auth import init_github_oauth, handle_oauth_callback, logout
import urllib.parse
import os
import hashlib

def main():
    st.set_page_config(
        page_title="GitHub Line Contribution Analyzer",
        page_icon="🐙",
        layout="wide"
    )

    st.title("🐙 GitHub Line Contribution Analyzer")
    st.markdown("""
    Analyze line contributions across all repositories for any GitHub user.
    This tool uses git log to provide accurate statistics similar to local git analysis.
    """)
    
    # Handle OAuth flow
    handle_oauth_callback()
    token = init_github_oauth()
    
    # Only show the rest of the UI if authenticated
    if token:
        # Show user info and logout button in sidebar
        user = st.session_state.get('github_user')
        if user:
            with st.sidebar:
                st.markdown(f"""
                ### 👤 Logged in as
                **{user['name'] or user['login']}** (@{user['login']})
                
                *Using {len(user['emails'])} verified email(s)*
                """)
                if st.button("🚪 Logout", type="primary"):
                    logout()
        
        # Pre-fill the form
        username = st.text_input(
            "GitHub Username",
            value=user['login'],
            disabled=True
        )
        
        emails = st.text_input(
            "Git Email Addresses",
            value=", ".join(user['emails']),
            help="These are your verified GitHub email addresses"
        )
        
        if st.button("Analyze Contributions"):
            if username and emails:
                author_emails = [email.strip() for email in emails.split(',')]
                with st.spinner('Fetching GitHub contributions...'):
                    client = GitHubClient(token['access_token'])  # Use the OAuth token
                    
                    try:
                        # Fetch repositories
                        repos = client.get_user_repos(username)
                        
                        if not repos:
                            st.warning("No repositories found for this user.")
                            return
                        
                        # Progress tracking setup
                        st.write("## Analysis Progress")
                        progress_placeholder = st.empty()
                        log_placeholder = st.empty()
                        
                        # Create a container for progress information
                        with st.container():
                            progress_bar = st.progress(0.0)
                            status_text = st.empty()
                        
                        # Analyze each repository
                        total_repos = len([repo for repo in repos if not repo['fork']])
                        processed_repos = 0
                        contributions = []
                        
                        for repo in repos:
                            if not repo['fork']:
                                # Update progress
                                current_progress = float(processed_repos) / float(total_repos)
                                progress_bar.progress(current_progress)
                                
                                # Update status
                                progress_placeholder.markdown(
                                    f"**Processing: {processed_repos+1}/{total_repos} repositories ({int(current_progress * 100)}%)**"
                                )
                                
                                # Add log message
                                log_placeholder.markdown(f"🔄 Analyzing {repo['name']}...")
                                
                                # Process repository
                                contribution = client.analyze_repo_contributions(
                                    username,
                                    repo['name'],
                                    repo['clone_url'],
                                    author_emails
                                )
                                if contribution['added_lines'] > 0 or contribution['deleted_lines'] > 0:
                                    contributions.append(contribution)
                                
                                # Update log with completion
                                log_placeholder.markdown(f"✅ Completed {repo['name']}")
                                processed_repos += 1
                                # Clear log for next repository
                                log_placeholder.empty()
                        
                        # Complete the progress bar
                        progress_bar.progress(1.0)
                        progress_placeholder.markdown("**✨ Analysis Complete!**")
                        
                        # Add spacing after progress section
                        st.write("---")
                        
                        if contributions:
                            # Create DataFrame
                            df = pd.DataFrame(contributions)
                            
                            # Display visualizations
                            create_metrics_display(df)
                            
                            # Visualization Tabs
                            tab1, tab2 = st.tabs(["Bar Chart", "Line Chart"])
                            fig_bar, fig_line = create_contribution_charts(df)
                            
                            with tab1:
                                st.plotly_chart(fig_bar, use_container_width=True)
                            
                            with tab2:
                                st.plotly_chart(fig_line, use_container_width=True)
                            
                            # Detailed Repository Table
                            st.dataframe(
                                df.sort_values('total_lines', ascending=False),
                                use_container_width=True
                            )
                            
                            # Add share functionality
                            create_share_section(df, username)
                        else:
                            st.warning("No contributions found in the analyzed repositories.")
                        
                    except Exception as e:
                        st.error(f"Error analyzing contributions: {str(e)}")

def create_share_section(df: pd.DataFrame, username: str):
    st.write("---")
    st.subheader("📤 Share Your Stats")
    
    # Calculate stats
    total_added = df['added_lines'].sum()
    total_deleted = df['deleted_lines'].sum()
    total_net = total_added - total_deleted
    
    # Create a verification hash (first 8 chars) using repository names and stats
    repos_string = "-".join(sorted(df['repository'].tolist()))
    verification_string = f"{username}-{total_added}-{total_deleted}-{repos_string}"
    verification_hash = hashlib.sha256(verification_string.encode()).hexdigest()[:8]
    
    # Create tweet text with verification
    tweet_text = (
        f"🚀 My GitHub Contributions Analysis:\n\n"
        f"📈 Added: {total_added:,} lines\n"
        f"📉 Deleted: {total_deleted:,} lines\n"
        f"✨ Net Change: {total_net:,} lines\n\n"
        f"🔍 Verify: #{verification_hash}\n"
        f"🔗 Try it: https://github.com/guillaumegay13/git-contributions"
    )
    
    # Create Twitter share link
    tweet_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(tweet_text)}"
    
    # Show preview and share button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.text_area("Tweet Preview", tweet_text, height=150)
    with col2:
        st.markdown(f"""
        <a href="{tweet_url}" target="_blank">
            <img src="https://img.shields.io/badge/Share%20on-X-black?logo=x&style=for-the-badge" alt="Share on X">
        </a>
        """, unsafe_allow_html=True)

def verify_contribution_hash(username: str, added: int, deleted: int, repos: str, hash_to_verify: str) -> bool:
    """Verify a contribution hash from a tweet."""
    # Reconstruct the verification string
    verification_string = f"{username}-{added}-{deleted}-{repos}"
    # Generate hash and compare
    computed_hash = hashlib.sha256(verification_string.encode()).hexdigest()[:8]
    return computed_hash == hash_to_verify

def create_verification_section():
    st.write("---")
    st.subheader("🔍 Verify Shared Stats")
    
    with st.expander("Verify someone's shared stats"):
        username = st.text_input("GitHub Username", key="verify_username")
        added = st.number_input("Added Lines", min_value=0, key="verify_added")
        deleted = st.number_input("Deleted Lines", min_value=0, key="verify_deleted")
        repos = st.text_input("Repository Names (comma-separated)", key="verify_repos")
        hash_to_verify = st.text_input("Verification Hash (without #)", key="verify_hash")
        
        if st.button("Verify"):
            if all([username, hash_to_verify, repos]):
                # Convert repos string to sorted dash-separated format
                repos_list = [r.strip() for r in repos.split(",")]
                repos_string = "-".join(sorted(repos_list))
                
                is_valid = verify_contribution_hash(
                    username=username,
                    added=added,
                    deleted=deleted,
                    repos=repos_string,
                    hash_to_verify=hash_to_verify
                )
                
                if is_valid:
                    st.success("✅ Verification Successful! These stats are authentic.")
                else:
                    st.error("❌ Verification Failed! These stats may have been modified.")
                
                # Show debug information
                with st.expander("Show Verification Details"):
                    st.code(f"""
Verification Process:
1. Input String: {username}-{added}-{deleted}-{repos_string}
2. Generated Hash: {hashlib.sha256(f"{username}-{added}-{deleted}-{repos_string}".encode()).hexdigest()[:8]}
3. Provided Hash: {hash_to_verify}
                    """)

if __name__ == "__main__":
    main()