import pymongo
import random
import string
from datetime import datetime

# MongoDB connection
client = pymongo.MongoClient("mongodb+srv://chahidhamdaoui:hamdaoui1@cluster0.kezbfis.mongodb.net/?retryWrites=true&w=majority")
db = client.foodtruck
orders_collection = db.orders
codes_collection = db.codes
users_collection = db.users

def display_orders():
    orders = orders_collection.find()
    for order in orders:
        print(f"Order ID: {order['_id']}")
        print(f"Username: {order['username']}")
        items = order.get('items', [])
        item_list = ', '.join([f"{item['name']} ({item['quantity']})" for item in items])
        print(f"Items: {item_list}")
        tip = order.get('tip', 0)
        print(f"Tip: {tip}")
        order_time = order.get('order_time', 'N/A')
        if order_time != 'N/A':
            order_time = order_time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"Date: {order_time}")
        print("-" * 20)

def generate_balance_code(amount):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    codes_collection.insert_one({"code": code, "amount": amount})
    print(f"Generated code: {code} for amount: {amount}")

def create_test_account():
    test_account = {
        "username": "test",
        "password": "test",
        "balance": 100.0
    }
    users_collection.insert_one(test_account)
    print("Test account created with username 'test' and password 'test'")

def verify_test_account():
    user = users_collection.find_one({"username": "test", "password": "test"})
    if user:
        print("Test account verified successfully.")
    else:
        print("Test account verification failed.")

def start_bonus_program():
    db.bonus_program.update_one({}, {'$set': {'active': True}}, upsert=True)
    print("Bonus program started.")

def end_bonus_program():
    db.bonus_program.update_one({}, {'$set': {'active': False}}, upsert=True)
    print("Bonus program ended.")

if __name__ == "__main__":
    while True:
        print("1. Display Orders")
        print("2. Generate Balance Code")
        print("3. Create Test Account")
        print("4. Verify Test Account")
        print("5. Start Bonus Program")
        print("6. End Bonus Program")
        print("7. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            display_orders()
        elif choice == "2":
            amount = float(input("Enter the amount for the balance code: "))
            generate_balance_code(amount)
        elif choice == "3":
            create_test_account()
        elif choice == "4":
            verify_test_account()
        elif choice == "5":
            start_bonus_program()
        elif choice == "6":
            end_bonus_program()
        elif choice == "7":
            break
        else:
            print("Invalid choice. Please try again.")
