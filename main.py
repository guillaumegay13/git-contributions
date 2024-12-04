import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def fetch_github_contributions(username):
    """Fetch repository contributions for a GitHub user."""
    try:
        # Fetch user's repositories
        repos_url = f"https://api.github.com/users/{username}/repos"
        repos_response = requests.get(repos_url, params={"per_page": 100})
        repos_response.raise_for_status()
        repos = repos_response.json()

        # Collect contribution data
        contributions = []
        for repo in repos:
            if not repo['fork']:
                try:
                    # Fetch contributors for each repository
                    contributors_url = f"https://api.github.com/repos/{username}/{repo['name']}/contributors"
                    contributors_response = requests.get(contributors_url)
                    contributors_response.raise_for_status()
                    contributors = contributors_response.json()

                    # Find the specific user's contributions
                    user_contrib = next(
                        (contrib for contrib in contributors 
                         if contrib['login'].lower() == username.lower()), 
                        None
                    )

                    if user_contrib:
                        contributions.append({
                            'repository': repo['name'],
                            'added_lines': user_contrib.get('additions', 0),
                            'deleted_lines': user_contrib.get('deletions', 0),
                            'total_lines': user_contrib.get('additions', 0) - user_contrib.get('deletions', 0)
                        })
                except Exception as repo_error:
                    st.warning(f"Could not fetch contributions for {repo['name']}: {repo_error}")

        return contributions

    except requests.RequestException as e:
        st.error(f"Error fetching GitHub data: {e}")
        return []

def main():
    st.set_page_config(
        page_title="GitHub Line Contribution Analyzer",
        page_icon=":computer:",
        layout="wide"
    )

    st.title("🐍 GitHub Line Contribution Analyzer")
    
    # User input
    username = st.text_input("Enter GitHub Username", placeholder="github_username")
    
    if st.button("Analyze Contributions"):
        if username:
            with st.spinner('Fetching GitHub contributions...'):
                contributions = fetch_github_contributions(username)
            
            if contributions:
                # Convert to DataFrame
                df = pd.DataFrame(contributions)
                
                # Total Statistics
                total_added = df['added_lines'].sum()
                total_deleted = df['deleted_lines'].sum()
                total_net = df['total_lines'].sum()
                
                # Display total stats
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Added Lines", f"{total_added:,}")
                col2.metric("Total Deleted Lines", f"{total_deleted:,}")
                col3.metric("Net Lines", f"{total_net:,}")
                
                # Visualization Tabs
                tab1, tab2 = st.tabs(["Bar Chart", "Line Chart"])
                
                with tab1:
                    # Bar Chart of Contributions by Repository
                    fig_bar = px.bar(
                        df, 
                        x='repository', 
                        y=['added_lines', 'deleted_lines'], 
                        title='Contributions by Repository',
                        labels={'value': 'Lines of Code', 'variable': 'Type'},
                        height=500
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with tab2:
                    # Line Chart of Contributions
                    fig_line = go.Figure()
                    fig_line.add_trace(go.Scatter(
                        x=df['repository'], 
                        y=df['added_lines'], 
                        mode='lines+markers', 
                        name='Added Lines'
                    ))
                    fig_line.add_trace(go.Scatter(
                        x=df['repository'], 
                        y=df['deleted_lines'], 
                        mode='lines+markers', 
                        name='Deleted Lines'
                    ))
                    fig_line.update_layout(
                        title='Line Contributions Over Repositories',
                        xaxis_title='Repositories',
                        yaxis_title='Lines of Code',
                        height=500
                    )
                    st.plotly_chart(fig_line, use_container_width=True)
                
                # Detailed Repository Table
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No contributions found or error fetching data.")

if __name__ == "__main__":
    main()