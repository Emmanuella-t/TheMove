
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="TheMove",
    page_icon="📍",
    layout="wide"
)

# Load location dataset
@st.cache_data
def load_places():
    return pd.read_csv(
        "themove_little_rock_places.csv"
    )

places = load_places()

# Page heading
st.title("TheMove 📍")
st.subheader("What's the Move?")
st.write(
    "Discover activities and real places around Little Rock!"
)

# Sidebar inputs
st.sidebar.header("Plan Your Move")

location = st.sidebar.text_input(
    "Where are we making moves?",
    placeholder="Enter your city or location",
    value="Little Rock, AR"
)

# Validate supported location
supported_locations = {
    "little rock",
    "little rock, ar",
    "little rock, arkansas"
}

if location.strip().lower() not in supported_locations:
    st.warning(
        "TheMove currently supports locations around "
        "central Little Rock, Arkansas. "
        "Additional cities are not yet supported."
    )
    st.stop()

category = st.sidebar.selectbox(
    "What are you in the mood for?",
    sorted(places["activity_category"].dropna().unique())
)

place_types = sorted(
    places.loc[
        places["activity_category"] == category,
        "fclass"
    ].dropna().unique().tolist()
)

place_type = st.sidebar.selectbox(
    "Preferred place type",
    ["Any"] + place_types
)

# Filter by selected category
matches = places[
    places["activity_category"] == category
].copy()

if place_type != "Any":
    matches = matches[
        matches["fclass"] == place_type
    ]

# Sort by distance from central Little Rock
matches = matches.sort_values(
    ["distance_km", "name"]
)

st.subheader("Your Suggested Places")

if matches.empty:
    st.warning(
        "No places found for this category. "
        "Try selecting another activity."
    )
else:
    st.success(
        f"Found {len(matches)} matching places!"
    )

    st.dataframe(
        matches[
            ["name", "fclass", "distance_km"]
        ].head(15),
        hide_index=True,
        use_container_width=True
    )

    st.subheader("Explore on the Map")

    st.map(
        matches.head(100),
        latitude="latitude",
        longitude="longitude"
    )

st.caption(
    "Places are sourced from OpenStreetMap geographic data. "
    "Distances are approximate from central Little Rock, "
    "not from the user's exact location. "
    "Prices and opening hours are not verified."
)
