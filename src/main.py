import streamlit as st
import pandas as pd
from github_client import GitHubClient
from visualization import create_metrics_display, create_contribution_charts
from auth import init_github_oauth, handle_oauth_callback, logout

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
                        else:
                            st.warning("No contributions found in the analyzed repositories.")
                        
                    except Exception as e:
                        st.error(f"Error analyzing contributions: {str(e)}")

if __name__ == "__main__":
    main()