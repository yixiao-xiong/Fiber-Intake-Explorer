# Fiber Intake Explorer — revised food-form screening

Run the notebook in `notebooks/` from top to bottom to regenerate `data/fiber_data.csv` and `data/fiber_data_recommendation.csv`; then run `streamlit run app.py` from the project root.

`food_features.py` is a small shared **pure transformation module** used by the notebook to avoid duplicating and drifting text-matching rules. The Streamlit app reads the exported CSV. It is not a mandatory layout; its logic could be pasted into the notebook, but that would make review and reuse harder.

Heuristics: dried fruit allowed with ranking penalty; dried staple grains/pulses and dehydrated non-fruit ingredients excluded by default, alongside spices, juice and minor ingredients. False positives/negatives remain possible; not a food-safety, popularity, or serving-size model. CNF composition averages are per 100 g edible portion. Review rules and results before use.

AI-use note: ChatGPT (GPT-6) assisted with refactoring and testing the rules and documentation. Verify and document your own manual review, design decisions, and tests before submission.
