from datetime import timedelta
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import onnxruntime as ort
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import csv
import json
import os


app = Flask(__name__)
app.secret_key = 'fsdjkfddgngjks'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
login_manager = LoginManager(app)
login_manager.login_view = 'login_register'

meal_logs = []
meal_logs_directory = 'meal_logs'

if not os.path.exists(meal_logs_directory):
    os.makedirs(meal_logs_directory)


class User(UserMixin):
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.meal_logs = []

    def add_meal_log(self, log):
        log['datetime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.meal_logs.append(log)



def load_users():
    try:
        with open('users.json', 'r') as file:
            users = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        users = {}
    return users




def save_users(users):
    with open('users.json', 'w') as file:
        json.dump(users, file)



users = load_users()



@login_manager.user_loader
def load_user(user_id):
    user_data = users.get(user_id)
    if user_data:
        email = user_data.get('email', '')
        return User(user_id, user_data.get('username', ''), email, user_data.get('password', ''))
    return None

@app.route('/')
@login_required
def render_homePage():
    user_log_file = os.path.join(
        meal_logs_directory, f"{current_user.id}_meal_log.json")
    try:
        with open(user_log_file, 'r') as file:
            user_logs = json.load(file)

        # Convert timestamp strings to datetime objects
        for log in user_logs:
            log['timestamp'] = datetime.strptime(
                log['timestamp'], '%Y-%m-%d %H:%M:%S')

        # Extract data for charts
        pie_chart_data = get_pie_chart_data(user_logs)
        line_chart_data = get_line_chart_data(user_logs)

    except FileNotFoundError:
        user_logs = []
        pie_chart_data = {'labels': [], 'data': []}
        line_chart_data = {'labels': [], 'data': []}

    return render_template('home_logged.html', current_user=current_user,
                           user_logs=user_logs, pie_chart_data=pie_chart_data, line_chart_data=line_chart_data)





@app.route('/login_register', methods=['GET', 'POST'])
def login_register():
    if request.method == 'POST':
 
        if 'login_username' in request.form:
            username_or_email = request.form['login_username']
            password = request.form['login_password']
            remember_me = request.form.get('formCheck')


            user = next((user_data for user_data in users.values() if
                         (user_data.get('username', '') == username_or_email or
                          user_data.get('email', '') == username_or_email)
                         and user_data.get('password', '') == password), None)

            if user:
                loaded_user = load_user(str(user['id']))
                if loaded_user:
                    login_user(loaded_user, remember=remember_me == 'on')
                    return redirect(url_for('render_homePage'))

            return render_template('home.html', error='Invalid username or password. Please try again.')

        elif 'register_username' in request.form:

            username = request.form['register_username']
            email = request.form['register_email']
            password = request.form['register_password']

            if any(user_data.get('username', '') == username or user_data.get('email', '') == email for user_data in users.values()):
                return render_template('home.html', error='Username or email already exists. Choose a different username or email.')
            if any(user_data.get('password', '') == password for user_data in users.values()):
                return render_template('home.html', error='Password already exists. Choose a different password.')
         
            user_id = str(len(users) + 1)
            users[user_id] = {'id': user_id, 'username': username,
                              'email': email, 'password': password}

           
            save_users(users)

            login_user(User(user_id, username, email, password))
            
            return redirect(url_for('render_homePage'))

    return render_template('home.html')



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('render_homePage'))

# Log Tracker


@app.route('/add_meal', methods=['GET', 'POST'])
@login_required
def add_meal():
    if request.method == 'POST':
        food = request.form['food']
        calories = int(request.form['calories'])
        quantity = int(request.form['quantity'])

       
        user_log_file = os.path.join(
            meal_logs_directory, f"{current_user.id}_meal_log.json")

        
        try:
            with open(user_log_file, 'r') as file:
                user_logs = json.load(file)
        except FileNotFoundError:
            user_logs = []

        
        user_logs.append({
            'food': food,
            'calories': calories,
            'quantity': quantity,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        # Save the updated logs to the file
        with open(user_log_file, 'w') as file:
            json.dump(user_logs, file)

        return redirect(url_for('view_meal_logs'))

    return render_template('add_meal.html')



@app.route('/view_meal_logs')
@login_required
def view_meal_logs():
    
    user_log_file = os.path.join(
        meal_logs_directory, f"{current_user.id}_meal_log.json")
    
    try:
        with open(user_log_file, 'r') as file:
            user_logs = json.load(file)

        
        for log in user_logs:
            log['timestamp'] = datetime.strptime(
                log['timestamp'], '%Y-%m-%d %H:%M:%S')

      
        pie_chart_data = get_pie_chart_data(user_logs)
        line_chart_data = get_line_chart_data(user_logs)

    except FileNotFoundError:
        user_logs = []
        pie_chart_data = {'labels': [], 'data': []}
        line_chart_data = {'labels': [], 'data': []}

    return render_template('view_meal_logs.html', user_logs=user_logs,
                           pie_chart_data=pie_chart_data, line_chart_data=line_chart_data)


def get_pie_chart_data(user_logs):

    food_data = {}
    for log in user_logs:
        food = log['food']
        calories = log['calories'] * log['quantity']
        food_data[food] = food_data.get(food, 0) + calories

    labels = list(food_data.keys())
    data = list(food_data.values())
    return {'labels': labels, 'data': data}


def get_line_chart_data(user_logs):
    
    daily_data = {}
    for log in user_logs:
        date_str = log['timestamp'].strftime('%Y-%m-%d')
        calories = log['calories'] * log['quantity']
        daily_data[date_str] = daily_data.get(date_str, 0) + calories

    labels = list(sorted(daily_data.keys()))
    data = [daily_data[label] for label in labels]
    return {'labels': labels, 'data': data}


# Meal Planner

onnx_session = ort.InferenceSession('meal_recommendation_model.onnx')


df = pd.read_csv('food_calories.csv')
df['Calories'] = df['Calories'].str.extract('(\d+)').astype(int)


food_names = df['Food'].values
label_encoder = LabelEncoder()
food_labels = label_encoder.fit_transform(food_names)


X = df[['Calories']].values


def recommend_meal_onnx(calories_needed, num_items):
    
    input_name = onnx_session.get_inputs()[0].name

    input_data = np.array([[calories_needed]], dtype=np.float32)

    predicted_probs = onnx_session.run(None, {input_name: input_data})[0]

 
    predicted_probs = predicted_probs.reshape(-1)

 
    sorted_indices = np.argsort(predicted_probs)[::-1]

    recommended_foods = []
    total_calories = 0

    for i in sorted_indices:
        food_label = label_encoder.inverse_transform([i])[0]
        food_calories = int(df[df['Food'] == food_label]['Calories'].values[0])
        food_serving = df[df['Food'] == food_label]['Serving'].values[0]

        if total_calories + food_calories <= calories_needed:
            recommended_foods.append(
                {'name': food_label, 'serving': food_serving, 'calories': food_calories})
            total_calories += food_calories

            if len(recommended_foods) == num_items:
                break

    return recommended_foods


@app.route('/plan_meal', methods=['POST'])
def plan_meal():
    calories_needed = int(request.form['calories'])
    num_items = int(request.form['num_items'])

    recommended_foods = recommend_meal_onnx(calories_needed, num_items)

    total_calories = int(sum(food['calories'] for food in recommended_foods))

    return jsonify({'recommended_foods': recommended_foods, 'total_calories': total_calories})

# food calories counter

@app.route('/food_calorie_counter')
@login_required
def render_FoodCalorieCounter():
    with open('food_calories.csv', 'r') as file:
        reader = csv.DictReader(file)
        food_data = [row for row in reader]
    return render_template('food_calorie_counter.html', food_data=food_data)


@app.route('/get_serving_options', methods=['POST'])
def get_serving_options():
    food = request.form.get('food')

    with open('food_calories.csv', 'r') as file:
        reader = csv.DictReader(file)
        food_data = [row for row in reader]
        for row in food_data:
            if row['Food'] == food:
                serving_options = row['Serving'].split(',')
                return {'serving_options': serving_options}


@app.route('/calculate', methods=['POST'])
def calculate_calories():
    food = request.form.get('food')
    serving = request.form.get('serving')
    quantity = int(request.form.get('quantity'))

    with open('food_calories.csv', 'r') as file:
        reader = csv.DictReader(file)
        food_data = [row for row in reader]
        for row in food_data:
            if row['Food'] == food:
                serving_options = row['Serving'].split(',')
                for option in serving_options:
                    if serving in option:
                        calories = int(row['Calories'].split()[0]) * quantity
                        message = f'{quantity} {food} with {serving} each, totaling {calories} calories.'
                        return render_template('food_calorie_counter.html', food_data=food_data, message=message)


if __name__ == '__main__':
    app.run(debug=True)
