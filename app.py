from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from datetime import datetime, timedelta
import bcrypt
import mysql.connector
from functools import wraps

app = Flask(__name__)
CORS(app)

# Database configuration from environment variables
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

ADMIN_API_KEY = os.getenv('ADMIN_API_KEY', 'your-secret-admin-key')

def get_db_connection():
    """Get MySQL database connection"""
    return mysql.connector.connect(**DB_CONFIG)

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def get_user_by_token(token):
    """Get user by session token"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT u.id, u.username, u.is_admin, s.user_id, s.expires_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = %s AND s.expires_at > NOW()
        """, (token,))
        
        result = cursor.fetchone()
        return result
    finally:
        cursor.close()
        conn.close()

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized'}), 401
        
        token = auth_header.split(' ')[1]
        user = get_user_by_token(token)
        
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function

def require_admin_token(f):
    """Decorator to require admin API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_token = request.headers.get('x-admin-token')
        if not admin_token or admin_token != ADMIN_API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    
    return decorated_function

# Health check endpoints
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'message': 'Flask API',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/auth/login, /auth/logout, /auth/me',
            'admin': '/admin/users'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

# Authentication routes
@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id, username, password_hash, is_admin FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if not user or not verify_password(password, user['password_hash']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create session token
        token = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(days=7)
        
        cursor.execute("""
            INSERT INTO sessions (user_id, token, created_at, expires_at)
            VALUES (%s, %s, NOW(), %s)
        """, (user['id'], token, expires_at))
        
        conn.commit()
        
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'is_admin': bool(user['is_admin'])
            }
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/auth/logout', methods=['POST'])
@require_auth
def logout():
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM sessions WHERE token = %s", (token,))
        conn.commit()
        return jsonify({'message': 'Logged out successfully'})
    finally:
        cursor.close()
        conn.close()

@app.route('/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    user = request.current_user
    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'is_admin': bool(user['is_admin'])
    })

# Admin routes
@app.route('/admin/users', methods=['POST'])
@require_admin_token
def create_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    is_admin = data.get('is_admin', False)
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if username already exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({'error': 'Username already exists'}), 400
        
        password_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO users (username, password_hash, is_admin, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (username, password_hash, is_admin))
        
        conn.commit()
        user_id = cursor.lastrowid
        
        return jsonify({
            'id': user_id,
            'username': username,
            'is_admin': is_admin,
            'message': 'User created successfully'
        }), 201
    except mysql.connector.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/users', methods=['GET'])
@require_admin_token
def list_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id, username, is_admin, created_at FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
        
        # Convert datetime to string and is_admin to boolean
        for user in users:
            if user['created_at']:
                user['created_at'] = user['created_at'].isoformat()
            user['is_admin'] = bool(user['is_admin'])
        
        return jsonify({'users': users})
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
@require_admin_token
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute("SELECT id, is_admin FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Only allow deleting non-admin users
        if user[1]:  # is_admin
            return jsonify({'error': 'Cannot delete admin users'}), 403
        
        # Delete user sessions first
        cursor.execute("DELETE FROM sessions WHERE user_id = %s", (user_id,))
        # Delete user
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        conn.commit()
        return jsonify({'message': 'User deleted successfully'})
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/users/<int:user_id>/password', methods=['PATCH'])
@require_admin_token
def update_user_password(user_id):
    data = request.get_json()
    new_password = data.get('password')
    
    if not new_password:
        return jsonify({'error': 'Password required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'User not found'}), 404
        
        password_hash = hash_password(new_password)
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (password_hash, user_id))
        
        conn.commit()
        return jsonify({'message': 'Password updated successfully'})
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

