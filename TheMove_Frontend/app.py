"""TheMove — branded Little Rock activity finder.

Local venue matching is rule-based and distinct from the research ML models.
Data: a separately generated OSM-based CSV; no real-time venue verification.
"""
from pathlib import Path
import html
import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parent
CSV = BASE / "themove_little_rock_places.csv"
LOGO = BASE / "assets" / "logo_horizontal.png"
ICON = BASE / "assets" / "app_icon.png"
CATEGORIES = ["Food & Drinks", "Outdoor & Nature", "Arts & Culture", "Entertainment", "Sports & Recreation"]
EMOJI = {"Food & Drinks":"🍜", "Outdoor & Nature":"🌳", "Arts & Culture":"🎨", "Entertainment":"🎭", "Sports & Recreation":"🏀"}

st.set_page_config(page_title="TheMove | What's the move?", page_icon=str(ICON) if ICON.exists() else "🥭", layout="wide", initial_sidebar_state="collapsed")
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
.hero:after {content:'✳';position:absolute;right:35px;top:8px;font-size:140px;color:#FFCC33;opacity:.85;transform:rotate(12deg)}
.hero h1 {font-size:clamp(2.5rem,5vw,4.8rem);line-height:1.03;letter-spacing:-.06em;color:white!important;max-width:730px;margin:12px 0;position:relative;z-index:1}
.hero p {font-size:1.15rem;max-width:610px;color:white;position:relative;z-index:1}
.eyebrow {font-weight:800;letter-spacing:.12em;font-size:.8rem;text-transform:uppercase}
.section-intro {font-size:1.08rem;color:#5D4B52;margin-top:-10px;margin-bottom:15px;}
.pill {display:inline-block;background:#FFCC33;color:#111827;padding:8px 15px;border-radius:999px;font-weight:800;font-size:.85rem;}
.venue {background:white;border:1px solid #F4D7CE;border-radius:18px;padding:18px 20px;margin:10px 0;box-shadow:0 4px 14px #39210e08;}
.venue h4 {margin:0 0 5px;font-weight:800;font-size:1.1rem;color:#111827}
.venue p {margin:0;color:#655864;font-size:.91rem}
.small-note {font-size:.85rem;color:#6B5960;}
div.stButton > button[kind='primary'] {background:#F53147;color:white;border:0;border-radius:999px;font-weight:800;padding:.65rem 1.45rem;}
div.stButton > button {border-radius:999px;}
[data-testid='stMetric'] {background:#fff;border:1px solid #F4D7CE;border-radius:17px;padding:16px;}
[data-baseweb='select'] > div, [data-testid='stNumberInput'] input {border-radius:12px;}
footer {visibility:hidden;}
@media(max-width:700px) {.hero{padding:32px 23px}.hero:after{font-size:75px;right:0;top:4px;opacity:.35}}
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
    df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce")
    df = df.dropna(subset=["distance_km"])
    return df

if LOGO.exists():
    st.image(str(LOGO), width=220)
else:
    st.markdown("### 🥭 TheMove")
st.markdown('''<div class="hero"><span class="eyebrow">GOOD PLANS. BETTER MEMORIES.</span><h1>So… what's the move?</h1><p>The group chat is indecisive again. Tell us what your crew likes and discover real places around Little Rock.</p><span class="pill">🥭 Plan together · everyone gets a say</span></div>''', unsafe_allow_html=True)

if not CSV.exists():
    st.error("Venue CSV missing. Upload `themove_little_rock_places.csv` to the same GitHub folder as `app.py`, then redeploy.")
    st.stop()
try:
    places = load_places(str(CSV))
except Exception as exc:
    st.error(f"Unable to read venue catalog: {exc}")
    st.stop()

st.subheader("01 / Assemble your crew 👯")
st.markdown('<div class="section-intro">Different tastes? Different budgets? No problem. Add what each friend is into, and we’ll find common ground.</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    group_size = st.number_input("How many friends are going?", min_value=2, max_value=5, value=3, step=1)

with col2:
    location = st.text_input(
        "Where are we making moves?",
        value="Little Rock, AR",
        placeholder="Enter your city",
        key="group_location"
    )

# The current dataset only covers central Little Rock
max_distance = 15


# Only Little Rock is currently supported
supported_locations = {
    "little rock",
    "little rock, ar",
    "little rock, arkansas"
}

if location.strip().lower() not in supported_locations:
    st.warning(
        "TheMove currently supports Little Rock, Arkansas. "
        "Recommendations for other cities are not available yet."
    )
    st.stop()


friends = []
for i in range(int(group_size)):
    with st.expander(f"Friend {i+1} · budget & vibe", expanded=True):
        left, right = st.columns([2, 1])
        with left:
            name = st.text_input("Name or nickname", value=f"Friend {i+1}", key=f"friend_name_{i}")
        with right:
            budget = st.number_input("My maximum budget ($)", min_value=0, max_value=500, value=20, step=5, key=f"friend_budget_{i}")
        vibe = st.text_input("What are you in the mood for?", placeholder="e.g. a chill café, outdoor fun, comedy...", key=f"friend_vibe_{i}")
        interests = st.multiselect(
            "Activity types you'd be open to",
            options=CATEGORIES,
            default=[],
            key=f"friend_interests_{i}",
            placeholder="Choose any that sound fun (optional)"
        )
        friends.append({"name": name.strip() or f"Friend {i+1}", "budget": int(budget), "vibe": vibe.strip(), "interests": interests})

st.markdown("---")
st.subheader("02 / Find your move")
method = st.radio("How should we balance the group's preferences?", ["Include everyone", "Most popular across the crew"], horizontal=True)

# Transparent, editable keyword hints for translating casual descriptions to broad categories.
# This is not a language model, nor is it a trained classifier.
KEYWORDS = {
    "Food & Drinks": ["food", "eat", "dinner", "lunch", "brunch", "restaurant", "cafe", "coffee", "drink", "snack", "chill", "catch up"],
    "Outdoor & Nature": ["outside", "outdoor", "nature", "park", "hike", "walk", "picnic", "relax", "scenic"],
    "Arts & Culture": ["art", "museum", "history", "culture", "gallery", "creative"],
    "Entertainment": ["fun", "comedy", "movie", "cinema", "show", "nightlife", "music", "theatre", "dance", "party"],
    "Sports & Recreation": ["sports", "sport", "active", "fitness", "basketball", "swim", "play", "game", "adventure"],
}

def interest_scores(friend):
    # Explicit interests count more than basic word matches.
    scores = {category: 0 for category in CATEGORIES}
    for category in friend["interests"]:
        scores[category] += 3
    lower = friend["vibe"].lower()
    for category, words in KEYWORDS.items():
        if any(word in lower for word in words):
            scores[category] += 2
    return scores

submit = st.button("🥭 Find our move", type="primary", use_container_width=True)
if submit:
    st.session_state["plan_friends"] = friends
    st.session_state["plan_distance"] = max_distance
    st.session_state["plan_method"] = method

if "plan_friends" in st.session_state:
    current_friends = st.session_state["plan_friends"]
    current_distance = st.session_state["plan_distance"]
    current_method = st.session_state["plan_method"]
    spending_limit = min(person["budget"] for person in current_friends)
    st.markdown(f"### Here's the move for your crew ")
    st.markdown(f"**Shared budget ceiling:** ${spending_limit} per person (the lowest individual budget, assuming everyone pays for themselves).")
    st.warning("Our venue catalog has no verified prices. Budget is shown as a planning constraint, but places are **not** filtered or certified as affordable. Check prices before going.")

    scored = [interest_scores(friend) for friend in current_friends]
    any_signals = any(any(values.values()) for values in scored)
    if not any_signals:
        st.info("We need a little more direction. Tell us at least one friend's vibe or choose an activity type, then click Find our move again.")
    else:
        rows=[]
        for category in CATEGORIES:
            scores = [values[category] for values in scored]
            rows.append({"category":category, "people_interested":sum(score>0 for score in scores), "total_score":sum(scores), "least_score":min(scores)})
        ranked = pd.DataFrame(rows)
        ranked = ranked[ranked["total_score"]>0].copy()
        if current_method == "Include everyone":
            ranked = ranked.sort_values(["people_interested","least_score","total_score","category"],ascending=[False,False,False,True])
        else:
            ranked = ranked.sort_values(["total_score","people_interested","category"],ascending=[False,False,True])
        st.caption("Activity ranking uses explicitly selected categories and simple text-keyword matching, not the research ML model.")
        for rank, r in enumerate(ranked.head(3).itertuples(), start=1):
            category = r.category
            matches = places[(places["activity_category"]==category)&(places["distance_km"]<=current_distance)].copy()
            matches = matches.sort_values(["distance_km","name"]).head(3)
            st.markdown(f"#### {rank}. {EMOJI[category]} {category}")
            st.write(f"Matches the interests of **{r.people_interested} of {len(current_friends)}** friends, based on the information entered.")
            if matches.empty:
                st.caption("No named places in this category within the selected distance. Try a larger radius.")
            else:
                for _, place in matches.iterrows():
                    name = html.escape(str(place["name"])); kind=html.escape(str(place["fclass"]).replace("_"," ").title())
                    st.markdown(f'<div class="venue"><h4>📍 {name}</h4><p>{kind} · {place["distance_km"]:.1f} km from central Little Rock · Price unverified</p></div>',unsafe_allow_html=True)
        top_categories = ranked.head(3)["category"].tolist()
        mapped = places[(places["activity_category"].isin(top_categories)) & (places["distance_km"]<=current_distance)].copy()
        if not mapped.empty:
            st.markdown("#### Places on the map 🗺️")
            st.map(mapped.head(100), latitude="latitude", longitude="longitude")
        with st.expander("Why these suggestions? / What's ML here?"):
            st.write("We compare each person's chosen categories and the keywords in their mood descriptions. We then prioritize activity categories that fit the group's inputs, and show named venues nearby. Everyone's individual budget is recorded; the lowest budget provides a suggested group spending ceiling, but we do not have confirmed venue prices.")
            st.write("This live Little Rock recommendation feature is rule-based. Our separately evaluated ML experiment predicts ratings for anonymous tourism destinations (D1–D10). It cannot legitimately score these Arkansas venues without further training data and validation.")
        st.info("Venues originate from historical OpenStreetMap-derived data. Prices, hours, accessibility, operation, and availability are unverified. Distances are approximate from downtown, not travel time.")

with st.expander("For the professor · ML research evidence"):
    st.write("The research compared a popularity baseline, user-based KNN, and Random Forest rating prediction. In the held-out group-aware test (12 groups), the popularity approach matched 41.67% of recorded top choices, while RF average and RF minimum each matched 25%. This local venue screen is a separate category-matching prototype; an integrated, validated AI explanation feature remains to be built.")
    st.caption("Results are from a small historical research dataset. Do not interpret them as effectiveness metrics for local venues.")
