"""
FuelUp — Student Health & Nutrition Planner
---------------------------------------------
A small full-stack Flask app that:
  1. Takes a student's basic stats (name, age, sex, height, weight, activity level, goal, diet type)
  2. Calculates BMR (Mifflin-St Jeor), TDEE, and a calorie/macro target
  3. Lets the student build a real diet plate from a food database
     (protein / fibre-veg / carb dropdowns, quantity-adjustable)
     and shows live totals against their target.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000
"""

from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# ----------------------------------------------------------------------
# FOOD DATABASE
# Values are per the stated serving unit.
# fields: label, unit, calories, protein(g), carbs(g), fat(g), fiber(g), diet ("veg" | "nonveg" | "both")
# ----------------------------------------------------------------------
FOOD_DB = {
    "protein": [
        {"id": "egg",       "label": "Whole Egg",          "unit": "1 egg (50g)",     "kcal": 78,  "protein": 6.3, "carbs": 0.6, "fat": 5.3, "fiber": 0,   "diet": "nonveg"},
        {"id": "egg_white",  "label": "Egg White",          "unit": "1 white (33g)",   "kcal": 17,  "protein": 3.6, "carbs": 0.2, "fat": 0.1, "fiber": 0,   "diet": "nonveg"},
        {"id": "chicken",   "label": "Chicken Breast",      "unit": "100g cooked",     "kcal": 165, "protein": 31,  "carbs": 0,   "fat": 3.6, "fiber": 0,   "diet": "nonveg"},
        {"id": "fish",      "label": "Fish (Rohu/Tilapia)", "unit": "100g cooked",     "kcal": 150, "protein": 26,  "carbs": 0,   "fat": 4.5, "fiber": 0,   "diet": "nonveg"},
        {"id": "protein_powder", "label": "Whey Protein Powder", "unit": "1 scoop (30g)", "kcal": 120, "protein": 24, "carbs": 3,  "fat": 1.5, "fiber": 0, "diet": "both"},
        {"id": "paneer",    "label": "Paneer (Cottage Cheese)", "unit": "100g",        "kcal": 265, "protein": 18,  "carbs": 3.4, "fat": 20,  "fiber": 0,   "diet": "veg"},
        {"id": "tofu",      "label": "Tofu",                "unit": "100g",            "kcal": 76,  "protein": 8,   "carbs": 1.9, "fat": 4.8, "fiber": 0.3, "diet": "veg"},
        {"id": "dal",       "label": "Dal / Lentils",       "unit": "100g cooked",     "kcal": 116, "protein": 9,   "carbs": 20,  "fat": 0.4, "fiber": 8,   "diet": "veg"},
        {"id": "chickpeas", "label": "Chickpeas (Chana)",   "unit": "100g cooked",     "kcal": 164, "protein": 8.9, "carbs": 27,  "fat": 2.6, "fiber": 7.6, "diet": "veg"},
        {"id": "greek_yogurt", "label": "Greek Yogurt",     "unit": "100g",            "kcal": 59,  "protein": 10,  "carbs": 3.6, "fat": 0.4, "fiber": 0,   "diet": "veg"},
    ],
    "fiber": [
        {"id": "carrot",    "label": "Carrot",     "unit": "100g", "kcal": 41, "protein": 0.9, "carbs": 10,  "fat": 0.2, "fiber": 2.8, "diet": "both"},
        {"id": "cucumber",  "label": "Cucumber",   "unit": "100g", "kcal": 15, "protein": 0.7, "carbs": 3.6, "fat": 0.1, "fiber": 0.5, "diet": "both"},
        {"id": "spinach",   "label": "Spinach",    "unit": "100g", "kcal": 23, "protein": 2.9, "carbs": 3.6, "fat": 0.4, "fiber": 2.2, "diet": "both"},
        {"id": "broccoli",  "label": "Broccoli",   "unit": "100g", "kcal": 34, "protein": 2.8, "carbs": 7,   "fat": 0.4, "fiber": 2.6, "diet": "both"},
        {"id": "tomato",    "label": "Tomato",     "unit": "100g", "kcal": 18, "protein": 0.9, "carbs": 3.9, "fat": 0.2, "fiber": 1.2, "diet": "both"},
        {"id": "beans",     "label": "Green Beans","unit": "100g", "kcal": 31, "protein": 1.8, "carbs": 7,   "fat": 0.2, "fiber": 3.4, "diet": "both"},
        {"id": "salad",     "label": "Salad ",     "unit": "100g", "kcal": 20, "protein": 1.5, "carbs": 3.5, "fat": 0.3, "fiber": 2,   "diet": "both"},
    ],
    "carbs": [
        {"id": "rice",        "label": "Rice",          "unit": "100g cooked", "kcal": 130, "protein": 2.7, "carbs": 28,  "fat": 0.3, "fiber": 0.4, "diet": "both"},
        {"id": "chapati",     "label": "Chapati/Roti",  "unit": "1 piece (40g)", "kcal": 120, "protein": 3.5, "carbs": 18,  "fat": 3.5, "fiber": 2.5, "diet": "both"},
        {"id": "sweet_potato","label": "Sweet Potato",  "unit": "100g",        "kcal": 86,  "protein": 1.6, "carbs": 20,  "fat": 0.1, "fiber": 3,   "diet": "both"},
        {"id": "oats",        "label": "Oats",          "unit": "100g dry",    "kcal": 389, "protein": 16.9,"carbs": 66,  "fat": 6.9, "fiber": 10.6,"diet": "both"},
        {"id": "quinoa",      "label": "Quinoa",        "unit": "100g cooked", "kcal": 120, "protein": 4.4, "carbs": 21,  "fat": 1.9, "fiber": 2.8, "diet": "both"},
        {"id": "brown_bread", "label": "Brown Bread",   "unit": "1 slice (30g)", "kcal": 75, "protein": 3.5, "carbs": 13,  "fat": 1,   "fiber": 2,   "diet": "both"},
        {"id": "banana",      "label": "Banana",        "unit": "1 medium (120g)", "kcal": 105,"protein": 1.3, "carbs": 27,  "fat": 0.4, "fiber": 3.1, "diet": "both"},
    ],
}

ACTIVITY_MULTIPLIERS = {
    "sedentary":   {"factor": 1.20, "label": "Sedentary (little/no exercise, desk study)"},
    "light":       {"factor": 1.375, "label": "Lightly active (1-3 light workouts/week)"},
    "moderate":    {"factor": 1.55, "label": "Moderately active (3-5 workouts/week or sports)"},
    "active":      {"factor": 1.725, "label": "Very active (6-7 workouts/week)"},
    "very_active": {"factor": 1.90, "label": "Extremely active (athlete / physical job + training)"},
}

GOAL_ADJUSTMENT = {
    "lose":     {"delta": -500, "label": "Lose Weight", "protein_g_per_kg": 1.8},
    "maintain": {"delta": 0,    "label": "Maintain Weight", "protein_g_per_kg": 1.6},
    "gain":     {"delta": 400,  "label": "Gain Muscle", "protein_g_per_kg": 2.0},
}


def calculate_bmr(sex, weight_kg, height_cm, age):
    """Mifflin-St Jeor Equation"""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if sex == "male" else base - 161


def calculate_calories_burned_estimate(weight_kg, activity_level):
    """Rough estimate of active calories burned per day from exercise, on top of BMR,
    used purely for the 'calories burned' display card (separate from TDEE, which already
    folds daily activity into the multiplier)."""
    met_by_level = {
        "sedentary": 1.5,
        "light": 4,
        "moderate": 6,
        "active": 8,
        "very_active": 10,
    }
    met = met_by_level.get(activity_level, 1.5)
    minutes = {"sedentary": 10, "light": 30, "moderate": 45, "active": 60, "very_active": 90}[activity_level]
    # calories = MET * weight(kg) * hours
    kcal = met * weight_kg * (minutes / 60)
    return round(kcal)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/foods")
def api_foods():
    return jsonify(FOOD_DB)


@app.route("/api/calculate", methods=["POST"])
def api_calculate():
    data = request.get_json(force=True)

    try:
        name = str(data.get("name", "Student")).strip() or "Student"
        age = float(data["age"])
        sex = data.get("sex", "male")
        height_cm = float(data["height"])
        weight_kg = float(data["weight"])
        activity = data.get("activity", "moderate")
        goal = data.get("goal", "maintain")
        diet_type = data.get("diet_type", "veg")
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "Please fill in all fields with valid numbers."}), 400

    if age <= 0 or height_cm <= 0 or weight_kg <= 0:
        return jsonify({"error": "Age, height and weight must be positive numbers."}), 400

    if activity not in ACTIVITY_MULTIPLIERS:
        activity = "moderate"
    if goal not in GOAL_ADJUSTMENT:
        goal = "maintain"

    bmr = calculate_bmr(sex, weight_kg, height_cm, age)
    activity_info = ACTIVITY_MULTIPLIERS[activity]
    tdee = bmr * activity_info["factor"]

    goal_info = GOAL_ADJUSTMENT[goal]
    target_calories = max(1200, round(tdee + goal_info["delta"]))

    burned_estimate = calculate_calories_burned_estimate(weight_kg, activity)

    # Macro split
    protein_g = round(goal_info["protein_g_per_kg"] * weight_kg)
    protein_kcal = protein_g * 4
    fat_kcal = round(target_calories * 0.25)
    fat_g = round(fat_kcal / 9)
    carbs_kcal = max(0, target_calories - protein_kcal - fat_kcal)
    carbs_g = round(carbs_kcal / 4)

    bmi = round(weight_kg / ((height_cm / 100) ** 2), 1)
    if bmi < 18.5:
        bmi_category = "Underweight"
    elif bmi < 25:
        bmi_category = "Normal"
    elif bmi < 30:
        bmi_category = "Overweight"
    else:
        bmi_category = "Obese"

    water_liters = round(weight_kg * 0.035, 1)

    return jsonify({
        "name": name,
        "bmr": round(bmr),
        "tdee": round(tdee),
        "target_calories": target_calories,
        "calories_burned_estimate": burned_estimate,
        "activity_label": activity_info["label"],
        "goal_label": goal_info["label"],
        "bmi": bmi,
        "bmi_category": bmi_category,
        "water_liters": water_liters,
        "macros": {
            "protein_g": protein_g,
            "carbs_g": carbs_g,
            "fat_g": fat_g,
            "protein_kcal": protein_kcal,
            "carbs_kcal": carbs_kcal,
            "fat_kcal": fat_kcal,
        },
        "diet_type": diet_type,
    })


if __name__ == "__main__":
    app.run(debug=True)
