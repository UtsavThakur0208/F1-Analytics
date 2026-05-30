# ============================================================
# STREAMLIT APP: Formula 1 Analytics Dashboard
# ============================================================
# This is the main dashboard file. Streamlit runs top-to-bottom
# on every user interaction (slider move, filter change, etc.)
# So we cache data loading to avoid re-reading CSVs every time.
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── PAGE CONFIGURATION ────────────────────────────────────────
# This must be the FIRST Streamlit command in the file.
# It sets the browser tab title, icon, and layout.

st.set_page_config(
    page_title="F1 Analytics Dashboard",
    page_icon="🏎️",
    layout="wide",               # "wide" uses full browser width
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ────────────────────────────────────────────────
# Small CSS injection makes the app feel polished.
# We use st.markdown with unsafe_allow_html=True for this.

st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #E10600;           /* F1 red */
        text-align: center;
        padding: 10px 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border-left: 4px solid #E10600;
    }
    </style>
""", unsafe_allow_html=True)


# ── DATA LOADING ──────────────────────────────────────────────
# @st.cache_data tells Streamlit: "Run this function once, save
# the result. If inputs don't change, reuse cached result."
# Without caching, CSVs would reload on every single interaction,
# making the app feel slow and sluggish.

@st.cache_data
def load_data():
    """Load all processed CSV files."""
    # IMPORTANT: When deployed on Streamlit Cloud, paths must be
    # relative to the repo root, NOT relative to this file.
    # We use try/except to handle both local and deployed paths.
    
  import os

@st.cache_data
def load_data():

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    DATA_DIR = os.path.join(BASE_DIR, "Data", "Processed")

    master = pd.read_csv(
        os.path.join(DATA_DIR, "processedmaster_df.csv")
    )

    driver_stats = pd.read_csv(
        os.path.join(DATA_DIR, "processeddriver_season_stats.csv")
    )

    constructor_stats = pd.read_csv(
        os.path.join(DATA_DIR, "processedconstructor_season_stats.csv")
    )

    pit_agg = pd.read_csv(
        os.path.join(DATA_DIR, "processedpit_agg.csv")
    )

    pit_stops = pd.read_csv(
        os.path.join(DATA_DIR, "processedpit_stops_clean.csv")
    )

    return master, driver_stats, constructor_stats, pit_agg, pit_stops

# Load data (cached after first run)
master, driver_stats, constructor_stats, pit_agg, pit_stops = load_data()
master['is_winner'] = (master['position'] == 1).astype(int)

# ── HEADER ────────────────────────────────────────────────────

st.markdown('<p class="main-header">🏎️ Formula 1 Analytics Dashboard</p>', 
            unsafe_allow_html=True)
st.markdown('<p class="sub-header">Exploring driver performance, constructor dominance, and pit stop strategy</p>', 
            unsafe_allow_html=True)
st.markdown("---")


# ── SIDEBAR FILTERS ───────────────────────────────────────────
# The sidebar is the control panel. Every filter here affects
# what data is shown in the main area.

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/F1.svg/320px-F1.svg.png", 
             width=150)
    
    st.header("🔧 Filters")
    
    # Year range slider
    # master['year'].min() and .max() get the actual range from data
    year_min = int(master['year'].min())
    year_max = int(master['year'].max())
    
    year_range = st.slider(
        "Select Year Range",
        min_value=year_min,
        max_value=year_max,
        value=(2010, year_max),    # default to 2010-present
        step=1
    )
    
    st.markdown("---")
    
    # Constructor multiselect
    all_constructors = sorted(master['constructor_name'].dropna().unique().tolist())
    
    # Default to top constructors for a nice first view
    default_teams = ['Mercedes', 'Red Bull', 'Ferrari', 'McLaren']
    # Only use defaults that actually exist in the data
    valid_defaults = [t for t in default_teams if t in all_constructors]
    
    selected_constructors = st.multiselect(
        "Select Constructors",
        options=all_constructors,
        default=valid_defaults
    )
    
    st.markdown("---")
    st.caption("📊 Data: Ergast F1 API Dataset")
    st.caption("Built with Streamlit + Plotly")


# ── APPLY FILTERS ─────────────────────────────────────────────
# Filter master dataframe based on sidebar selections

filtered = master[
    (master['year'] >= year_range[0]) &
    (master['year'] <= year_range[1])
].copy()

filtered_constr = filtered[
    filtered['constructor_name'].isin(selected_constructors)
] if selected_constructors else filtered


# ── KPI CARDS ─────────────────────────────────────────────────
# Key Performance Indicators at the top give users a quick
# summary before they dig into charts. This is standard in
# professional BI dashboards (Tableau, Power BI do this).

st.subheader("📈 Key Metrics for Selected Period")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    total_races = filtered['raceId'].nunique()
    st.metric(
        label="🏁 Total Races",
        value=f"{total_races:,}"
    )

with kpi2:
    total_drivers = filtered['driver_name'].nunique()
    st.metric(
        label="👤 Unique Drivers",
        value=f"{total_drivers:,}"
    )

with kpi3:
    total_constructors = filtered['constructor_name'].nunique()
    st.metric(
        label="🏭 Constructors",
        value=f"{total_constructors:,}"
    )

with kpi4:
    # Most successful driver in selected period
    top_driver = (
        filtered[filtered['position'] == 1]
        .groupby('driver_name')['position']
        .sum()
        .idxmax()
    )
    st.metric(
        label="🏆 Most Wins",
        value=top_driver
    )

st.markdown("---")


# ── TABS ──────────────────────────────────────────────────────
# st.tabs creates a tabbed interface. Much cleaner than one
# giant scrollable page. Professional dashboards always use
# tabs or pages to organize content.

tab1, tab2, tab3, tab4 = st.tabs([
    "🧑‍💼 Driver Analysis",
    "🏭 Constructor Analysis", 
    "🔄 Positions Gained",
    "⏱️ Pit Stop Analysis"
])


# ════════════════════════════════════════════════════════════════
# TAB 1: DRIVER ANALYSIS
# ════════════════════════════════════════════════════════════════

with tab1:
    st.header("Driver Performance Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # ── Chart: Top Winners ──────────────────────────────
        st.subheader("🏆 Top Race Winners")
        
        top_n = st.slider("Show top N drivers", 5, 20, 10, key="winner_slider")
        
        wins_data = (
            filtered[filtered['position'] == 1]
            .groupby('driver_name')['position']
            .sum()
            .sort_values(ascending=True)
            .tail(top_n)
            .reset_index()
        )
        wins_data.columns = ['Driver', 'Wins']
        
        fig_wins = px.bar(
            wins_data, x='Wins', y='Driver',
            orientation='h',
            color='Wins',
            color_continuous_scale='Reds',
            text='Wins'
        )
        fig_wins.update_layout(
            plot_bgcolor='white',
            height=400,
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        fig_wins.update_traces(textposition='outside')
        st.plotly_chart(fig_wins, use_container_width=True)
    
    with col2:
        # ── Chart: Podium Rate ──────────────────────────────
        st.subheader("🥇 Driver Podium Rate (%)")
        
        podium_data = (
            filtered.groupby('driver_name')
            .agg(
                races  = ('resultId', 'count'),
                podiums = ('position', 'sum')
            )
            .reset_index()
        )
        podium_data = podium_data[podium_data['races'] >= 20]
        podium_data['podium_rate'] = (podium_data['podiums'] / podium_data['races'] * 100).round(1)
        podium_data = podium_data.sort_values('podium_rate', ascending=True).tail(top_n)
        
        fig_podium = px.bar(
            podium_data, x='podium_rate', y='driver_name',
            orientation='h',
            color='podium_rate',
            color_continuous_scale='Oranges',
            text='podium_rate',
            labels={'podium_rate': 'Podium Rate (%)', 'driver_name': 'Driver'}
        )
        fig_podium.update_layout(
            plot_bgcolor='white',
            height=400,
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        fig_podium.update_traces(textposition='outside')
        st.plotly_chart(fig_podium, use_container_width=True)
    
    # ── Points Trend Line Chart ─────────────────────────────
    st.subheader("📈 Season Points Trend")
    
    # Let user pick specific drivers to compare
    all_drivers = sorted(filtered['driver_name'].dropna().unique().tolist())
    
    # Smart default: automatically pick top 5 by wins
    top5_default = (
        filtered[filtered['position'] == 1]
        .groupby('driver_name')['position']
        .sum()
        .nlargest(5)
        .index.tolist()
    )
    # Filter to only include drivers in the valid list
    valid_top5 = [d for d in top5_default if d in all_drivers]
    
    selected_drivers = st.multiselect(
        "Select drivers to compare",
        options=all_drivers,
        default=valid_top5[:5]
    )
    
    if selected_drivers:
        driver_season = driver_stats[
            (driver_stats['driver_name'].isin(selected_drivers)) &
            (driver_stats['year'] >= year_range[0]) &
            (driver_stats['year'] <= year_range[1])
        ]
        
        fig_trend = px.line(
            driver_season,
            x='year',
            y='total_points',
            color='driver_name',
            markers=True,
            title='Season Points by Driver',
            labels={'total_points': 'Points', 'year': 'Year', 'driver_name': 'Driver'}
        )
        fig_trend.update_layout(plot_bgcolor='white', height=400)
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Select at least one driver above to see the trend chart.")


# ════════════════════════════════════════════════════════════════
# TAB 2: CONSTRUCTOR ANALYSIS
# ════════════════════════════════════════════════════════════════

with tab2:
    st.header("Constructor Performance Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Constructor Wins")
        
        constr_wins = (
            filtered[filtered['position'] == 1]
            .groupby('constructor_name')['position']
            .sum()
            .sort_values(ascending=True)
            .tail(12)
            .reset_index()
        )
        constr_wins.columns = ['Constructor', 'Wins']
        
        fig_cw = px.bar(
            constr_wins, x='Wins', y='Constructor',
            orientation='h',
            color='Wins',
            color_continuous_scale='Blues',
            text='Wins'
        )
        fig_cw.update_layout(
            plot_bgcolor='white', height=450,
            coloraxis_showscale=False
        )
        fig_cw.update_traces(textposition='outside')
        st.plotly_chart(fig_cw, use_container_width=True)
    
    with col2:
        st.subheader("⚙️ Constructor DNF Rate (%)")
        
        dnf_data = (
            filtered.groupby('constructor_name')
            .agg(
                total_starts = ('resultId', 'count'),
                total_dnf    = ('position', lambda x: (x == 0).sum())
            )
            .reset_index()
        )
        dnf_data = dnf_data[dnf_data['total_starts'] >= 30]
        dnf_data['dnf_rate'] = (dnf_data['total_dnf'] / dnf_data['total_starts'] * 100).round(1)
        dnf_data = dnf_data.sort_values('dnf_rate').head(12)
        
        fig_dnf = px.bar(
            dnf_data, x='dnf_rate', y='constructor_name',
            orientation='h',
            color='dnf_rate',
            color_continuous_scale='RdYlGn_r',
            text='dnf_rate',
            labels={'dnf_rate': 'DNF Rate (%)', 'constructor_name': 'Constructor'}
        )
        fig_dnf.update_layout(
            plot_bgcolor='white', height=450,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_dnf, use_container_width=True)
    
    # Constructor points race
    st.subheader("📈 Constructor Points Race by Season")
    
    if selected_constructors:
        constr_trend = constructor_stats[
            (constructor_stats['constructor_name'].isin(selected_constructors)) &
            (constructor_stats['year'] >= year_range[0]) &
            (constructor_stats['year'] <= year_range[1])
        ]
        
        fig_ct = px.line(
            constr_trend,
            x='year',
            y='total_points',
            color='constructor_name',
            markers=True,
            labels={'total_points': 'Points', 'constructor_name': 'Team'}
        )
        fig_ct.update_layout(plot_bgcolor='white', height=400)
        st.plotly_chart(fig_ct, use_container_width=True)
    else:
        st.info("Select constructors in the sidebar to compare their points trends.")


# ════════════════════════════════════════════════════════════════
# TAB 3: POSITIONS GAINED
# ════════════════════════════════════════════════════════════════

with tab3:
    st.header("Positions Gained Analysis — Overtaking & Racecraft")
    
    st.markdown("""
    > **What is this?** Positions Gained = Starting Grid − Finishing Position.  
    > A positive number means the driver moved *forward* through the field.  
    > This metric isolates **driver racecraft and overtaking ability** from car performance.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔼 Average Positions Gained Per Race")
        
        min_races = st.slider("Minimum races (for statistical reliability)", 
                               10, 50, 20, key="pg_slider")
        
        pg_data = (
            filtered.groupby('driver_name')
            .agg(
                avg_gained = ('position', 'mean'),
                races      = ('resultId', 'count')
            )
            .reset_index()
        )
        pg_data = pg_data[pg_data['races'] >= min_races]
        pg_data['avg_gained'] = pg_data['avg_gained'].round(2)
        pg_data = pg_data.sort_values('avg_gained', ascending=False).head(20)
        
        fig_pg = px.bar(
            pg_data,
            x='driver_name',
            y='avg_gained',
            color='avg_gained',
            color_continuous_scale='RdYlGn',
            text='avg_gained',
            labels={'avg_gained': 'Avg Positions Gained', 'driver_name': 'Driver'}
        )
        fig_pg.update_layout(
            xaxis_tickangle=-45,
            plot_bgcolor='white',
            height=450,
            coloraxis_showscale=False
        )
        fig_pg.update_traces(textposition='outside')
        st.plotly_chart(fig_pg, use_container_width=True)
    
    with col2:
        st.subheader("🔎 Single Race Highlights")
        
        # Best individual race overtaking performances
        best_single = (
            filtered[['driver_name', 'race_name', 'year', 
                       'grid', 'positionOrder', 'position']]
            .dropna(subset=['position'])
            .sort_values('position', ascending=False)
            .head(10)
        )
        best_single = best_single.rename(columns={
            'driver_name':   'Driver',
            'race_name':     'Race',
            'year':          'Year',
            'grid':          'Start',
            'positionOrder': 'Finish',
            'position': '↑ Gained'
        })
        best_single['↑ Gained'] = best_single['↑ Gained'].astype(int)
        
        st.dataframe(
            best_single.reset_index(drop=True),
            use_container_width=True,
            height=350
        )
    
    # Grid vs Finish scatter
    st.subheader("🎯 Grid Position vs Finishing Position")
    st.markdown("Points below the diagonal line indicate positions gained; above means positions lost.")
    
    scatter_sample = filtered.dropna(subset=['grid', 'positionOrder']).sample(
        min(2000, len(filtered)), random_state=42
    )
    
    fig_scatter = px.scatter(
        scatter_sample,
        x='grid',
        y='positionOrder',
        color='constructor_name',
        opacity=0.5,
        title='Starting Grid vs Finishing Position',
        labels={'grid': 'Grid Position', 'positionOrder': 'Finishing Position',
                'constructor_name': 'Constructor'},
        hover_data=['driver_name', 'race_name', 'year']
    )
    
    # Add diagonal reference line (grid = finish = no change)
    fig_scatter.add_shape(
        type='line',
        x0=1, y0=1, x1=22, y1=22,
        line=dict(color='red', width=1.5, dash='dash')
    )
    fig_scatter.add_annotation(
        x=18, y=15, text="No change line",
        showarrow=False, font=dict(color='red', size=10)
    )
    
    fig_scatter.update_layout(plot_bgcolor='white', height=450)
    st.plotly_chart(fig_scatter, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# TAB 4: PIT STOP ANALYSIS
# ════════════════════════════════════════════════════════════════

with tab4:
    st.header("Pit Stop Strategy Analysis")
    
    # Merge pit data with race year info
    pit_with_year = pd.merge(
        pit_agg,
        master[['raceId', 'driverId', 'year', 'constructor_name', 
                'positionOrder', 'driver_name']].drop_duplicates(),
        on=['raceId', 'driverId'],
        how='left'
    )
    
    pit_filtered = pit_with_year[
        (pit_with_year['year'] >= year_range[0]) &
        (pit_with_year['year'] <= year_range[1])
    ]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⚡ Fastest Pit Crews by Constructor")
        
        crew = (
            pit_filtered.groupby('constructor_name')['avg_stop_time']
            .mean()
            .sort_values()
            .head(15)
            .reset_index()
        )
        crew.columns = ['Constructor', 'Avg Stop Time (s)']
        crew['Avg Stop Time (s)'] = crew['Avg Stop Time (s)'].round(3)
        
        fig_crew = px.bar(
            crew,
            x='Constructor',
            y='Avg Stop Time (s)',
            color='Avg Stop Time (s)',
            color_continuous_scale='RdYlGn_r',
            text='Avg Stop Time (s)'
        )
        fig_crew.update_layout(
            xaxis_tickangle=-45,
            plot_bgcolor='white',
            height=420,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_crew, use_container_width=True)
    
    with col2:
        st.subheader("📊 Stop Count vs Avg Finishing Position")
        
        stop_strategy = (
            pit_filtered[pit_filtered['total_stops'].between(1, 4)]
            .groupby('total_stops')['positionOrder']
            .agg(['mean', 'count'])
            .reset_index()
        )
        stop_strategy.columns = ['Stops', 'Avg Finish Position', 'Count']
        stop_strategy['Avg Finish Position'] = stop_strategy['Avg Finish Position'].round(2)
        
        fig_strat = px.bar(
            stop_strategy,
            x='Stops',
            y='Avg Finish Position',
            color='Avg Finish Position',
            color_continuous_scale='RdYlGn_r',
            text='Avg Finish Position',
            title='Strategy Analysis: Stops vs Finishing Position'
        )
        fig_strat.update_layout(
            plot_bgcolor='white',
            height=420,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_strat, use_container_width=True)
    
    # Pit stop time distribution
    st.subheader("⏱️ Pit Stop Duration Distribution by Year")
    
    pit_stops_with_year = pd.merge(
        pit_stops,
        master[['raceId', 'driverId', 'year', 'constructor_name']].drop_duplicates(),
        on=['raceId', 'driverId'],
        how='left'
    )
    
    pit_year_filtered = pit_stops_with_year[
        (pit_stops_with_year['year'] >= year_range[0]) &
        (pit_stops_with_year['year'] <= year_range[1]) &
        (pit_stops_with_year['duration'].between(2, 60))  # realistic pit stop range
    ]
    
    fig_box = px.box(
        pit_year_filtered,
        x='year',
        y='duration',
        title='Pit Stop Duration by Year (Shows how pit stops have evolved)',
        labels={'duration': 'Duration (seconds)', 'year': 'Year'}
    )
    fig_box.update_layout(plot_bgcolor='white', height=400)
    st.plotly_chart(fig_box, use_container_width=True)

# ── FOOTER ────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "**Data Source:** [Ergast Motor Racing API](http://ergast.com/mrd/) | "
    "**Built with:** Python, Streamlit, Plotly | "
    "**GitHub:** [Your Repo Link]",
    unsafe_allow_html=False
)
