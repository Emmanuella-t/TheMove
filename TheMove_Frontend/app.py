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
st.markdown('''<div class="hero"><span class="eyebrow">GOOD PLANS. BETTER MEMORIES.</span><h1>So… what's the move?</h1><p>The group chat is indecisive again. Tell us what your crew likes and discover real places around Little Rock.</p><span class="pill">🥭 Let's make a plan</span></div>''', unsafe_allow_html=True)

if not CSV.exists():
    st.error("Venue CSV missing. Upload `themove_little_rock_places.csv` to the same GitHub folder as `app.py`, then redeploy.")
    st.stop()
try:
    places = load_places(str(CSV))
except Exception as exc:
    st.error(f"Unable to read venue catalog: {exc}")
    st.stop()

st.subheader("01 / Assemble your crew 👯")
st.markdown('<div class="section-intro">Everyone gets a say. Rate how much each person would enjoy these activity types.</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    group_size = st.number_input("How many friends?", min_value=2, max_value=5, value=3, step=1)
with c2:
    max_distance = st.slider("Max distance from downtown (km)", min_value=1, max_value=15, value=10)
with c3:
    preference_method = st.selectbox("How should we decide?", ["Make sure everyone's included", "Highest group average"])

st.caption("0 = no interest · 1 = maybe · 2 = sounds good · 3 = love it")
ratings = []
for i in range(int(group_size)):
    with st.expander(f"Friend {i+1} · activity preferences", expanded=(i == 0)):
        name = st.text_input("Nickname (optional)", value=f"Friend {i+1}", key=f"name{i}")
        cols = st.columns(3)
        entry = {"friend": name.strip() or f"Friend {i+1}"}
        for j, cat in enumerate(CATEGORIES):
            with cols[j % 3]:
                entry[cat] = st.select_slider(f"{EMOJI[cat]} {cat}", options=[0,1,2,3], value=2, key=f"pref{i}_{j}")
        ratings.append(entry)

st.markdown("---")
st.subheader("02 / Find your move ✨")
show = st.button("Find our move", type="primary", use_container_width=True)
if show:
    st.session_state["show_moves"] = True
if st.session_state.get("show_moves", False):
    pref = pd.DataFrame(ratings)
    scores = []
    for cat in CATEGORIES:
        vals = pref[cat]
        scores.append({"category":cat,"min_score":int(vals.min()),"avg_score":float(vals.mean())})
    ranked = pd.DataFrame(scores)
    if preference_method == "Make sure everyone's included":
        ranked = ranked.sort_values(["min_score","avg_score","category"], ascending=[False,False,True])
        method_note = "ranked by the least-interested friend first, then group average"
    else:
        ranked = ranked.sort_values(["avg_score","min_score","category"], ascending=[False,False,True])
        method_note = "ranked by group average first, then the least-interested friend"
    st.markdown(f"**Your group's top vibes** — {method_note}.")
    top = ranked.head(3)
    st.markdown(" · ".join(f"**{EMOJI[r.category]} {r.category}**" for r in top.itertuples()))
    candidates = places[(places["activity_category"].isin(top["category"])) & (places["distance_km"] <= max_distance)].copy()
    rank_lookup = {cat:i for i,cat in enumerate(top["category"])}
    candidates["category_rank"] = candidates["activity_category"].map(rank_lookup)
    candidates = candidates.sort_values(["category_rank","distance_km","name"])
    if candidates.empty:
        st.warning("No matching places in the catalog for this distance. Try a wider radius or different interests.")
    else:
        st.success(f"Found {len(candidates)} matching venues in the selected categories.")
        st.markdown("#### Real spots to check out")
        for _, row in candidates.head(9).iterrows():
            name = html.escape(str(row["name"])); cat = html.escape(str(row["activity_category"])); kind=html.escape(str(row["fclass"]).replace('_',' ').title())
            st.markdown(f'<div class="venue"><h4>{EMOJI.get(row["activity_category"],"📍")} {name}</h4><p>{cat} · {kind} · {row["distance_km"]:.1f} km from downtown</p></div>',unsafe_allow_html=True)
        st.markdown("#### Where's the move? 📍")
        st.map(candidates.head(100),latitude="latitude",longitude="longitude")
        with st.expander("Why these recommendations? / How it works"):
            st.write("Your friends' ratings determine the highest-ranked activity categories. Venues within those categories are then ordered by approximate distance from central Little Rock. This local matching is a transparent rule-based feature, **not** a prediction from our tourism ML model.")
            st.write("The original research model was evaluated separately on anonymous tourism destinations D1–D10. It has not been trained on these Arkansas venues.")
    st.info("Venue listings come from a downloaded OpenStreetMap-derived dataset. Hours, admission fees, accessibility, current operation and availability have not been verified. Distances are straight-line estimates from downtown, not driving times.")

with st.expander("For the professor · ML research evidence"):
    st.write("The research compared a popularity baseline, user-based KNN, and Random Forest rating prediction. In the held-out group-aware test (12 groups), the popularity approach matched 41.67% of recorded top choices, while RF average and RF minimum each matched 25%. This local venue screen is a separate category-matching prototype; an integrated, validated AI explanation feature remains to be built.")
    st.caption("Results are from a small historical research dataset. Do not interpret them as effectiveness metrics for local venues.")
