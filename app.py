from flask import Flask, render_template, request, redirect, url_for
import requests
import datetime

app = Flask(__name__)
app.secret_key = '1b3d3a59146f36bf36cdce4b0061d433'

user_profile = {
    'weight': None,
    'age': None,
    'sex': None,
    'height': None,
    'goal': None,
}

daily_log = {
    'date': datetime.date.today().isoformat(),
    'foods': [],
    'total_protein': 0
}

NUTRITIONIX_APP_ID = 'ff6b9be9'
NUTRITIONIX_API_KEY = '3846149efd0939d0e460420712194829'
NUTRITIONIX_ENDPOINT = 'https://trackapi.nutritionix.com/v2/natural/nutrients'

def calculate_bmr(weight, height, age, sex):
    if sex == 'male':
        return 10 * weight + 6.25 * height - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161

def calculate_protein_target(weight, height, age, sex, goal):
    bmr = calculate_bmr(weight, height, age, sex)

    # Auto-adjusted protein_per_kg based on weight
    if goal == 'bulking':
        if weight <= 70:
            protein_per_kg = 2.2
        elif weight <= 90:
            protein_per_kg = 2.0
        elif weight > 90:
            protein_per_kg = 1.8
    elif goal == 'cutting':
        protein_per_kg = 2.4
    elif goal == 'maintaining':
        protein_per_kg = 1.8
    else:
        protein_per_kg = 2.0  # fallback

    # Slight BMR-based adjustment
    adjustment = (bmr - 1600) / 10000
    protein_per_kg += adjustment
    protein_per_kg = max(1.2, protein_per_kg)

    return round(weight * protein_per_kg, 1)


@app.route('/')
def index():
    if not all([user_profile['weight'], user_profile['goal']]):
        return redirect(url_for('profile'))
    daily_target = calculate_protein_target(
        user_profile['weight'], 
        user_profile['height'], 
        user_profile['age'], 
        user_profile['sex'], 
        user_profile['goal']
    )
    return render_template('index.html', log=daily_log, target=daily_target)

@app.route('/add_food', methods=['POST'])
def add_food():
    food_input = request.form.get('food')
    protein_override = request.form.get('protein_override')

    if protein_override:
        protein = round(float(protein_override), 1)
        daily_log['foods'].append({'name': food_input, 'protein': protein})
        daily_log['total_protein'] = round(daily_log['total_protein'] + protein, 1)
        return redirect(url_for('index'))

    headers = {
        'x-app-id': NUTRITIONIX_APP_ID,
        'x-app-key': NUTRITIONIX_API_KEY,
        'Content-Type': 'application/json'
    }
    data = {'query': food_input}
    response = requests.post(NUTRITIONIX_ENDPOINT, json=data, headers=headers)

    if response.status_code == 200:
        food_data = response.json()['foods'][0]
        food_name = food_data['food_name']
        protein = round(food_data['nf_protein'], 1)
        daily_log['foods'].append({'name': food_name, 'protein': protein})
        daily_log['total_protein'] = round(daily_log['total_protein'] + protein, 1)

    return redirect(url_for('index'))

@app.route('/remove_food', methods=['POST'])
def remove_food():
    index = int(request.form.get('index'))
    if 0 <= index < len(daily_log['foods']):
        protein_removed = daily_log['foods'][index]['protein']
        daily_log['total_protein'] = round(daily_log['total_protein'] - protein_removed, 1)
        del daily_log['foods'][index]
    return redirect(url_for('index'))

@app.route('/clear_log', methods=['POST'])
def clear_log():
    daily_log['foods'].clear()
    daily_log['total_protein'] = 0
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    return render_template('profile.html', profile=user_profile)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    user_profile['weight'] = float(request.form.get('weight'))
    user_profile['age'] = int(request.form.get('age'))
    user_profile['sex'] = request.form.get('sex')
    user_profile['height'] = int(request.form.get('height'))
    user_profile['goal'] = request.form.get('goal')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
