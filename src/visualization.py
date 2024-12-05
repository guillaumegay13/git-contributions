import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
import os

def create_metrics_display(df: pd.DataFrame):
    total_added = df['added_lines'].sum()
    total_deleted = df['deleted_lines'].sum()
    total_net = df['total_lines'].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Added Lines", f"{total_added:,}")
    col2.metric("Total Deleted Lines", f"{total_deleted:,}")
    col3.metric("Net Lines", f"{total_net:,}")

def create_contribution_charts(df: pd.DataFrame):
    # Bar Chart
    fig_bar = px.bar(
        df,
        x='repository',
        y=['added_lines', 'deleted_lines'],
        title='Contributions by Repository',
        labels={'value': 'Lines of Code', 'variable': 'Type'},
        height=500,
        color_discrete_map={
            'added_lines': '#28a745',
            'deleted_lines': '#dc3545'
        }
    )
    
    # Line Chart
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=df['repository'],
        y=df['added_lines'],
        mode='lines+markers',
        name='Added Lines',
        line=dict(color='#28a745')
    ))
    fig_line.add_trace(go.Scatter(
        x=df['repository'],
        y=df['deleted_lines'],
        mode='lines+markers',
        name='Deleted Lines',
        line=dict(color='#dc3545')
    ))
    fig_line.update_layout(
        title='Line Contributions Over Repositories',
        xaxis_title='Repositories',
        yaxis_title='Lines of Code',
        height=500
    )
    
    return fig_bar, fig_line 

def create_social_share_image(username: str, added: int, deleted: int, net: int, verification_hash: str) -> str:
    """
    Creates a social media preview image with user stats.
    Returns the path to the generated image.
    """
    # Create figure
    plt.figure(figsize=(12, 6))
    plt.style.use('dark_background')
    
    # Add text
    plt.text(0.5, 0.8, f"GitHub Contributions by @{username}", ha='center', va='center', fontsize=24)
    plt.text(0.5, 0.6, f"Added: {added:,} lines", ha='center', va='center', fontsize=20, color='#00ff00')
    plt.text(0.5, 0.4, f"Deleted: {deleted:,} lines", ha='center', va='center', fontsize=20, color='#ff0000')
    plt.text(0.5, 0.2, f"Net Change: {net:,} lines", ha='center', va='center', fontsize=20, color='#ffffff')
    plt.text(0.5, 0.1, f"Verification: #{verification_hash}", ha='center', va='center', fontsize=16, color='#888888')
    
    # Remove axes
    plt.axis('off')
    
    # Save to temporary file
    os.makedirs('temp', exist_ok=True)
    image_path = f'temp/share_{username}.png'
    plt.savefig(image_path, bbox_inches='tight', facecolor='#0D1117')
    plt.close()
    
    return image_path