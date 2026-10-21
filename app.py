from pathlib import Path
from itertools import combinations, product
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Fiber Intake Explorer", page_icon="🥦", layout="wide")
DATA = Path(__file__).resolve().parent / "data" / "fiber_data_recommendation.csv"

@st.cache_data
def load_data():
    cols = ["Food_Code", "Food_Description_EN", "category", "fiber_per_100g", "calories_per_100g", "recommendation_eligible", "is_common_example", "practicality_penalty", "food_form"]
    df = pd.read_csv(DATA, usecols=cols)
    for col in ("fiber_per_100g", "calories_per_100g"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["Food_Code", "Food_Description_EN", "category", "fiber_per_100g", "calories_per_100g"]).query("fiber_per_100g > 0 and calories_per_100g >= 0 and recommendation_eligible == True").drop_duplicates("Food_Code")

@st.cache_data(show_spinner=False)
def build_combos(categories, goal, weight_cap, portion_options, max_foods):
    df = load_data()
    df = df[df.category.isin(categories)]
    parts = []
    for _, group in df.groupby("category"):
        # Prioritize ordinary food forms BEFORE constructing the limited search pool.
        ranked = group.sort_values(["practicality_penalty", "fiber_per_100g"], ascending=[True, False])
        parts.extend([ranked.head(14), ranked.loc[ranked["is_common_example"]].head(8)])
    if not parts:
        return pd.DataFrame()

    pool = pd.concat(parts).drop_duplicates("Food_Code").reset_index(drop=True)
    fiber_values = pool["fiber_per_100g"].to_numpy(dtype=float) / 100
    energy_values = pool["calories_per_100g"].to_numpy(dtype=float) / 100
    portions = np.asarray(portion_options, dtype=int)
    n = len(pool)
    candidate_chunks = []

    # All distinct two-food pairs x all portion choices: batched calculations.
    pair_ids = np.asarray(list(combinations(range(n), 2)), dtype=int)
    portion_pairs = np.asarray(list(product(portions, repeat=2)), dtype=int)
    if len(pair_ids):
        ids2 = np.repeat(pair_ids, len(portion_pairs), axis=0)
        g2 = np.tile(portion_pairs, (len(pair_ids), 1))
        candidate_chunks.append((ids2, g2))

    if max_foods == 3 and n >= 3:
        # Reproducible sampled triples, evaluated simultaneously with NumPy.
        rng = np.random.default_rng(830)
        trials = 18000
        random_scores = rng.random((trials, n))
        ids3 = np.sort(np.argpartition(random_scores, kth=2, axis=1)[:, :3], axis=1)
        g3 = rng.choice(portions, size=(trials, 3))
        candidate_chunks.append((ids3, g3))

    feasible = []
    for ids, grams in candidate_chunks:
        total_weight = grams.sum(axis=1)
        total_fiber = (fiber_values[ids] * grams).sum(axis=1)
        mask = total_fiber >= goal
        if weight_cap is not None:
            mask &= total_weight <= weight_cap
        valid = np.flatnonzero(mask)
        if len(valid):
            total_energy = (energy_values[ids[valid]] * grams[valid]).sum(axis=1)
            # We only need strong candidates to construct a short list.
            order = np.lexsort((total_energy, total_fiber[valid] - goal, total_weight[valid]))
            for j in valid[order[:500]]:
                kcal = float((energy_values[ids[j]] * grams[j]).sum())
                penalty = int(pool.iloc[ids[j]]["practicality_penalty"].sum())
                feasible.append((penalty, int(total_weight[j]), float(total_fiber[j]), kcal,
                                 tuple(int(z) for z in ids[j]), tuple(int(z) for z in grams[j])))

    feasible.sort(key=lambda r: (r[0], r[1], r[2] - goal, r[3]))
    seen = set()
    output = []
    for penalty, total_g, fiber, kcal, ids, amounts in feasible:
        if ids in seen:
            continue
        seen.add(ids)
        rows = pool.iloc[list(ids)]
        description = " + ".join(f"{g} g {name}" for g, name in zip(amounts, rows.Food_Description_EN))
        output.append({"Combination": description, "Total weight (g)": total_g,
                       "Fiber (g)": round(fiber, 2), "Calories (kcal)": round(kcal, 1),
                       "Food groups": ", ".join(sorted(set(rows.category)))})
        if len(output) == 20:
            break
    return pd.DataFrame(output)

all_df = load_data()
st.title("Fiber Intake Explorer")
st.write("Enter your desired fiber intake and explore example combinations of fruits, vegetables, and legumes. Results use reference nutrient values, not personalized dietary advice.")
st.caption("Source: Health Canada, Canadian Nutrient File (CNF). Values are calculated using nutrients per 100 g of each listed food.")

with st.sidebar:
    st.header("Your preferences")
    goal = st.number_input("Desired fiber (g)", min_value=1.0, max_value=80.0, value=10.0, step=1.0)
    apply_cap = st.checkbox("Set maximum total food weight", value=False)
    cap = st.number_input("Maximum combined weight (g)", 100, 1500, 400, 50, disabled=not apply_cap)
    selected_groups = st.multiselect("Include these food groups", ["Fruit", "Vegetable", "Legume"], default=["Fruit", "Vegetable", "Legume"])
    max_foods = st.radio("Foods per combination", [2, 3], index=1, help="When 3 is chosen, recommendations may contain two or three foods.")
    show_nutrients = st.checkbox("Show complementary nutrient summary", value=False)
    st.caption("Tested portions: 50 g, 100 g, 150 g, or 200 g per food. No cost estimates are used.")

if not selected_groups:
    st.warning("Choose at least one food group to continue.")
    st.stop()

st.header("Food combinations for your fiber goal")
st.write("Choose your preferences in the sidebar. Each recommendation contains two or three distinct food entries, with the estimated total fiber meeting your target. The optional weight limit applies to the **entire** combination.")
with st.spinner("Finding food combinations…"):
    result = build_combos(tuple(sorted(selected_groups)), float(goal), int(cap) if apply_cap else None, (50, 100, 150, 200), max_foods)
if result.empty:
    st.warning("No feasible combination was found in the tested candidate foods and portion sizes. Try lowering your fiber target, increasing your weight limit, or including more food groups. This does not prove that no combination exists.")
else:
    st.success(f"Found {len(result)} distinct combinations to explore (up to 20 shown).")
    displayed = result.drop(columns=["Calories (kcal)"])
    st.caption("Click a row to view that food combination's details.")
    table_event = st.dataframe(
        displayed,
        hide_index=True,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
    )
    selected_rows = table_event.selection.rows
    if selected_rows:
        chosen = result.iloc[selected_rows[0]]
        st.subheader("Selected combination")
        m1, m2 = st.columns(2)
        m1.metric("Combined weight", f"{int(chosen['Total weight (g)'])} g")
        m2.metric("Estimated fiber", f"{chosen['Fiber (g)']:.1f} g")
        st.write(chosen["Combination"])
        if show_nutrients:
            with st.expander("Complementary nutrient summary", expanded=True):
                st.metric("Estimated energy", f"{chosen['Calories (kcal)']:.0f} kcal")
                st.caption("Only energy and fiber are available in the current cleaned dataset. Protein, iron, and other nutrients require an additional validated nutrient-data merge.")
    else:
        st.info("Select a row above to inspect its ingredients, portions, and nutrient totals.")

with st.expander("How recommendations are made — methods and limitations"):
    st.markdown("""**Dataset and preparation:** Each observation is one Canadian Nutrient File food entry. Fiber/energy values are per 100 g. The notebook constructs keyword-based `food_form` labels and flags herbs/spices, peels, juice/cooking liquids and uncooked dry pulses as unsuitable for default large-portion suggestions. These heuristic labels can misclassify entries, and the full augmented dataset preserves all flags for review.

**Search method:** Foods are shortlisted within each selected group using fiber density and a transparent, curated list of familiar food names; excluded food entries cannot enter the shortlist. The app exhaustively tests two-food pairs of shortlist entries at 50/100/150/200 g portions; three-food candidates are sampled using a fixed random seed and evaluated in vectorized batches to keep the app responsive. Results are sorted by lower heuristic practicality penalty first, then lowest combined weight, then closest fiber amount above target, then lowest estimated calories. Food-form screening excludes dried staples and dehydrated non-fruit ingredients by default, while dried fruits remain eligible with a ranking penalty. The hand-built common-food priority is not measured popularity. It displays different sets of foods and does **not** guarantee global optimality.

**Limitations:** Portions are simplified discrete quantities, not customary servings. Nutrient values are approximate and refer to specific preparation states. Keyword-based screening reduces obvious impractical entries but does not validate serving norms or personal preferences. This is not a complete dietary plan and does not incorporate price, allergies, micronutrient adequacy, or health conditions. The weight cap is an upper bound, not a recommendation to eat that quantity.""")
