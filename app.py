from flask import Flask, request, jsonify
from models.user import User
from database import db
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:admin@127.0.0.1:3306/flask-crud'

login_manager = LoginManager()
db.init_app(app)
login_manager.init_app(app)

login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()

    if user and bcrypt.checkpw(str.encode(password), str.encode(user.password)):
        login_user(user)
        return jsonify({'message': 'Login successful'}), 200
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/register', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'message': 'User already exists'}), 400

    hashed_password = bcrypt.hashpw(str.encode(password), bcrypt.gensalt())

    new_user = User(username=username, password=hashed_password, role='user')
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

@app.route('/user/<int:id_user>', methods=['GET'])
@login_required
def read_user(id_user):
    user = User.query.get(id_user)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    return jsonify({'username': user.username}), 200

@app.route('/users', methods=['GET'])
@login_required
def read_users():
    users = User.query.all()
    content = [{'id': user.id, 'username': user.username, 'role': user.role} for user in users]
    total = len(content)
    return jsonify({'total': total, 'users': content}), 200

@app.route('/user/<int:id_user>', methods=['PUT'])
@login_required
def update_user(id_user):
    data = request.json
    user = User.query.get(id_user)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    if not (password := data.get('password')):
        return jsonify({'message': 'Password is required'}), 400
    
    if current_user.id != user.id and current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403

    user.password = password

    db.session.commit()
    return jsonify({'message': f'User {user.username} updated successfully'}), 200

@app.route('/user/<int:id_user>', methods=['DELETE'])
@login_required
def delete_user(id_user):
    user = User.query.get(id_user)

    if current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403

    if not user:
        return jsonify({'message': 'User not found'}), 404

    if user.id == current_user.id:
        return jsonify({'message': 'You cannot delete your own account'}), 403

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': f'User {user.username} deleted successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)