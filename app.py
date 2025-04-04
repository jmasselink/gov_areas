import streamlit as st
import geopandas as gpd
import pandas as pd
import leafmap.foliumap as leafmap
from datetime import datetime, date
# import json

page_title='SBA HUBZone Governor Designated Areas'
st.set_page_config(page_title)
st.subheader(page_title)

# Load the spatial data
@st.cache_data
def load_data():
    counties = gpd.read_file('data/20250403_gda_county.geojson') #20240916_gov_area_county
    tracts = gpd.read_file('data/20250403_gda_tract.geojson')
    return counties, tracts

counties, tracts = load_data()

# Convert disaster declaration dates to datetime
counties['date_approved'] = pd.to_datetime(counties['date_approved'], errors='coerce')
tracts['date_approved'] = pd.to_datetime(tracts['date_approved'], errors='coerce')

# Drop rows with NaT in 'date_approved'
counties = counties.dropna(subset=['date_approved'])
tracts = tracts.dropna(subset=['date_approved'])

# Get the date range for the slider
combined_dates = pd.concat([counties['date_approved'], tracts['date_approved']])
min_date = combined_dates.min().date()
max_date = combined_dates.max().date()

# min_date = tracts['date_approved'].min().date()
# max_date = counties['date_approved'].max().date()

# Create a Streamlit app
st.sidebar.title('Filter by Approval Date')

# Slider for selecting the date range
try:
    start_date, end_date = st.sidebar.slider(
        'Select date range',
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD"
    )
    expiration_date=date(2028, 6, 30)
    st.write("Approval date range:", start_date, "to", end_date, "; Expiration date:", expiration_date) #, end_date)
except Exception as e:
    st.error(f"Error in slider configuration: {e}")

# Extract unique state values from both counties and tracts
unique_states = sorted(pd.concat([counties['state_name'], tracts['state_name']]).unique())

# add a checkbox to the sidebar
select_all = st.sidebar.checkbox('Select/Deselect All States', value=True)

#toggle_state = st.sidebar.checkbox('Toggle State')
selected_states = st.sidebar.multiselect(
    'Select States',
    options=unique_states,
    default=unique_states if select_all else []
)

# Sort the selected states
selected_states.sort()

start_datetime = datetime.combine(start_date, datetime.min.time())
end_datetime = datetime.combine(end_date, datetime.max.time())

# Filter the data based on the selected date range and states
if selected_states: #toggle_state:
    filtered_counties = counties[(counties['date_approved'] >= start_datetime) & (counties['date_approved'] <= end_datetime) & (counties['state_name'].isin(selected_states))]
    filtered_tracts = tracts[(tracts['date_approved'] >= start_datetime) & (tracts['date_approved'] <= end_datetime) & (tracts['state_name'].isin(selected_states))]
else:
    filtered_counties = gpd.GeoDataFrame(columns=counties.columns)
    filtered_tracts = gpd.GeoDataFrame(columns=tracts.columns)

# Ensure that filtered data is JSON serializable by converting 'date_approved' to string if it exists
if not filtered_counties.empty and 'date_approved' in filtered_counties.columns:
    filtered_counties['date_approved'] = filtered_counties['date_approved'].dt.strftime('%Y-%m-%d')

if not filtered_tracts.empty and 'date_approved' in filtered_tracts.columns:
    filtered_tracts['date_approved'] = filtered_tracts['date_approved'].dt.strftime('%Y-%m-%d')

for column in filtered_counties.select_dtypes(include=['datetime64']).columns:
    filtered_counties[column] = filtered_counties[column].dt.strftime('%Y-%m-%d')

for column in filtered_tracts.select_dtypes(include=['datetime64']).columns:
    filtered_tracts[column] = filtered_tracts[column].dt.strftime('%Y-%m-%d')

if selected_states:
    st.write(f"Selected states:", len(selected_states),
             f"counties:", len(filtered_counties),
             f"tracts:", len(filtered_tracts))
else:
    st.write("No states, counties, or tracts selected.")

# st.write(f"Number of selected counties: {len(filtered_counties)}")
# st.write(f"Number of selected tracts: {len(filtered_tracts)}")

# Define style functions for counties and tracts
def style_counties(feature):
    return {
        'fillColor': 'red',
        'color': 'red',
        'weight': 2,
        'fillOpacity': 0.4
    }

def style_tracts(feature):
    return {
        'fillColor': 'lightblue',
        'color': 'blue',
        'weight': 1,
        'fillOpacity': 0.6
    }

if st.button('Clear Cache'):
    st.cache_data.clear()

# Create a Folium map
m = leafmap.Map(
    layers_control=True,
    draw_control=False,
    measure_control=False,
    fullscreen_control=False,
    center=[37.8, -96], 
    zoom=3
)

if not filtered_counties.empty:
    m.add_gdf(
        gdf=filtered_counties,
        layer_name='Counties',
        style_function=style_counties,  # Apply the style dictionary directly
        # style_dict=style_counties(),  # Apply the style dictionary directly
        info_mode='on_hover'
    )

if not filtered_tracts.empty:
    m.add_gdf(
        gdf=filtered_tracts,
        layer_name='Tracts',
        style_function=style_tracts,  # Apply the style dictionary directly
        # style_dict=style_counties(),  # Apply the style dictionary directly
        info_mode='on_hover'
    )

m.to_streamlit(800, 600)