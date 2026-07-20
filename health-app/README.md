# FuelUp — Student Health & Nutrition Planner

A full-stack Python (Flask) web app that helps students understand their daily
calorie needs and build a real, balanced diet plate from foods they actually eat.

## Features

- **Profile intake** — name, age, sex, height, weight, activity level, goal, diet type (veg / non-veg)
- **Science-based calculations**
  - BMR via the Mifflin-St Jeor equation
  - TDEE (maintenance calories) from activity level
  - Daily calorie target adjusted for the student's goal (lose / maintain / gain)
  - Estimated active calories burned
  - BMI, BMI category, and a daily water intake target
  - Macro split (protein / carbs / fat) in grams and calories
- **Plate builder** — dropdowns for Protein (eggs, chicken, fish, protein powder,
  paneer, tofu, dal, chickpeas, Greek yogurt), Veggies & Fibre (carrot, cucumber,
  spinach, broccoli, tomato, beans, salad), and Carbs (rice, chapati, sweet potato,
  oats, quinoa, brown bread, banana) — filtered automatically by veg / non-veg choice
- **Live dashboard** — an animated "fuel gauge", a macro donut chart, and progress
  bars that update in real time as the student adds food to their plate
- **Educational footer disclaimer** — makes clear this is a learning tool, not medical advice

## Project structure

```
health-app/
├── app.py                 # Flask backend: routes, BMR/TDEE/macro calculations, food database
├── requirements.txt
├── templates/
│   └── index.html         # Page structure
└── static/
    ├── style.css           # Visual design (design tokens documented at top of file)
    └── script.js            # Form handling, gauge/chart rendering, plate builder logic
```

## Run it locally

```bash
cd health-app
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## Using it with a class

- Each student fills in their own stats and gets a personal calorie target —
  a good jumping-off point for lessons on BMR/TDEE, macronutrients, or portion sizes.
- The plate builder is a hands-on way to show how quickly calories add up
  (or how to hit a protein target) using foods common in Indian student diets.
- All the nutrition numbers live in one place — the `FOOD_DB` dictionary at the
  top of `app.py` — so you can add local dishes, correct values, or extend it
  with new food groups (fruits, snacks, drinks) without touching the front end.

## Notes on the calculations

- BMR: Mifflin-St Jeor equation (widely used, reasonably accurate for most adults)
- TDEE = BMR × activity multiplier (1.2 sedentary → 1.9 extremely active)
- Calorie target = TDEE ± 500/400 kcal depending on goal
- Protein target scales with goal (1.6–2.0 g/kg bodyweight); fat is fixed at 25%
  of target calories; carbs fill the remainder
- Food nutrition values are standard per-100g / per-unit averages, meant for
  teaching estimation — not lab-precise nutrition facts

This is an educational tool, not medical advice. Encourage students to talk to
a doctor or registered dietitian for individual medical or nutrition guidance.
