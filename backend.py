from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import bcrypt, jwt, datetime
from functools import wraps
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tether.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pw_hash = db.Column(db.LargeBinary(60), nullable=False)
    data = db.Column(db.Text, default='{}')

def token_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(payload['user_id'])
        except Exception:
            return jsonify({'message':'Invalid or missing token'}), 401
        return f(current_user, *args, **kwargs)
    return wrap

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    salt = bcrypt.gensalt()
    pw_hash = bcrypt.hashpw(data['password'].encode(), salt)
    user = User(email=data['email'], pw_hash=pw_hash)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message':'Account created'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if not user or not bcrypt.checkpw(data['password'].encode(), user.pw_hash):
        return jsonify({'message':'Invalid credentials'}), 401
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    return jsonify({'token': token})

@app.route('/sync', methods=['POST'])
@token_required
def sync(current_user):
    client_data = request.json.get('local_data', {})
    current_user.data = jsonify(client_data).get_data(as_text=True)
    db.session.commit()
    return jsonify({'server_data': client_data})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)