import streamlit as st
import geopandas as gpd
import pandas as pd
import leafmap.foliumap as leafmap
# from datetime import datetime, date
# import json

page_title='SBA HUBZone Governor Designated Areas'
st.set_page_config(page_title)
st.subheader(page_title)

# Custom CSS for checkboxes
custom_css = """
<style>
    .stCheckbox > div:first-child {
        display: flex;
        align-items: center;
    }
    .stCheckbox > div:first-child > div {
        margin-right: 10px;
    }
    .stCheckbox > div:first-child > div > input {
        width: 20px;
        height: 20px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Load the spatial data
@st.cache_data
def load_data():
    counties = gpd.read_file('data/sba_gov_elig_county.geojson') #20240916_gov_area_county
    tracts = gpd.read_file('data/sba_gov_elig_tract_al.geojson')
    return counties, tracts
    # return counties 

# counties = load_data()
counties, tracts = load_data()

# Create a Streamlit app
# st.sidebar.title('Filter by Expiration Date')

# Extract unique state values from both counties and tracts
# unique_states = sorted(pd.concat([counties['state_name'], tracts['state_name']]).unique())

# just counties for now
# unique_states = sorted(counties['statefp'].unique())
unique_states = sorted(pd.concat([counties['statefp'], tracts['statefp']]).unique())

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

if selected_states:
    filtered_counties = counties[counties['statefp'].isin(selected_states)]
    filtered_tracts = tracts[tracts['statefp'].isin(selected_states)]
else:
    filtered_counties = gpd.GeoDataFrame(columns=counties.columns).drop(counties.index)
    filtered_tracts = gpd.GeoDataFrame(columns=tracts.columns)

# Display the number of selected counties and tracts in the sidebar
st.sidebar.write(f"Number of selected counties: {len(filtered_counties)}")
st.sidebar.write(f"Number of selected tracts: {len(filtered_tracts)}")

# Count the number of county features per state
county_state_counts = counties['statefp'].value_counts().sort_index()
tract_state_counts = tracts['statefp'].value_counts().sort_index()

# Display counts of in the sidebar and list counties
st.sidebar.write("Count of counties and tracts per state:")
for state in selected_states: #_counts.items():
    county_count = county_state_counts.get(state, 0)
    tract_count =tract_state_counts.get(state, 0)
    st.sidebar.write(f"State {state}: {county_count} counties, {tract_count} tracts")

# for state, count in state_counts.items():
#     st.sidebar.write(f"{state}: {count}")

# Use the state of the checkbox to conditionally display the data
if selected_states: #toggle_state:
    st.write("Number of selected states:", len(selected_states)) #('Filtered Counties:', filtered_counties)
else:
    st.write("No states selected.") #'Filtered Tracts:', filtered_tracts)

# Get a list of counties in the selected states in alphabetical order
if not filtered_counties.empty:
    county_names = filtered_counties['name'].unique()
    sorted_county_names = sorted(county_names)
    # st.sidebar.write("Counties in selected states (alphabetical order):")
    # st.sidebar.write(sorted_county_names)

    # Display the filtered counties in a table format
    st.sidebar.write("Filtered Counties:")
    filtered_counties_display = filtered_counties[['statefp', 'name']].sort_values(by=['statefp', 'name']).reset_index(drop=True)
    st.sidebar.dataframe(filtered_counties_display)

# Define style functions for counties and tracts
def style_counties(feature):
    return {
        'fillColor': 'red',
        'color': 'red',
        'weight': 1,
        'fillOpacity': 0.4
    }

def style_tracts(feature):
    return {
        'fillColor': 'lightblue',
        'color': 'blue',
        'weight': 1,
        'fillOpacity': 0.6
    }

def style_states(feature):
    return {
        'fillColor': 'none',
        # 'color': 'red',
        'stroke': True,
        'color': 'black',
        'weight': 0.2,
        'fillOpacity': 0.4
    }

# Create a Folium map
m = leafmap.Map(
    layers_control=True,
    draw_control=False,
    measure_control=False,
    fullscreen_control=False,
    center=[37.8, -96], 
    zoom=9,
    basemap='Google Satellite'
)

if not filtered_counties.empty:
    m.add_gdf(
        gdf=filtered_counties,
        layer_name='Counties',
        style_function=style_counties,  # Apply the style dictionary directly
        # style_dict=style_counties(),  # Apply the style dictionary directly
        info_mode='on_hover'
    )
# Calculate the bounding box of the selected counties
    bounds = filtered_counties.total_bounds
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

if not filtered_tracts.empty:
    m.add_gdf(
        gdf=filtered_tracts,
        layer_name='Tracts',
        style_function=style_tracts,  # Apply the style dictionary directly
        # style_dict=style_counties(),  # Apply the style dictionary directly
        info_mode='on_hover'
    )

polygons = "https://raw.githubusercontent.com/opengeos/leafmap/master/examples/data/us_states.json"
m.add_geojson(
    polygons,
    layer_name='States',
    style_function=style_states # Apply the style dictionary directly
    # info_mode='on_hover'
)
# if not filtered_tracts.empty:
#     m.add_gdf(
#         gdf=filtered_tracts,
#         layer_name='Tracts',
#         style_function=style_tracts,  # Apply the style dictionary directly
#         # style_dict=style_counties(),  # Apply the style dictionary directly
#         info_mode='on_hover'
#     )

m.to_streamlit(800, 600)