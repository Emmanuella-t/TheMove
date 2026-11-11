"""TheMove — group activity planner for Little Rock, Arkansas.

Live suggestions are transparent preference/keyword matches to OSM-derived places.
The research Random Forest is evaluated separately and is not used for venues.
"""
from pathlib import Path
import html
import re

import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parent
CSV = BASE / "themove_little_rock_places.csv"
LOGO = BASE / "assets" / "logo_horizontal.png"
ICON = BASE / "assets" / "app_icon.png"

CATEGORIES = ["Food & Drinks", "Outdoor & Nature", "Arts & Culture", "Entertainment", "Sports & Recreation"]
EMOJI = {"Food & Drinks": "🍜", "Outdoor & Nature": "🌳", "Arts & Culture": "🎨", "Entertainment": "🎭", "Sports & Recreation": "🏀"}
KEYWORDS = {
    "Food & Drinks": ["food", "eat", "dinner", "lunch", "brunch", "restaurant", "cafe", "café", "coffee", "drink", "snack", "chill", "catch up"],
    "Outdoor & Nature": ["outside", "outdoor", "nature", "park", "hike", "walk", "picnic", "relax", "scenic"],
    "Arts & Culture": ["art", "museum", "history", "culture", "gallery", "creative"],
    "Entertainment": ["fun", "comedy", "movie", "cinema", "show", "nightlife", "music", "theatre", "theater", "dance", "party"],
    "Sports & Recreation": ["sports", "sport", "active", "fitness", "basketball", "swim", "play", "game", "adventure"],
}

# Matching these strong user intents to venue types prevents recommending a
# fast-food restaurant for a café outing or a memorial for a museum visit.
SPECIFIC_REQUESTS = {
    "coffee / café": {
        "terms": ("coffee", "cafe", "café", "espresso", "latte"),
        "fclass": ("cafe", "coffee_shop", "coffeehouse", "tea_house"),
        "name": ("coffee", "cafe", "café", "espresso", "roaster"),
        "categories": ("Food & Drinks",),
    },
    "museum": {
        "terms": ("museum",),
        "fclass": ("museum",),
        "name": ("museum",),
        "categories": ("Arts & Culture",),
    },
    "art gallery": {
        "terms": ("art gallery", "gallery"),
        "fclass": ("gallery", "art_gallery"),
        "name": ("gallery",),
        "categories": ("Arts & Culture",),
    },
    "park": {
        "terms": ("park", "picnic"),
        "fclass": ("park", "garden", "nature_reserve", "recreation_ground"),
        "name": ("park", "garden"),
        "categories": ("Outdoor & Nature",),
    },
    "sports center": {
        "terms": ("basketball", "sports center", "sports centre", "recreation center", "recreation centre"),
        "fclass": ("sports_centre", "sports_center", "pitch", "stadium", "recreation_ground"),
        "name": ("recreation", "basketball", "sports"),
        "categories": ("Sports & Recreation",),
    },
}


def normalized(value):
    return re.sub(r"\s+", " ", str(value).lower().replace("_", " ").strip())


def contains_term(text, term):
    """Find whole words/phrases rather than matching 'art' inside 'party'."""
    return re.search(r"(?<!\w)" + re.escape(normalized(term)) + r"(?!\w)", normalized(text)) is not None


def interest_scores(friend):
    result = {category: 0 for category in CATEGORIES}
    for category in friend["interests"]:
        if category in result:
            result[category] += 3
    for category, terms in KEYWORDS.items():
        if any(contains_term(friend["vibe"], term) for term in terms):
            result[category] += 2
    return result


def requested_subtypes(friends, category):
    descriptions = " ".join(person["vibe"] for person in friends)
    found = []
    for label, spec in SPECIFIC_REQUESTS.items():
        if category in spec["categories"] and any(contains_term(descriptions, term) for term in spec["terms"]):
            found.append(label)
    return found


def matching_subtype(place, label):
    spec = SPECIFIC_REQUESTS[label]
    kind = normalized(place["fclass"])
    name = normalized(place["name"])
    return any(contains_term(kind, term) for term in spec["fclass"]) or any(
        contains_term(name, term) for term in spec["name"]
    )


def select_venues(places, category, friends, radius_km=15, limit=3):
    """Rank local catalog places by specific requested subtype, then distance.

    If specific subtypes are explicitly requested, do not present unrelated
    venues from the broad category as equivalent. Empty results are honest.
    """
    candidates = places.loc[
        (places["activity_category"] == category) & (places["distance_km"] <= radius_km)
    ].copy()
    subtypes = requested_subtypes(friends, category)
    if subtypes:
        candidates["specific_fit"] = candidates.apply(
            lambda place: sum(matching_subtype(place, label) for label in subtypes), axis=1
        )
        candidates = candidates[candidates["specific_fit"] > 0]
        candidates = candidates.sort_values(["specific_fit", "distance_km", "name"], ascending=[False, True, True])
    else:
        candidates = candidates.sort_values(["distance_km", "name"])
    return candidates.head(limit), subtypes


@st.cache_data
def load_places(path):
    df = pd.read_csv(path)
    required = {"name", "fclass", "activity_category", "latitude", "longitude", "distance_km"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
    df = df.dropna(subset=list(required)).copy()
    for field in ["distance_km", "latitude", "longitude"]:
        df[field] = pd.to_numeric(df[field], errors="coerce")
    return df.dropna(subset=["distance_km", "latitude", "longitude"])


def rank_categories(friends, method):
    scores = [interest_scores(friend) for friend in friends]
    rows = []
    for category in CATEGORIES:
        values = [person[category] for person in scores]
        rows.append({
            "category": category,
            "people_interested": sum(value > 0 for value in values),
            "total_score": sum(values),
            "least_score": min(values),
        })
    ranked = pd.DataFrame(rows)
    ranked = ranked[ranked["total_score"] > 0]
    if method == "Include everyone":
        return ranked.sort_values(
            ["people_interested", "least_score", "total_score", "category"],
            ascending=[False, False, False, True],
        )
    return ranked.sort_values(
        ["total_score", "people_interested", "category"],
        ascending=[False, False, True],
    )


def discovery_categories(places, radius_km=15):
    """Offer distinct available categories if no one knows what to do."""
    pool = places.loc[places["distance_km"] <= radius_km]
    preference = ["Outdoor & Nature", "Food & Drinks", "Arts & Culture", "Entertainment", "Sports & Recreation"]
    available = [category for category in preference if (pool["activity_category"] == category).any()]
    return available[:3]


def venue_card(place):
    name = str(place["name"])
    safe_name = html.escape(name)
    kind = html.escape(str(place["fclass"]).replace("_", " ").title())
    distance = float(place["distance_km"])
    st.markdown(
        f'<div class="venue"><h4>📍 {safe_name}</h4>'
        f'<p>{kind} · {distance:.1f} km from central Little Rock · Price unverified</p></div>',
        unsafe_allow_html=True,
    )
    lat, lon = float(place["latitude"]), float(place["longitude"])
    st.link_button(
        f"Directions to {name}",
        f"https://www.google.com/maps/dir/?api=1&destination={lat}%2C{lon}",
    )


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

st.subheader("Assemble your crew 👯")
st.markdown('<div class="section-intro">Different tastes? Different budgets? No problem. Add what each friend is into, and we’ll find common ground.</div>', unsafe_allow_html=True)
left, right = st.columns(2)
with left:
    group_size = st.number_input("How many friends are going?", min_value=2, max_value=5, value=3, step=1)
with right:
    location = st.text_input("Where are we making moves?", value="Little Rock, AR", placeholder="Enter your city", key="group_location")

supported_locations = {"little rock", "little rock, ar", "little rock, arkansas"}
location_supported = location.strip().lower() in supported_locations
if not location_supported:
    st.warning("TheMove currently supports Little Rock, Arkansas. We won't show you Little Rock places as though they're in another city.")

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
st.subheader("Find your move")
method = st.radio("How should we balance the group's preferences?", ["Include everyone", "Most popular across the crew"], horizontal=True)
discover_anyway = st.checkbox("🎲 Surprise us — give us ideas even if we don't know what we want", value=False)

if st.button("🥭 Find our move", type="primary", use_container_width=True, disabled=not location_supported):
    st.session_state["plan_friends"] = [dict(p) for p in friends]
    st.session_state["plan_method"] = method
    st.session_state["plan_surprise"] = discover_anyway
    st.session_state["plan_location"] = location.strip().lower()

if "plan_friends" in st.session_state and location_supported and st.session_state.get("plan_location") == location.strip().lower():
    current_friends = st.session_state["plan_friends"]
    current_method = st.session_state["plan_method"]
    current_surprise = st.session_state.get("plan_surprise", False)
    spending_limit = min(p["budget"] for p in current_friends)
    st.markdown("### Here's the move for your crew")
    st.markdown(f"**Shared budget ceiling:** ${spending_limit} per person (lowest individual budget, assuming everyone pays for themselves).")
    st.warning("Venue prices are unverified. The budget is a planning constraint, not an affordability filter. Check admission, menu prices and transport costs before going.")
    if spending_limit == 0:
        st.info("Someone has a $0 budget. These places are discovery ideas only; none is verified as free. Consider a free activity once its cost is confirmed.")

    ranked = rank_categories(current_friends, current_method)
    no_preferences = ranked.empty
    if no_preferences or current_surprise:
        categories = discovery_categories(places)
        st.info("**No plans? No problem!** Here are different ideas to get the group talking. These are exploratory picks, not personalized or budget-verified predictions.")
        display_rows = [{"category": category, "people_interested": 0} for category in categories]
    else:
        display_rows = ranked.head(3).to_dict("records")
        maximum_coverage = int(ranked["people_interested"].max())
        if maximum_coverage < len(current_friends):
            st.info(
                f"**Not everyone agrees yet.** The strongest category matches {maximum_coverage} of "
                f"{len(current_friends)} friends. These are conversation starters, not a group-wide consensus. "
                "Ask everyone which other activity they would also try, then update their choices."
            )
        if current_method == "Include everyone":
            st.caption("'Include everyone' ranks activities by how many friends expressed interest, then their lowest and combined scores. It cannot invent agreement when none exists.")
        else:
            st.caption("'Most popular across the crew' ranks activities by combined preference score. It may leave some friends out.")
    st.caption("Local recommendations use explicit selections and keyword rules, not the research Random Forest model.")

    # Produce three ACTUAL venue options, not three groups of venue cards.
    # A single best-supported option is featured, followed by two alternatives.
    # We do not claim statistical confidence, verified affordability, or unanimous agreement.
    discovery = no_preferences or current_surprise
    suggestions = []
    selected_ids = set()
    unavailable = []

    def append_options(category, limit):
        picks, requested = select_venues(
            places, category, [] if discovery else current_friends,
            limit=max(limit + 3, 6),
        )
        if picks.empty and requested:
            unavailable.append(f"{category}: {', '.join(requested)}")
        for _, place in picks.iterrows():
            # Prevent the same venue from appearing twice if catalogs overlap.
            venue_id = str(place.get("osm_id", "")) or (
                str(place["name"]), float(place["latitude"]), float(place["longitude"])
            )
            if venue_id in selected_ids:
                continue
            selected_ids.add(venue_id)
            suggestions.append({"place": place, "category": category,
                                "matched": 0 if discovery else int(coverage.get(category, 0)),
                                "requested": requested})
            if len(suggestions) >= limit:
                break

    coverage = {row["category"]: int(row["people_interested"]) for row in display_rows}
    for row in display_rows:
        if len(suggestions) >= 3:
            break
        append_options(row["category"], 1)

    # Prefer extra distinct places from the best-ranked requested category over
    # unrelated categories, while retaining any specific-subtype filtering.
    if len(suggestions) < 3 and not discovery and display_rows:
        first_category = display_rows[0]["category"]
        append_options(first_category, 3)

    # If preferences produce fewer than three available places, fill from other
    # venue types while labeling those additions as exploratory alternatives.
    if len(suggestions) < 3:
        for category in CATEGORIES:
            if len(suggestions) >= 3:
                break
            if category in coverage:
                continue
            extra, _ = select_venues(places, category, [], limit=5)
            for _, place in extra.iterrows():
                venue_id = str(place.get("osm_id", "")) or (
                    str(place["name"]), float(place["latitude"]), float(place["longitude"])
                )
                if venue_id in selected_ids:
                    continue
                selected_ids.add(venue_id)
                suggestions.append({"place": place, "category": category,
                                    "matched": 0, "requested": [], "exploratory": True})
                if len(suggestions) >= 3:
                    break

    if unavailable:
        st.warning("We couldn't find an exact local match for " + "; ".join(unavailable) + ". We won't label unrelated venues as exact matches.")

    if suggestions:
        st.markdown("### TheMove's Top Pick")
        top = suggestions[0]
        top_category = top["category"]
        top_match = top["matched"]
        top_name = str(top["place"]["name"])
        if discovery:
            reason = "A starting idea selected from the available local venue catalog—not a personalized prediction."
        elif top_match == len(current_friends):
            reason = f"Best-ranked available activity type, matching all {len(current_friends)} friends' expressed interests."
        elif top_match > 0:
            reason = (f"Highest-ranked available activity type, matching {top_match} of "
                      f"{len(current_friends)} friends. Not everyone agreed, so check with the crew first.")
        else:
            reason = "An exploratory alternative; no friend explicitly requested this activity type."
        st.markdown(f"**{EMOJI[top_category]} {html.escape(top_name)}** · {top_category}")
        st.write("**Why this one?** " + reason)
        venue_card(top["place"])

        if len(suggestions) > 1:
            st.markdown("### Two other ideas")
            for i, choice in enumerate(suggestions[1:], start=2):
                category = choice["category"]
                st.markdown(f"#### Option {i} · {EMOJI[category]} {category}")
                if discovery or choice.get("exploratory", False):
                    st.caption("Exploratory alternative; preference match not established.")
                else:
                    st.caption(f"Matches {choice['matched']} of {len(current_friends)} friends' expressed interests.")
                venue_card(choice["place"])
        st.caption("Exactly one top pick is highlighted. Rankings use transparent preference and venue rules, not the trained research Random Forest model.")
        st.markdown("#### Your three places on the map 🗺️")
        st.map(pd.DataFrame([choice["place"] for choice in suggestions]), latitude="latitude", longitude="longitude")
    else:
        st.info("There are no eligible venues in this 15 km catalog radius for these inputs.")

    with st.expander("Why these suggestions?"):
        st.write("Selected activity interests receive more weight than keywords in mood descriptions. The two group strategies use different sorting priorities. If no shared preference exists, we show that uncertainty rather than claiming a unanimous top choice.")
        st.write("When someone requests a specific venue type (such as a café, museum or gallery), results are filtered to matching names or mapped venue types. If that type is absent from the local catalog, we say so.")
        st.write("Surprise Us offers diverse catalog categories without assuming what people like. The research ML model predicts ratings of anonymous study destinations (D1–D10) and is not used to score local businesses.")
    st.info("Places come from historical OpenStreetMap-derived data. Prices, hours, accessibility and current operating status are not verified. Distances are approximate from downtown, not travel time.")
