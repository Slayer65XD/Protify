from flask import Flask, render_template, request, redirect, url_for, session
import requests
import datetime

app = Flask(__name__)
#import secrets
#print(secrets.token_hex(16))
app.secret_key = '1b3d3a59146f36bf36cdce4b0061d433'

# Placeholder for user profile and daily logs
user_profile = {
    'weight': 100,  # in kg
    'goal': 'bulking',
    'protein_per_kg': 2.0  # can vary based on goal
}

daily_log = {
    'date': datetime.date.today().isoformat(),
    'foods': [],
    'total_protein': 0
}

# Nutritionix API details
NUTRITIONIX_APP_ID = 'ff6b9be9'
NUTRITIONIX_API_KEY = '3846149efd0939d0e460420712194829'
NUTRITIONIX_ENDPOINT = 'https://trackapi.nutritionix.com/v2/natural/nutrients'

@app.route('/')
def index():
    daily_target = user_profile['weight'] * user_profile['protein_per_kg']
    return render_template('index.html', log=daily_log, target=daily_target)

@app.route('/add_food', methods=['POST'])
def add_food():
    food_input = request.form.get('food')
    headers = {
        'x-app-id': NUTRITIONIX_APP_ID,
        'x-app-key': NUTRITIONIX_API_KEY,
        'Content-Type': 'application/json'
    }
    data = {
        'query': food_input
    }
    response = requests.post(NUTRITIONIX_ENDPOINT, json=data, headers=headers)
    if response.status_code == 200:
        food_data = response.json()['foods'][0]
        food_name = food_data['food_name']
        protein = food_data['nf_protein']
        daily_log['foods'].append({'name': food_name, 'protein': protein})
        daily_log['total_protein'] += protein
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    return render_template('profile.html', profile=user_profile)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    user_profile['weight'] = float(request.form.get('weight'))
    user_profile['goal'] = request.form.get('goal')
    user_profile['protein_per_kg'] = float(request.form.get('protein_per_kg'))
    return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run(debug=True)
