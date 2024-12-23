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
    counties = gpd.read_file('data/20241220_gov_area_county.geojson') #20240916_gov_area_county
    tracts = gpd.read_file('data/20241220_gov_area_tract.geojson')
    return counties, tracts

counties, tracts = load_data()

# Convert disaster declaration dates to datetime
counties['expires'] = pd.to_datetime(counties['expires'], errors='coerce')
tracts['expires'] = pd.to_datetime(tracts['expires'], errors='coerce')

# Drop rows with NaT in 'expires'
counties = counties.dropna(subset=['expires'])
tracts = tracts.dropna(subset=['expires'])

# Get the date range for the slider
min_date = counties['expires'].min().date()
max_date = counties['expires'].max().date()

# Create a Streamlit app
st.sidebar.title('Filter by Expiration Date')

# Slider for selecting the date range
try:
    start_date, end_date = st.sidebar.slider(
        'Select date range',
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD"
    )
    st.write("Expiration date range:", start_date, "to", end_date)
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
    filtered_counties = counties[(counties['expires'] >= start_datetime) & (counties['expires'] <= end_datetime) & (counties['state_name'].isin(selected_states))]
    filtered_tracts = tracts[(tracts['expires'] >= start_datetime) & (tracts['expires'] <= end_datetime) & (tracts['state_name'].isin(selected_states))]
else:
    filtered_counties = gpd.GeoDataFrame(columns=counties.columns)
    filtered_tracts = gpd.GeoDataFrame(columns=tracts.columns)

# Ensure that filtered data is JSON serializable by converting 'expires' to string if it exists
if not filtered_counties.empty and 'expires' in filtered_counties.columns:
    filtered_counties['expires'] = filtered_counties['expires'].dt.strftime('%Y-%m-%d')

if not filtered_tracts.empty and 'expires' in filtered_tracts.columns:
    filtered_tracts['expires'] = filtered_tracts['expires'].dt.strftime('%Y-%m-%d')

for column in filtered_counties.select_dtypes(include=['datetime64']).columns:
    filtered_counties[column] = filtered_counties[column].dt.strftime('%Y-%m-%d')

for column in filtered_tracts.select_dtypes(include=['datetime64']).columns:
    filtered_tracts[column] = filtered_tracts[column].dt.strftime('%Y-%m-%d')

# Display the number of selected counties and tracts in the sidebar
st.sidebar.write(f"Number of selected counties: {len(filtered_counties)}")
st.sidebar.write(f"Number of selected tracts: {len(filtered_tracts)}")

# Use the state of the checkbox to conditionally display the data
if selected_states: #toggle_state:
    st.write("Number of selected states:", len(selected_states)) #('Filtered Counties:', filtered_counties)
else:
    st.write("No states selected.") #'Filtered Tracts:', filtered_tracts)

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