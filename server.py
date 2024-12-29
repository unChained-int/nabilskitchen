from flask import Flask, request, jsonify, send_from_directory
from pymongo import MongoClient
import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string

app = Flask(__name__, static_folder='../')

# MongoDB connection
client = MongoClient("mongodb+srv://chahidhamdaoui:hamdaoui1@cluster0.kezbfis.mongodb.net/?retryWrites=true&w=majority")
db = client.foodtruck
users_collection = db.users
orders_collection = db.orders
codes_collection = db.codes

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory(app.static_folder, path)

@app.route('/admin')
def serve_admin():
    return send_from_directory(app.static_folder, 'admin.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    email = data['email']
    password = data['password']

    if users_collection.find_one({'username': username}):
        return jsonify({'success': False, 'message': 'Benutzername bereits vergeben.'})

    hashed_password = generate_password_hash(password)
    users_collection.insert_one({'username': username, 'email': email, 'password': hashed_password, 'balance': 0.0})
    return jsonify({'success': True})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']

    user = users_collection.find_one({'username': username})
    if user and check_password_hash(user['password'], password):
        return jsonify({'success': True, 'balance': user['balance'], 'bonusPoints': user.get('bonus_count', 0)})
    else:
        return jsonify({'success': False, 'message': 'Ungültiger Benutzername oder Passwort.'})

@app.route('/api/balance', methods=['GET'])
def get_balance():
    username = request.args.get('username')
    user = users_collection.find_one({'username': username})
    if user:
        return jsonify({'success': True, 'balance': user['balance']})
    else:
        return jsonify({'success': False, 'message': 'Benutzer nicht gefunden.'})

@app.route('/api/orders', methods=['GET'])
def get_orders():
    username = request.args.get('username')
    orders = orders_collection.find({'username': username})
    return jsonify([order for order in orders])

@app.route('/api/open-orders', methods=['GET'])
def get_open_orders():
    username = request.args.get('username')
    orders = orders_collection.find({'username': username, 'status': 'open'})
    return jsonify({'success': True, 'orders': list(orders)})

@app.route('/api/order', methods=['POST'])
def order():
    data = request.json
    items = data['items']
    username = data['username']
    tip = data.get('tip', 0)
    order_time = datetime.datetime.strptime(data['order_time'], '%Y-%m-%dT%H:%M')

    fixed_prices = {
        'Classic-Ham': 6.50, 'Classic-Cheese': 6.00, 'Classic-Chicken': 7.50, 'Classic-Crispy': 6.00,
        'Veggie-Burger': 5.50, 'Bacon-Burger': 7.00, 'Onion-Burger': 6.50, 'Chillicheese-Burger': 7.00,
        'Pastrami-Burger': 8.00, 'Medina-Burger': 8.00, 'Juarez-Burger': 8.00, 'BBQ-Burger': 7.50,
        'Double-Double-Burger': 9.50, 'Jamina\'s Nr. 1': 11.00, 'Long-Ham': 8.00, 'Long-Chicken': 8.50,
        'Long-Merguez': 7.00, 'Long-Crispy': 6.50, 'Long-Köfta': 7.00, 'Long-Medina': 7.50,
        'Long-Chillicheese': 7.50, 'Long-Turkey Roll': 8.50, 'Long-Smokey BBQ': 8.50, 'Ham-Burrito': 4.50,
        'Chicken-Burrito': 4.50, 'Mix-Burrito': 5.00, 'Veggie-Burrito': 4.00, 'Pommes': 2.00,
        'Süßkartoffelpommes': 2.50, 'Onion-Rings': 2.00, 'Tortilla-Patty': 4.00, 'Chicken-File': 4.50,
        'César Salat': 4.00, 'Thunfisch Salat': 4.00, 'Marokkanischer Tomaten Salat': 3.50,
        'Classic Salat': 3.50, 'Cola': 1.80, 'Fanta': 1.80, 'Sprite': 1.80, 'Mezzo-Mix': 1.80,
        'Red Bull': 2.50, 'Smoothie': 3.50, 'Bacon': 1.00, 'Pastrami': 1.00, 'gegrillter Rinderschinken': 1.00,
        'Käse': 0.50, 'Röstzwiebeln': 0.50, 'Jalapeños': 0.50, 'BBQ': 0.50, 'gegr. Paprika': 0.50,
        'gegr. Champignons': 0.50, 'Zwiebeln à la Jamina': 0.50
    }
    total_amount = sum(fixed_prices[item['name']] * item['quantity'] for item in items if item['quantity'] > 0) + tip

    user = users_collection.find_one({'username': username})
    if not user:
        return jsonify({'success': False, 'message': 'Benutzer nicht gefunden.'})

    if user['balance'] is None or user['balance'] < total_amount:
        return jsonify({'success': False, 'message': 'Nicht genügend Guthaben.'})

    now = datetime.datetime.now()
    if order_time < now:
        return jsonify({'success': False, 'message': 'Bestellungen für die Vergangenheit sind nicht möglich.'})

    bonus_program = db.bonus_program.find_one({})
    if bonus_program and bonus_program.get('active', False):
        if total_amount > 5:
            user['bonus_count'] = user.get('bonus_count', 0) + 1
            if user['bonus_count'] >= 3:
                user['bonus_count'] = 0
                total_amount = 0  # Free order
            users_collection.update_one({'username': username}, {'$set': {'bonus_count': user['bonus_count']}})

    users_collection.update_one({'username': username}, {'$inc': {'balance': -total_amount}})
    orders_collection.insert_one({'username': username, 'items': items, 'tip': tip, 'order_time': order_time, 'status': 'open'})

    user = users_collection.find_one({'username': username})
    new_balance = user['balance']
    return jsonify({'success': True, 'newBalance': new_balance, 'bonusPoints': user.get('bonus_count', 0), 'message': 'Ihre Bestellung wird in 30 Minuten zur Abholung bereit sein.'})

@app.route('/api/top-up', methods=['POST'])
def top_up():
    try:
        data = request.json
        code = data['code']
        username = data['username']

        valid_code = codes_collection.find_one({'code': code})
        if not valid_code:
            return jsonify({'success': False, 'message': 'Ungültiger Zahlencode.'})

        amount = valid_code['amount']
        user = users_collection.find_one({'username': username})
        if user['balance'] is None:
            users_collection.update_one({'username': username}, {'$set': {'balance': 0.0}})
        users_collection.update_one({'username': username}, {'$inc': {'balance': amount}})
        codes_collection.delete_one({'code': code})

        user = users_collection.find_one({'username': username})
        new_balance = user['balance']
        return jsonify({'success': True, 'newBalance': new_balance})
    except Exception as e:
        print(f"Error during top-up: {e}")
        return jsonify({'success': False, 'message': 'Ein Fehler ist aufgetreten.'})

@app.route('/api/daily-orders', methods=['GET'])
def get_daily_orders():
    orders = orders_collection.find({'status': 'open'})
    orders_list = []
    for order in orders:
        order['_id'] = str(order['_id'])
        orders_list.append(order)
    return jsonify({'success': True, 'orders': orders_list})

@app.route('/api/complete-order', methods=['POST'])
def complete_order():
    data = request.json
    order_id = data['order_id']
    orders_collection.delete_one({'_id': order_id})
    return jsonify({'success': True, 'message': 'Bestellung abgeschlossen und gelöscht.'})

@app.route('/api/set-order-times', methods=['POST'])
def set_order_times():
    data = request.json
    start_time = data['start_time']
    end_time = data['end_time']
    db.order_times.update_one({}, {'$set': {'start_time': start_time, 'end_time': end_time}}, upsert=True)
    return jsonify({'success': True, 'message': 'Bestellzeiten aktualisiert.'})

@app.route('/api/refund', methods=['POST'])
def process_refund():
    try:
        data = request.json
        username = data['username']
        amount = data['amount']
        user = users_collection.find_one({'username': username})
        if user['balance'] is None:
            users_collection.update_one({'username': username}, {'$set': {'balance': 0.0}})
        users_collection.update_one({'username': username}, {'$inc': {'balance': amount}})
        return jsonify({'success': True, 'message': 'Rückerstattung erfolgreich.'})
    except Exception as e:
        print(f"Error during refund: {e}")
        return jsonify({'success': False, 'message': 'Ein Fehler ist aufgetreten.'})

@app.route('/api/generate-code', methods=['POST'])
def generate_code():
    try:
        data = request.json
        amount = data['amount']
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        codes_collection.insert_one({'code': code, 'amount': amount})
        return jsonify({'success': True, 'code': code})
    except Exception as e:
        print(f"Error during code generation: {e}")
        return jsonify({'success': False, 'message': 'Ein Fehler ist aufgetreten.'})

@app.route('/api/start-bonus-program', methods=['POST'])
def start_bonus_program():
    try:
        db.bonus_program.update_one({}, {'$set': {'active': True}}, upsert=True)
        return jsonify({'success': True, 'message': 'Bonusprogramm gestartet.'})
    except Exception as e:
        print(f"Error during starting bonus program: {e}")
        return jsonify({'success': False, 'message': 'Ein Fehler ist aufgetreten.'})

@app.route('/api/end-bonus-program', methods=['POST'])
def end_bonus_program():
    try:
        db.bonus_program.update_one({}, {'$set': {'active': False}}, upsert=True)
        return jsonify({'success': True, 'message': 'Bonusprogramm beendet.'})
    except Exception as e:
        print(f"Error during ending bonus program: {e}")
        return jsonify({'success': False, 'message': 'Ein Fehler ist aufgetreten.'})

@app.route('/api/monthly-stats', methods=['GET'])
def get_monthly_stats():
    pipeline = [
        {
            '$group': {
                '_id': {'year': {'$year': '$order_time'}, 'month': {'$month': '$order_time'}},
                'total_orders': {'$sum': 1},
                'total_revenue': {'$sum': '$total_amount'}
            }
        },
        {
            '$sort': {'_id.year': 1, '_id.month': 1}
        }
    ]
    stats = list(orders_collection.aggregate(pipeline))
    return jsonify({'success': True, 'stats': stats})

if __name__ == '__main__':
    app.run(debug=True)
