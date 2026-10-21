# Fiber Intake Explorer

**CMSE 830 — Foundations of Data Science | Midterm Project | Fall 2026**

## Project Overview

Fiber Intake Explorer is an interactive Streamlit application that helps users explore combinations of fruits, vegetables, and legumes that meet a desired dietary fiber target.

Users can specify their fiber target, optionally set a maximum combined food weight, select food groups, and explore recommended combinations.

## Data Source

This project uses the **Canadian Nutrient File (CNF), 2026 edition**, maintained by Health Canada.

Official source: [Health Canada — Canadian Nutrient File](https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/nutrient-data/canadian-nutrient-file-about-us.html)

The analysis focuses on dietary fiber (g/100 g) and energy (kcal/100 g) in selected fruit, vegetable, and legume entries.

## Data Preparation and EDA

The Jupyter Notebook documents the data processing workflow:

1. Examine the original CNF relational tables.
2. Merge food descriptions, nutrient information, and food groups.
3. Assess missingness and remove entries without available fiber information.
4. Explore fiber and energy distributions.
5. Classify food preparation forms using description-based rules.
6. Apply heuristic practicality screening.
7. Export the recommendation-ready dataset.

Of the 5,993 original food records, 1,353 belong to the selected food categories. After excluding 113 entries without fiber values, 1,240 records remain. The final screening produces 1,048 recommendation-eligible records.

## Streamlit Features

- User-defined fiber target
- Optional maximum combined food weight
- Food-group selection
- Two- or three-food combinations
- Interactive row selection
- Optional complementary nutrient summary

## Running the Project

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the Streamlit application from the project root:

```bash
streamlit run app.py
```

The analysis notebook is located in `notebooks/`.

## Limitations

- Nutrient values are reference averages, not exact measurements of individual products.
- Food-form classification and practicality screening rely on heuristic rules.
- Recommendations are generated from a restricted candidate pool and do not guarantee global optimality.
- Food commonness is not estimated from actual consumption-frequency data.
- Portion sizes are simplified.
- Prices, allergies, and individual dietary requirements are not considered.

## Generative AI Disclosure

ChatGPT (GPT-6) was used to assist with Python debugging, code refactoring, Streamlit implementation, documentation, and exploration of food-classification rules.

AI-assisted outputs were reviewed through code execution, data consistency checks, and manual inspection of selected food entries. The project question, analytical decisions, interpretation, and final review remain the student's responsibility.
