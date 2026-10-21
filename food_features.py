"""Auditable text-based food heuristics for CNF 2026; not measured consumption frequency."""
import re
import pandas as pd

# Matching the FIRST comma-separated clause prevents 'apple, ...' matching pineapple, etc.
COMMON_BASES = {"apple","banana","orange","pear","peach","plum","grape","kiwi","mango","pineapple","avocado","broccoli","carrot","cabbage","spinach","lettuce","tomato","cucumber","potato","sweet potato","cauliflower","asparagus","artichoke","corn","fig","date","raisin","strawberry","blueberry","raspberry","blackberry","apricot","lentils","lentil","chickpeas","chickpea","tofu","soybean kernels","green beans","peas"}
SPICE_PATTERN = r"\b(?:paprika|cayenne|ancho|chili powder|chilli powder|cinnamon|cumin|cloves?|nutmeg|turmeric|oregano|thyme|basil|rosemary|sage|marjoram|bay leaves?|allspice|cardamom|tarragon|spices?|seasoning|celery flakes)\b"
MINOR_PATTERN = r"\b(?:peels?|rinds?|zest|skin only|shell only|cooking water|cooking liquid|liquid from|brine|broth|stock|extract|concentrate|powder|flour|vine leaves?|grape leaves?)\b"
DRIED_PATTERN = r"\b(?:dried|dry|dehydrated|freeze.dried|sun.dried|low moisture)\b"
COOKED_PATTERN = r"\b(?:cooked|boiled|steamed|baked|roasted|microwaved|fried|stewed|braised|grilled|sauteed|sautéed)\b"
PROCESSED_PATTERN = r"\b(?:canned|bottled|pickled|fermented|preserved|syrup|juice|frozen|shelf stable)\b"
RAW_PATTERN = r"\b(?:raw|fresh|uncooked)\b"
# These are deliberately narrow exceptions, NOT a nutrition safety classifier.
DRIED_FRUIT_PATTERN = r"\b(?:apple|apricot|banana|date|fig|grape|raisin|peach|pear|plum|prune|cranberr|blueberr|strawberr|mango|pineapple)\b"
DRY_STAPLE_PATTERN = r"\b(?:corn|maize|beans?|lentils?|chickpeas?|peas?|soybeans?|rice|grain|kernels?)\b"

def classify_form(description):
    s=str(description).lower()
    # Dried takes precedence over 'uncooked', and cooked takes precedence only if not dried.
    if re.search(DRIED_PATTERN,s): return 'Dried / dehydrated'
    if re.search(COOKED_PATTERN,s): return 'Cooked'
    if re.search(PROCESSED_PATTERN,s): return 'Processed / preserved'
    if re.search(RAW_PATTERN,s): return 'Raw / fresh'
    return 'Other / unknown'

def add_food_features(df):
    out=df.copy()
    desc=out['Food_Description_EN'].fillna('').astype(str).str.lower()
    base=desc.str.split(',').str[0].str.strip()
    out['food_form']=desc.map(classify_form)
    dried=desc.str.contains(DRIED_PATTERN,regex=True)
    # Dried fruit is a potentially ordinary snack, but receives a ranking penalty.
    out['is_dried_fruit']=dried & base.str.contains(DRIED_FRUIT_PATTERN,regex=True)
    out['is_dry_staple']=dried & (base.str.contains(DRY_STAPLE_PATTERN,regex=True)) & ~out['is_dried_fruit']
    out['is_dehydrated_nonfruit']=dried & ~out['is_dried_fruit'] & ~out['is_dry_staple']
    out['is_herb_spice']=desc.str.contains(SPICE_PATTERN,regex=True)
    out['is_minor_ingredient']=desc.str.contains(MINOR_PATTERN,regex=True) | desc.str.contains(r'\bjuice\b')
    out['is_dry_pulse']=out['is_dry_staple'] & base.str.contains(r'\b(?:beans?|lentils?|chickpeas?|peas?|soybeans?)\b',regex=True)
    out['is_common_example']=base.map(lambda s:s in COMMON_BASES or any(s.startswith(t+' ') for t in COMMON_BASES))
    out['practicality_penalty']=(
        10*out['is_herb_spice'].astype(int) + 10*out['is_minor_ingredient'].astype(int)
        + 8*out['is_dry_staple'].astype(int) + 8*out['is_dehydrated_nonfruit'].astype(int)
        + 2*out['is_dried_fruit'].astype(int) + 2*(~out['is_common_example']).astype(int)
    )
    excluded=out['is_herb_spice'] | out['is_minor_ingredient'] | out['is_dry_staple'] | out['is_dehydrated_nonfruit']
    out['recommendation_eligible']=(~excluded & out['fiber_per_100g'].notna() & out['calories_per_100g'].notna() & (out['fiber_per_100g']>0) & (out['calories_per_100g']>=0))
    return out
