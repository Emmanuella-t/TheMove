import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="TheMove",
    page_icon="📍",
    layout="wide"
)

@st.cache_data
def load_places():
   return pd.read_csv(
    "themove_little_rock_places.csv"
)

places = load_places()

st.title("TheMove 📍")
st.subheader("What's the Move?")
st.write(
    "Discover activities and real places around Little Rock!"
)

st.sidebar.header("Plan Your Move")

category = st.sidebar.selectbox(
    "What are you in the mood for?",
    sorted(places["activity_category"].unique())
)

distance = st.sidebar.slider(
    "Maximum distance from downtown (km)",
    min_value=1,
    max_value=15,
    value=10
)

place_type = st.sidebar.selectbox(
    "Preferred place type",
    ["Any"] + sorted(
        places.loc[
            places["activity_category"] == category,
            "fclass"
        ].unique()
    .tolist())
)

matches = places[
    (places["activity_category"] == category)
    & (places["distance_km"] <= distance)
].copy()

if place_type != "Any":
    matches = matches[
        matches["fclass"] == place_type
    ]

matches = matches.sort_values(
    ["distance_km", "name"]
)

st.subheader("Your Recommended Places")

if matches.empty:
    st.warning(
        "No matching places found. Try a different "
        "category or increase your distance."
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
    "Places are from OpenStreetMap geographic data. "
    "Distances are approximate from central Little Rock. "
    "Opening hours and prices are not verified."
)
