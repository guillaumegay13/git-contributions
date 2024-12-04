import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

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

def create_social_share_image(df: pd.DataFrame, username: str):
    # Create a figure with subplots
    fig = go.Figure()
    
    # Add main bar chart
    fig.add_trace(go.Bar(
        name='Added Lines',
        x=df['repository'],
        y=df['added_lines'],
        marker_color='#28a745'
    ))
    
    fig.add_trace(go.Bar(
        name='Deleted Lines',
        x=df['repository'],
        y=df['deleted_lines'],
        marker_color='#dc3545'
    ))
    
    # Update layout with GitHub-style theme
    fig.update_layout(
        title=f"@{username}'s GitHub Contributions",
        template='plotly_dark',
        showlegend=True,
        barmode='group',
        plot_bgcolor='#0d1117',
        paper_bgcolor='#0d1117',
        font=dict(color='#c9d1d9'),
        height=600,
        width=1200,
        margin=dict(t=100, b=100),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#21262d'),
    )
    
    # Add total stats as annotations
    total_added = df['added_lines'].sum()
    total_deleted = df['deleted_lines'].sum()
    total_net = total_added - total_deleted
    
    fig.add_annotation(
        text=f"Total Added: {total_added:,} | Total Deleted: {total_deleted:,} | Net Change: {total_net:,}",
        xref="paper", yref="paper",
        x=0.5, y=1.1,
        showarrow=False,
        font=dict(size=14, color='#c9d1d9')
    )
    
    return fig