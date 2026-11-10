"""TheMove: Little Rock group activity planner + separate research ML demonstration.

Venue recommendations use explicit group preferences and keyword rules.
The Random Forest is trained for anonymous research items, not local venues.
"""
from pathlib import Path
import html
import json
import joblib
import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parent
CSV = BASE / "themove_little_rock_places.csv"
LOGO = BASE / "assets" / "logo_horizontal.png"
ICON = BASE / "assets" / "app_icon.png"
MODEL_PATH = BASE / "models" / "themove_rf_model.joblib"
MODEL_INFO_PATH = BASE / "models" / "themove_model_info.json"

CATEGORIES = ["Food & Drinks", "Outdoor & Nature", "Arts & Culture", "Entertainment", "Sports & Recreation"]
EMOJI = {"Food & Drinks": "🍜", "Outdoor & Nature": "🌳", "Arts & Culture": "🎨", "Entertainment": "🎭", "Sports & Recreation": "🏀"}
KEYWORDS = {
    "Food & Drinks": ["food", "eat", "dinner", "lunch", "brunch", "restaurant", "cafe", "coffee", "drink", "snack", "chill", "catch up"],
    "Outdoor & Nature": ["outside", "outdoor", "nature", "park", "hike", "walk", "picnic", "relax", "scenic"],
    "Arts & Culture": ["art", "museum", "history", "culture", "gallery", "creative"],
    "Entertainment": ["fun", "comedy", "movie", "cinema", "show", "nightlife", "music", "theatre", "dance", "party"],
    "Sports & Recreation": ["sports", "sport", "active", "fitness", "basketball", "swim", "play", "game", "adventure"],
}

st.set_page_config(
    page_title="TheMove | What's the move?",
    page_icon=str(ICON) if ICON.exists() else "🥭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
:root { --coral:#F53147;--orange:#FF7A00;--gold:#FFCC33;--ink:#111827;--cream:#FFF9F0; }
.stApp { background:#FFF9F0; color:#111827; }
.block-container { max-width:1140px; padding-top:1.1rem; }
h1,h2,h3 { font-family:'Space Grotesk',sans-serif!important; letter-spacing:-.04em!important; }
html,body,p,div,label {font-family:'DM Sans',sans-serif;}
[data-testid='stHeader'] {background:transparent;}
.hero {border-radius:30px;background:linear-gradient(115deg,#F53147 0%,#FF6246 55%,#FF9300 100%);padding:46px 44px;color:white;position:relative;overflow:hidden;margin:16px 0 26px;}
.hero h1 {font-size:clamp(2.5rem,5vw,4.8rem);line-height:1.03;letter-spacing:-.06em;color:white!important;max-width:730px;margin:12px 0;}
.hero p {font-size:1.15rem;max-width:610px;color:white;}
.eyebrow {font-weight:800;letter-spacing:.12em;font-size:.8rem;text-transform:uppercase}
.section-intro {font-size:1.08rem;color:#5D4B52;margin-top:-10px;margin-bottom:15px;}
.pill {display:inline-block;background:#FFCC33;color:#111827;padding:8px 15px;border-radius:999px;font-weight:800;font-size:.85rem;}
.venue {background:white;border:1px solid #F4D7CE;border-radius:18px;padding:18px 20px;margin:10px 0;box-shadow:0 4px 14px #39210e08;}
.venue h4 {margin:0 0 5px;font-weight:800;font-size:1.1rem;color:#111827}
.venue p {margin:0;color:#655864;font-size:.91rem}
div.stButton > button[kind='primary'] {background:#F53147;color:white;border:0;border-radius:999px;font-weight:800;padding:.65rem 1.45rem;}
div.stButton > button {border-radius:999px;}
[data-testid='stMetric'] {background:#fff;border:1px solid #F4D7CE;border-radius:17px;padding:16px;}
[data-baseweb='select'] > div, [data-testid='stNumberInput'] input {border-radius:12px;}
footer {visibility:hidden;}
@media(max-width:700px) {.hero{padding:32px 23px}}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_places(path: str):
    df = pd.read_csv(path)
    required = {"name", "fclass", "activity_category", "latitude", "longitude", "distance_km"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
    df = df.dropna(subset=list(required)).copy()
    for col in ["distance_km", "latitude", "longitude"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["distance_km", "latitude", "longitude"])

@st.cache_resource
def load_ml_model(path: str):
    # Only load model files you generated yourself and trust.
    return joblib.load(path)

def interest_scores(friend):
    scores = {category: 0 for category in CATEGORIES}
    for category in friend["interests"]:
        if category in scores:
            scores[category] += 3
    vibe = friend["vibe"].lower()
    for category, terms in KEYWORDS.items():
        if any(term in vibe for term in terms):
            scores[category] += 2
    return scores

if LOGO.exists():
    st.image(str(LOGO), width=220)
else:
    st.markdown("### 🥭 TheMove")

st.markdown('''<div class="hero"><span class="eyebrow">GOOD PLANS. BETTER MEMORIES.</span><h1>So… what's the move?</h1><p>The group chat is indecisive again. Tell us what your crew likes and discover real places around Little Rock.</p><span class="pill">🥭 Plan together · everyone gets a say</span></div>''', unsafe_allow_html=True)

if not CSV.exists():
    st.error("Venue CSV missing. Place `themove_little_rock_places.csv` next to `app.py`.")
    st.stop()
try:
    places = load_places(str(CSV))
except Exception as exc:
    st.error(f"Unable to read venue catalog: {exc}")
    st.stop()

st.subheader("01 / Assemble your crew 👯")
st.markdown('<div class="section-intro">Different tastes? Different budgets? No problem. Add what each friend is into, and we’ll find common ground.</div>', unsafe_allow_html=True)
left, right = st.columns(2)
with left:
    group_size = st.number_input("How many friends are going?", min_value=2, max_value=5, value=3, step=1)
with right:
    location = st.text_input("Where are we making moves?", value="Little Rock, AR", placeholder="Enter your city", key="group_location")

supported_locations = {"little rock", "little rock, ar", "little rock, arkansas"}
location_supported = location.strip().lower() in supported_locations
if not location_supported:
    st.warning("TheMove currently supports Little Rock, Arkansas. Recommendations for other cities are not available yet.")

friends = []
for i in range(int(group_size)):
    with st.expander(f"Friend {i + 1} · budget & vibe", expanded=True):
        a, b = st.columns([2, 1])
        with a:
            name = st.text_input("Name or nickname", value=f"Friend {i + 1}", key=f"friend_name_{i}")
        with b:
            budget = st.number_input("My maximum budget ($)", min_value=0, max_value=500, value=20, step=5, key=f"friend_budget_{i}")
        vibe = st.text_input("What are you in the mood for?", placeholder="e.g. a chill café, outdoor fun, comedy...", key=f"friend_vibe_{i}")
        interests = st.multiselect("Activity types you'd be open to", options=CATEGORIES, default=[], key=f"friend_interests_{i}", placeholder="Choose any that sound fun (optional)")
        friends.append({"name": name.strip() or f"Friend {i + 1}", "budget": int(budget), "vibe": vibe.strip(), "interests": interests})

st.markdown("---")
st.subheader("02 / Find your move")
method = st.radio("How should we balance the group's preferences?", ["Include everyone", "Most popular across the crew"], horizontal=True)

if st.button("🥭 Find our move", type="primary", use_container_width=True, disabled=not location_supported):
    st.session_state["plan_friends"] = friends
    st.session_state["plan_method"] = method
    st.session_state["plan_location"] = location.strip().lower()

if "plan_friends" in st.session_state and location_supported and st.session_state.get("plan_location") == location.strip().lower():
    current_friends = st.session_state["plan_friends"]
    current_method = st.session_state["plan_method"]
    spending_limit = min(p["budget"] for p in current_friends)
    st.markdown("### Here's the move for your crew")
    st.markdown(f"**Shared budget ceiling:** ${spending_limit} per person (lowest individual budget, assuming everyone pays for themselves).")
    st.warning("Prices are unverified. This budget is a planning constraint, not an affordability filter. Check prices before going.")

    scored = [interest_scores(friend) for friend in current_friends]
    if not any(any(values.values()) for values in scored):
        st.info("Enter at least one friend's vibe or select an activity type, then click Find our move again.")
    else:
        rows = []
        for category in CATEGORIES:
            values = [s[category] for s in scored]
            rows.append({"category": category, "people_interested": sum(v > 0 for v in values), "total_score": sum(values), "least_score": min(values)})
        ranked = pd.DataFrame(rows)
        ranked = ranked[ranked["total_score"] > 0].copy()
        if current_method == "Include everyone":
            ranked = ranked.sort_values(["people_interested", "least_score", "total_score", "category"], ascending=[False, False, False, True])
        else:
            ranked = ranked.sort_values(["total_score", "people_interested", "category"], ascending=[False, False, True])
        st.caption("Local activity ranking uses selected interests and keyword matching—not the research Random Forest model.")
        for rank, row in enumerate(ranked.head(3).itertuples(), start=1):
            category = row.category
            label = " — TOP MATCH" if rank == 1 else ""
            st.markdown(f"#### {rank}. {EMOJI[category]} {category}{label}")
            st.write(f"Matches **{row.people_interested} of {len(current_friends)}** friends based on their entered interests and moods.")
            matches = places[(places["activity_category"] == category) & (places["distance_km"] <= 15)].sort_values(["distance_km", "name"]).head(3)
            if matches.empty:
                st.caption("No named places in this category in the current 15 km catalog radius.")
            else:
                for _, place in matches.iterrows():
                    name = html.escape(str(place["name"]))
                    kind = html.escape(str(place["fclass"]).replace("_", " ").title())
                    st.markdown(f'<div class="venue"><h4>📍 {name}</h4><p>{kind} · {place["distance_km"]:.1f} km from central Little Rock · Price unverified</p></div>', unsafe_allow_html=True)
                    lat, lon = float(place["latitude"]), float(place["longitude"])
                    st.link_button(f"Directions to {str(place['name'])}", f"https://www.google.com/maps/dir/?api=1&destination={lat}%2C{lon}")
        selected_categories = ranked.head(3)["category"].tolist()
        mapped = places[(places["activity_category"].isin(selected_categories)) & (places["distance_km"] <= 15)]
        if not mapped.empty:
            st.markdown("#### Places on the map 🗺️")
            st.map(mapped.head(100), latitude="latitude", longitude="longitude")
        with st.expander("Why these suggestions?"):
            st.write("Selected interests have higher weight than keywords in mood descriptions. For 'Include everyone', the ranking favors categories matched by more friends; the other option prioritizes the combined score.")
            st.write("This live venue matching is rule-based. The trained Random Forest predicts ratings of anonymous research destinations (D1–D10), not Arkansas venues.")
        st.info("Venue names and coordinates come from historical OpenStreetMap-derived data. Prices, hours, accessibility and operating status have not been verified. Distances are from downtown, not travel time.")

st.markdown("---")
with st.expander("For the professor · Try our trained Random Forest model"):
    st.write("This is a separate research demonstration. It predicts ratings for anonymous items D1–D10 from the original study. These predictions do not represent local venue quality or affordability.")
    if not MODEL_PATH.exists():
        st.warning("Model file not found at `TheMove_Frontend/models/themove_rf_model.joblib`.")
    else:
        try:
            model = load_ml_model(str(MODEL_PATH))
            model_info = json.loads(MODEL_INFO_PATH.read_text(encoding="utf-8")) if MODEL_INFO_PATH.exists() else {}
            expected = model_info.get("model_features", ["item", "opn", "cns", "ext", "agr", "est", "experience"])
            required = ["item", "opn", "cns", "ext", "agr", "est", "experience"]
            if set(expected) != set(required):
                st.error(f"The exported model expects different features: {expected}. Check the notebook metadata before using this demo.")
            else:
                st.success("Trained Random Forest loaded successfully.")
                st.caption("Personality-profile numbers below are example research inputs, not the friends' budgets or mood text. Use values appropriate to the training dataset's scales.")
                with st.form("research_prediction_form"):
                    item = st.selectbox("Research destination", [f"D{i}" for i in range(1, 11)])
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        opn = st.number_input("Openness (opn)", value=3.0, step=0.1)
                        cns = st.number_input("Conscientiousness (cns)", value=3.0, step=0.1)
                    with c2:
                        ext = st.number_input("Extraversion (ext)", value=3.0, step=0.1)
                        agr = st.number_input("Agreeableness (agr)", value=3.0, step=0.1)
                    with c3:
                        est = st.number_input("Emotional stability (est)", value=3.0, step=0.1)
                        experience = st.number_input("Experience", value=3.0, step=0.1)
                    predict_clicked = st.form_submit_button("Predict research rating")
                if predict_clicked:
                    data = {"item": item, "opn": opn, "cns": cns, "ext": ext, "agr": agr, "est": est, "experience": experience}
                    features = pd.DataFrame([data], columns=expected)
                    try:
                        predicted = float(model.predict(features)[0])
                        st.metric("Predicted research rating", f"{predicted:.2f}")
                        st.caption("This is a research-item rating prediction, not a live Little Rock venue recommendation.")
                    except Exception as exc:
                        st.error(f"Prediction failed: {exc}. Check that item labels and feature scales match the training notebook.")
        except Exception as exc:
            st.error(f"Unable to load Random Forest: {exc}")
            st.caption("Ensure your Streamlit environment uses compatible scikit-learn, joblib, pandas and NumPy versions.")

with st.expander("For the professor · Research evaluation results"):
    st.write("The research compared popularity, user-based KNN and Random Forest. On the group-aware held-out test (12 groups), popularity matched 5 of 12 recorded first choices (41.67%), while Random Forest average and minimum each matched 3 of 12 (25%).")
    st.caption("These results are for anonymous research items. They do not measure accuracy of the local Little Rock venue suggestions. A generative conversational assistant is not yet integrated.")
