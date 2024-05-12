import requests
import random
import pandas as pd
import time
import csv
import numpy as np
import streamlit as st
import plotly.express as px
import os
import warnings
from datetime import datetime, timedelta
warnings.filterwarnings('ignore')

API_KEY = None
API_ENDPOINT = None

import datetime

NUM_TEST_ROWS = 2000
START_DATE = datetime.date(2024, 6, 7)
END_DATE = datetime.date(2024, 6, 10)

def get_olympics_data_from_api(api_key, api_endpoint):
    try:
        response = requests.get(api_endpoint, headers={'Authorization': f'Bearer {api_key}'})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as err:
        print(f"Error occurred: {err}")
        return None

def clean_olympics_data(data):
    sports_data_list = [
        {
            'Timestamp': entry['Timestamp'],
            'Viewer IPs': entry['ip_address'],
            'User ID': entry['user_id'],
            'Country': entry['country'],
            'Sport': entry['sport'],
            'Duration': entry['duration'],
            'Device': entry['device'],
            'Channel': entry['channel']
        } for entry in data
    ]
    sports_data_df = pd.DataFrame(sports_data_list)
    sports_data_df.replace('', pd.NA, inplace=True)
    sports_data_df.dropna(inplace=True)
    return sports_data_df

def generate_random_ip_addresses(num_addresses):
    return ['.'.join(str(random.choice(range(1, 255))) for _ in range(4)) for _ in range(num_addresses)]

def generate_timestamps(start_date, end_date):
    timestamps = []
    current_date = start_date
    while current_date <= end_date:
        for hour in range(24):
            timestamps.append(current_date.strftime(f'%Y-%m-%d {hour:02}:00:00'))
        current_date += datetime.timedelta(days=1)
    return timestamps

def generate_test_data(num_rows):
    random_ip_addresses = generate_random_ip_addresses(num_rows)
    timestamps = generate_timestamps(START_DATE, END_DATE)
    user_ids = list(range(10000, 20000))
    countries = ['USA', 'Canada', 'Mexico', 'Chile', 'Brazil', 'Namibia', 'South Africa']
    sports = ['Swimming', 'Basketball', 'Soccer', 'Hockey', 'Snowboarding', 'Tennis']
    durations = [30, 60, 90, 40, 50, 10, 120, 70, 80]
    devices = ['Desktop', 'Mobile', 'Tablet']
    channels = ['Main Channel', 'Events Channel 2', 'Live Sports']

    sports_data = []
    for _ in range(num_rows):
        sports_data.append({
            'Timestamp': random.choice(timestamps),
            'Viewer IPs': random.choice(random_ip_addresses),
            'User ID': random.choice(user_ids),
            'Country': random.choice(countries),
            'Sport': random.choice(sports),
            'Duration': random.choice(durations),
            'Device': random.choice(devices),
            'Channel': random.choice(channels)
        })
    return pd.DataFrame(sports_data)

def get_data(use_api=False, api_key=None, api_endpoint=None):
    if use_api:
        if api_key and api_endpoint:
            time.sleep(15)  # Add a 15-second sleep
            data = get_olympics_data_from_api(api_key, api_endpoint)
            if data:
                fun_olympics_df = clean_olympics_data(data)
                return fun_olympics_df
        else:
            print("API key or endpoint not provided. Returning generated data instead.")
    else:
        fun_olympics_test = generate_test_data(NUM_TEST_ROWS)
        return fun_olympics_test

#df = get_data(use_api=False)
df = df = pd.read_csv("olympics_data.csv", encoding = "ISO-8859-1")

# Dashboard
st.set_page_config(page_title="FunOlmypics_Dash", page_icon=":bar_chart:",layout="wide")

st.title("Fun Olympics Streaming Dashboard")
st.markdown('<style>div.block-container{padding-top:1rem;}</style>',unsafe_allow_html=True)

col1, col2 = st.columns((2))
df["Timestamp"] = pd.to_datetime(df["Timestamp"])

# Getting the min and max dates
startDate = pd.to_datetime(df["Timestamp"]).min()
endDate = pd.to_datetime(df["Timestamp"]).max()

with col1:
    date1 = pd.to_datetime(st.date_input("Start Date", startDate))

with col2:
    date2 = pd.to_datetime(st.date_input("End Date", endDate))

df = df[(df["Timestamp"] >= date1) & (df["Timestamp"] <= date2)].copy()

st.sidebar.header("Choose your filter: ")
# Create for Country
Country = st.sidebar.multiselect("Pick your Country", df["Country"].unique())
if not Country:
    df2 = df.copy()
else:
    df2 = df[df["Country"].isin(Country)]

# Create for Sport
Sport = st.sidebar.multiselect("Pick the Sport", df2["Sport"].unique())
if not Sport:
    df3 = df2.copy()
else:
    df3 = df2[df2["Sport"].isin(Sport)]

# Create for Device
Device = st.sidebar.multiselect("Pick the Device",df3["Device"].unique())

# Filter the data based on Country, Sport and Device
if not Country and not Sport and not Device:
    filtered_df = df
elif not Sport and not Device:
    filtered_df = df[df["Country"].isin(Country)]
elif not Country and not Device:
    filtered_df = df[df["Sport"].isin(Sport)]
elif Sport and Device:
    filtered_df = df3[df["Sport"].isin(Sport) & df3["Device"].isin(Device)]
elif Country and Device:
    filtered_df = df3[df["Country"].isin(Country) & df3["Device"].isin(Device)]
elif Country and Sport:
    filtered_df = df3[df["Country"].isin(Country) & df3["Sport"].isin(Sport)]
elif Device:
    filtered_df = df3[df3["Device"].isin(Device)]
else:
    filtered_df = df3[df3["Country"].isin(Country) & df3["Sport"].isin(Sport) & df3["Device"].isin(Device)]

category_df = filtered_df.groupby(by = ["Sport"], as_index = False)["Duration"].sum()

with col1:
    st.subheader("Views Per Sport")
    fig = px.bar(category_df, x = "Sport", y = "Duration", text = ['{:,d}'.format(x) for x in category_df["Duration"]],
                 template = "seaborn")
    st.plotly_chart(fig,use_container_width=True, height = 200)

with col2:
    st.subheader("Views Per Country")
    fig = px.pie(filtered_df, values = "Duration", names = "Country", hole = 0.5)
    fig.update_traces(text = filtered_df["Country"], textposition = "outside")
    st.plotly_chart(fig,use_container_width=True)

cl1, cl2 = st.columns((2))
with cl1:
    with st.expander("views_per_sport"):
        st.write(category_df.style.background_gradient(cmap="Blues"))
        csv = category_df.to_csv(index = False).encode('utf-8')
        st.download_button("Download Data", data = csv, file_name = "Views_Per_Country.csv", mime = "text/csv",
                            help = 'Click here to download the data as a CSV file')

filtered_df["date"] = filtered_df["Timestamp"].dt.date

st.subheader('Time Series Analysis')

linechart = pd.DataFrame(filtered_df.groupby(filtered_df["date"])["Duration"].sum()).reset_index()
fig2 = px.line(linechart, x = "date", y="Duration", labels = {"Duration": "Views"},height=500, width = 1000,template="gridon")
st.plotly_chart(fig2,use_container_width=True)

with st.expander("View Data of TimeSeries:"):
    st.write(linechart.T.style.background_gradient(cmap="Blues"))
    csv = linechart.to_csv(index=False).encode("utf-8")
    st.download_button('Download Data', data = csv, file_name = "TimeSeries.csv", mime ='text/csv')

chart1, chart2 = st.columns((2))
with chart1:
    st.subheader('Views By Channel')
    fig = px.pie(filtered_df, values = "Duration", names = "Channel", template = "plotly_dark")
    fig.update_traces(text = filtered_df["Channel"], textposition = "inside")
    st.plotly_chart(fig,use_container_width=True)

with chart2:
    st.subheader('Views By Streaming Device')
    fig = px.pie(filtered_df, values = "Duration", names = "Device", template = "gridon")
    fig.update_traces(text = filtered_df["Device"], textposition = "inside")
    st.plotly_chart(fig,use_container_width=True)

import plotly.figure_factory as ff
st.subheader("Olympic Games Streaming Summary")
with st.expander("Summary_Table"):
    df_sample = df[0:15][["Timestamp","Country","Sport","Device","Channel"]]
    fig = ff.create_table(df_sample, colorscale = "Cividis")
    st.plotly_chart(fig, use_container_width=True)

# Download orginal DataSet
csv = df.to_csv(index = False).encode('utf-8')
st.download_button('Download CSV Dataset', data = csv, file_name = "OlympicData.csv",mime = "text/csv")
