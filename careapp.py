
import streamlit as st
import pandas as pd 
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
from datetime import date, timedelta, datetime
import warnings

warnings.filterwarnings("ignore")

st.set_page_config(page_title="CBP and HHS Care Transition Efficiency and Placement Outcome ", page_icon=":hospital:", layout="wide")
st.image("images/Healthcare_logo.png.png", width=200)
st.title(" :hospital: Care Transition Efficiency and Placement Outcome Analytics")
st.markdown(" :pen: This application provides insights into transition efficiency and placement outcomes for patients.")

@st.cache_data
def load_data():
    data = pd.read_csv("HHS_Unaccompanied_Alien_Children_Program.csv")
    data["Date"] = pd.to_datetime(data["Date"])
    data = data.sort_values(by="Date")
    return data

df = load_data()

with st.sidebar:
    st.image("images/streamlit_logo.png.png", width=200)
    st.title(" :hospital: Healthcare Analytics Dashboard")


def custom_quarter(date):
    if pd.isna(date):
        return None

    month = date.month
    year = date.year
    if month in [2, 3, 4]:
        return pd.Period(year=year, quarter=1, freq='Q')
    elif month in [5, 6, 7]:
        return pd.Period(year=year, quarter=2, freq='Q')
    elif month in [8, 9, 10]:
        return pd.Period(year=year, quarter=3, freq='Q')
    else:
        return pd.Period(year=year if month != 1 else year-1, quarter=4, freq='Q')
    
def aggregate_data(df, freq):

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])

    if freq == 'Q':
        df = df.copy()
        df['Quarter'] = df['Date'].apply(custom_quarter)
        df_agg = df.groupby('Quarter').agg({
            'Children apprehended and placed in CBP custody*': 'sum',
            'Children in CBP custody': 'sum',
            'Children transferred out of CBP custody': 'sum',
            'Children in HHS Care': 'sum',
            'Children discharged from HHS Care': 'sum'
        })
        return df_agg 
    
    else:
         return df.resample(freq, on='Date').agg({
        'Children apprehended and placed in CBP custody*': 'sum',
        'Children in CBP custody': 'sum',
        'Children transferred out of CBP custody': 'sum',
        'Children in HHS Care': 'sum',
        'Children discharged from HHS Care': 'sum'
         })
    


def get_weekly_data(df):
    return aggregate_data(df, 'W')

def get_monthly_data(df):
    return aggregate_data(df, 'M')

def get_yearly_data(df):
    return aggregate_data(df, 'Y')

def get_quarterly_data(df):
    return aggregate_data(df, 'Q')

def format_with_commas(number):
    return f"{number:,}"


def create_metric_chart(df, column, color, chart_type, height=150, time_frame="daily"):
    chart_data = df[[column]]
    chart_data = chart_data.reset_index()
    if time_frame == 'Quarterly':
        chart_data.index = pd.to_datetime(chart_data.index)
        chart_data.index = chart_data.index.strftime('%Y Q%q')
    if chart_type=='line':
        st.line_chart(chart_data, y=column, color=color, height="content")
    if chart_type=='Area':
        st.area_chart(chart_data, y=column, color=color, height="content")



def calculate_delta(df, column):
    if len(df) <2:
        return 0, 0
    current_value = df[column].iloc[-1]
    previous_value = df[column].iloc[-2]
    delta = current_value - previous_value
    if previous_value == 0:
        delta_percent = 0
    else:
        delta_percent = (delta / previous_value) * 100
    return delta, delta_percent


def display_metric(col, title, value, df, column, color, time_frame, chart_selection):
    with col:
        with st.container(border=True):
            delta, delta_percent = calculate_delta(df, column)
            delta_str = f"{delta:+,.0f} ({delta_percent:+.2f}%)"
            st.metric(title, format_with_commas(value), delta=delta_str)
            create_metric_chart(df, column, color, time_frame=time_frame, chart_type=chart_selection) 

with st.sidebar:
    
    st.header(" :gear: User Capabilities")

    max_date = df["Date"].max().date()
    default_start_date = max_date - timedelta(days=30)
    default_end_date = max_date
    start_date = st.date_input("Start date",default_start_date, min_value=df["Date"].min().date(), max_value=max_date)
    end_date = st.date_input("End date", default_end_date, min_value=start_date, max_value=max_date)
    time_frame = st.selectbox("Select Time Frame", ("Daily", "Weekly", "Monthly", "Quarterly"),
                              )
    chart_selection = st.selectbox("Select a chart type", ("line", "Area"))


if time_frame == "Daily":
    df_display = df.set_index('Date')
elif time_frame == "Weekly":
    df_display = get_weekly_data(df)
    df['Date'] = pd.to_datetime(df['Date'])
    weekly = df.resample('W', on='Date').sum().reset_index()
elif time_frame == "Monthly":
    df_display = get_monthly_data(df)
    df['Date'] = pd.to_datetime(df['Date'])
    monthly = df.resample('M', on='Date').sum().reset_index()
elif time_frame == "Quarterly":
    df_display = get_quarterly_data(df)
    df['Date'] = pd.to_datetime(df['Date'])
    quarterly = df.resample('Q', on='Date').sum().reset_index()


tab1, tab2, tab3 = st.tabs(["🌟 All-Time Statistics", "✍️ Backlogs and Delays", "🚨 KPI"])

df['Transfer Efficiency'] = (df['Children transferred out of CBP custody']/df['Children in CBP custody'])
df['Transfer Efficiency'] = df['Transfer Efficiency'].replace([px.np.inf,-px.np.inf],px.np.nan)
    
df['Children in HHS Care'] = df['Children in HHS Care'].str.replace(',', '').astype(float)
df['Discharge Rate'] = (df['Children discharged from HHS Care']/df['Children in HHS Care'])
df['Discharge Rate'] = df['Discharge Rate'].replace([px.np.inf,-px.np.inf],px.np.nan)

df["Cummulative Entries"] = df["Children apprehended and placed in CBP custody*"].cumsum()
df["Cummulative Exits"] = df["Children discharged from HHS Care"].cumsum()
df["Cummulative Throughput Rate"] = df["Children discharged from HHS Care"]/df["Children apprehended and placed in CBP custody*"]


with tab1:
    st.subheader("👉All-Time Statistics")
    metrics = [
    {"title":"Transfer Efficiency", "column": "Children transferred out of CBP custody", "color": "#ff5a0e"},
    {"title":"Discharge Rate", "column": "Children discharged from HHS Care", "color": "#2ca02c"},
    {"title":"Cummulative Throughput Rate", "column":"Children apprehended and placed in CBP custody*", "color": "#9b1fb4"}
    ]

    cols = st.columns(3)
    for col, metric in zip(cols, metrics):
       display_metric(col, metric["title"], df[metric["column"]].sum(), df_display, metric["column"], metric["color"], time_frame, chart_selection)

    st.subheader("📆Select Duration")
    if time_frame =="Quarterly":
      start_quarter = custom_quarter(default_start_date)
      end_quarter = custom_quarter(default_end_date)
      mask = (df_display.index >= start_quarter) & (df_display.index <= end_quarter)
    else:
       mask = (df_display.index >= pd.Timestamp(start_date)) & (df_display.index <= pd.Timestamp(end_date)) # type: ignore
    df_filtered = df_display.loc[mask]

    cols = st.columns(3)
    for col, (title, column, color) in zip(cols, [(m["title"], m["column"], m["color"]) for m in metrics]):
       display_metric(col, title.split()[-1], df_filtered[column].sum(), df_filtered, column, color, time_frame, chart_selection)

    with st.expander("See Dataframe (Selected time frame)"):
         st.dataframe(df_filtered)
         
         
df["CBP_Backlog"] = (df["Children apprehended and placed in CBP custody*"]-df["Children transferred out of CBP custody"])
df["HHS_Backlog"] = (df["Children in HHS Care"]-df["Children discharged from HHS Care"])

with tab2:
    st.markdown("⏱Child Custody Backlog & Bottelneck Monitoring")

    st.subheader("🕵️‍♂️Backlog Detection")
    monthly_df = get_monthly_data(df)
    monthly_df = monthly_df.reset_index()
    fig2 = px.bar(df, x="Date", y=["CBP_Backlog","HHS_Backlog"],
              color_discrete_sequence=["#fcff33","#ff3333"],)
    fig2.update_layout(title= "Backlog trends")
    st.plotly_chart(fig2, use_container_width=True)


    st.subheader("🤖Detected Bottelnecks")
    df["CBP_bottleneck"] = ((df["Children in CBP custody"].diff()>0) & (df["Children transferred out of CBP custody"].diff()<=0))
    df["HHS_bottleneck"] = ((df["Children in HHS Care"].diff()>0) & (df["Children discharged from HHS Care"].diff()<=0))
    bottlenecks = df[(df["CBP_bottleneck"]) | (df["HHS_bottleneck"])]
    with st.expander("Data Preview"):
       st.dataframe(bottlenecks)

    st.subheader("⚡Flow Monitering")

    monthly_df = get_monthly_data(df)
    monthly_df = monthly_df.reset_index()
    fig = px.line(monthly_df, x="Date", y=[ "Children in CBP custody",  "Children transferred out of CBP custody",
        "Children in HHS Care", "Children discharged from HHS Care"],
              color_discrete_sequence=["#720eff","#ff2e0e", "#32ff0e", "#0eefff"],
              markers=True,
              title="Flow Relationship Analysis")
    fig.update_traces(textposition="top center")
    st.plotly_chart(fig, use_container_width=True)



# Create Transfer Rate column
df["CBP_Transfer_Rate"] = (
    df["Children transferred out of CBP custody"] /
    df["Children in CBP custody"]
)

# Handle divide by zero / NaN
df["CBP_Transfer_Rate"] = df["CBP_Transfer_Rate"].fillna(0)

# HHS discharge rate
df["HHS_discharge_rate"] = (
    df["Children discharged from HHS Care"] /
    df["Children in HHS Care"]
).replace([float("inf"), -float("inf")], 0).fillna(0)


with tab3:
    st.subheader("📝Key Performance Indicator")   
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Avg CBP Transfer Rate",f"{df['CBP_Transfer_Rate'].mean():.2}")
    col2.metric("Avg HHS Discharge Rate",f"{df['HHS_discharge_rate'].mean():.2}")
    col3.metric("Avg Daily CBP Backlog Change",int(df['CBP_Backlog'].mean()))
    col4.metric("Avg HHS Backlog Change",int(df['HHS_Backlog'].mean()))

    
    if df["HHS_Backlog"].mean() > 0:
        st.warning("HHS backlog is slower than inflow, care backlog risk")
    else:
        st.success("HHS discharge are balanced with transfers.")

    df["Length_of_Stay"] = df["Children in HHS Care"] / df["Children discharged from HHS Care"].replace(0,1)

    st.sidebar.subheader("⚠️Alert Thresholds")
    los_threshold = st.sidebar.slider("Max Avg Length of Stay (days)",
                                  min_value=1, max_value=20, value=7)

    transfer_threshold = st.sidebar.slider("Max Transfer Rate(%)",
                                       min_value=1, max_value=100, value=30)
    
    df["Transfer Rate"] = (
    df["Children transferred out of CBP custody"] /
    df["Children in CBP custody"]
      ) * 100
    avg_los = df["Length_of_Stay"].mean()
    transfer_rate = (df["Transfer Rate"].sum()/len(df) * 100)

    with col1:
        if avg_los > los_threshold:
            st.error(f"Avg LOS: {avg_los:.2f} days (Above Threshold)")
        else:
            st.success(f"Avg LOS: {avg_los:.2f} days (Within Limit)")

    with col2:
        if transfer_rate > transfer_threshold:
            st.error(f"Transfer Rate: {transfer_rate:.1f}% (High)")
        else:
            st.success(f"Transfer Rate: {transfer_rate:.1f}% (Normal)")


    df["CBP_Transfer_Ratio"] = (df['Children transferred out of CBP custody']/df['Children in CBP custody'])
    df["HHS_Discharge_Ratio"] = (df['Children discharged from HHS Care']/df['Children in HHS Care'])

    df["CBP_Transfer_Ratio"] = df["CBP_Transfer_Ratio"] * 100
    df["HHS_Discharge_Ratio"] = df["HHS_Discharge_Ratio"] * 100

    st.sidebar.header("🔺Metric Mode🔻")
    metric_mode = st.sidebar.radio("Select Metric Type",["Absolute Numbers", "Ratio / Percentage"])
    st.subheader("🔑Key System Metrics")
    col1, col2 = st.columns(2)
    if metric_mode == "Absolute Numbers":
        value = df["Children in CBP custody"].dropna().iloc[-1]

        col1.metric(
           "Children in CBP custody",
           f"{int(value):,}"
        )

        value = df["Children in HHS Care"].dropna().iloc[-1]
        col1.metric(
           "Children in CBP custody",
           f"{int(value):,}"
        )
    else:
        col1.metric("CBP Transfer Rate",f"{df['CBP_Transfer_Ratio'].iloc[-1]:.2f}%")
        col2.metric("HHS Dscharge Rate",f"{df['HHS_Discharge_Ratio'].iloc[-1]:.2f}%")


    st.subheader("⌛System Flow Trend")
    if metric_mode == "Absolute Numbers":
        fig = px.line(df, x="Date", y=["Children in CBP custody", "Children in HHS Care"],
                  title="Children in system")
    else:
        fig = px.line(df, x="Date", y=["CBP_Transfer_Ratio", "HHS_Discharge_Ratio"],
                  title="System Efficiency Ratio(%)")
        st.plotly_chart(fig,use_container_width=True)

