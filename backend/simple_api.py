from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import datetime
import sqlite3
import os
import hashlib
import json
from domain_scanner import DomainScanner
from llm_analyzer import LLMAnalyzer
from webarchive_analyzer import WebArchiveAnalyzer

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret')

# Инициализация анализаторов
domain_scanner = DomainScanner()
llm_analyzer = LLMAnalyzer()
webarchive_analyzer = WebArchiveAnalyzer()

# Database setup
def init_db():
    conn = sqlite3.connect('data/drop_analyzer.db')
    cursor = conn.cursor()
    
    # Create users table with roles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Create domains table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS domains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT UNIQUE NOT NULL,
            quality_score INTEGER DEFAULT 0,
            total_snapshots INTEGER DEFAULT 0,
            years_covered INTEGER DEFAULT 0,
            ai_category TEXT DEFAULT 'unknown',
            is_good BOOLEAN DEFAULT FALSE,
            recommended BOOLEAN DEFAULT FALSE,
            has_snapshot BOOLEAN DEFAULT FALSE,
            first_snapshot TEXT,
            last_snapshot TEXT,
            description TEXT,
            dns_records TEXT,
            whois_data TEXT,
            ssl_info TEXT,
            is_available BOOLEAN DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            analyzed_at TIMESTAMP
        )
    ''')
    
    # Create reports table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            domain_id INTEGER,
            report_type TEXT DEFAULT 'basic',
            report_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (domain_id) REFERENCES domains (id)
        )
    ''')
    
    # Create settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert demo admin user
    admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password_hash, email, role) 
        VALUES (?, ?, ?, ?)
    ''', ('admin', admin_password, 'admin@example.com', 'admin'))
    
    # Insert demo moderator user
    mod_password = hashlib.sha256('mod123'.encode()).hexdigest()
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password_hash, email, role) 
        VALUES (?, ?, ?, ?)
    ''', ('moderator', mod_password, 'mod@example.com', 'moderator'))
    
    # Insert demo regular user
    user_password = hashlib.sha256('user123'.encode()).hexdigest()
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password_hash, email, role) 
        VALUES (?, ?, ?, ?)
    ''', ('user', user_password, 'user@example.com', 'user'))
    
    # Insert demo domains
    demo_domains = [
        ('example.com', 85, 1234, 15, 'technology', True, True, True, '2008-03-15', '2023-11-20', 'High-quality technology domain with consistent content.'),
        ('test-site.org', 72, 856, 8, 'education', True, False, True, '2015-06-10', '2023-10-15', 'Educational content with good archive coverage.'),
        ('demo-domain.net', 45, 234, 3, 'business', False, False, True, '2020-01-01', '2023-08-30', 'Business domain with limited historical data.'),
        ('quality-site.com', 92, 2156, 18, 'technology', True, True, True, '2005-12-01', '2023-12-01', 'Excellent technology resource with extensive archive.'),
        ('learning-hub.edu', 78, 945, 12, 'education', True, False, True, '2011-09-15', '2023-11-10', 'Educational platform with consistent quality content.')
    ]
    
    for domain_data in demo_domains:
        cursor.execute('''
            INSERT OR IGNORE INTO domains 
            (domain, quality_score, total_snapshots, years_covered, ai_category, is_good, recommended, has_snapshot, first_snapshot, last_snapshot, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', domain_data)
    
    # Insert default settings
    default_settings = [
        ('openrouter_api_key', '', 'OpenRouter API key for LLM analysis'),
        ('openrouter_model', 'openai/gpt-3.5-turbo', 'Default OpenRouter model'),
        ('analysis_prompt', 'Analyze the following domain data and provide insights about its quality, potential, and recommendations for use.', 'Default prompt for LLM analysis'),
        ('report_retention_days', '30', 'Number of days to retain user reports'),
        ('max_domains_per_batch', '10', 'Maximum number of domains per batch analysis')
    ]
    
    for setting in default_settings:
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value, description) 
            VALUES (?, ?, ?)
        ''', setting)
    
    conn.commit()
    conn.close()

# Initialize database
os.makedirs('data', exist_ok=True)
init_db()

def generate_token(user_id, username, role):
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token:
            token = token.replace('Bearer ', '')
        
        if not token:
            return jsonify({'message': 'Token required'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'message': 'Invalid token'}), 401
        
        request.current_user = payload
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

def require_admin(f):
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user') or request.current_user.get('role') != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

# Auth routes
@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400
    
    conn = sqlite3.connect('data/drop_analyzer.db')
    cursor = conn.cursor()
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute('SELECT id, username, role, is_active FROM users WHERE username = ? AND password_hash = ?', (username, password_hash))
    user = cursor.fetchone()
    
    if user and user[3]:  # Check if user is active
        # Update last login
        cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user[0],))
        conn.commit()
        conn.close()
        
        token = generate_token(user[0], user[1], user[2])
        return jsonify({
            'access_token': token, 
            'user': {
                'id': user[0],
                'username': user[1],
                'role': user[2]
            },
            'message': 'Login successful'
        })
    else:
        conn.close()
        return jsonify({'message': 'Invalid credentials or account disabled'}), 401

@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email', '')
    
    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400
    
    conn = sqlite3.connect('data/drop_analyzer.db')
    cursor = conn.cursor()
    
    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute('INSERT INTO users (username, password_hash, email, role) VALUES (?, ?, ?, ?)', 
                      (username, password_hash, email, 'user'))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        token = generate_token(user_id, username, 'user')
        return jsonify({
            'access_token': token, 
            'user': {
                'id': user_id,
                'username': username,
                'role': 'user'
            },
            'message': 'Registration successful'
        }), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'message': 'Username already exists'}), 400

# Admin routes
@app.route('/api/v1/admin/users', methods=['GET'])
@require_auth
@require_admin
def get_users():
    conn = sqlite3.connect('data/drop_analyzer.db')
    cursor = conn.cursor()
    
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    search = request.args.get('search', '')
    
    query = 'SELECT id, username, email, role, is_active, created_at, last_login FROM users'
    params = []
    
    if search:
        query += ' WHERE username LIKE ? OR email LIKE ?'
        params.extend([f'%{search}%', f'%{search}%'])
    
    query += ' ORDER BY created_at DESC'
    query += f' LIMIT {per_page} OFFSET {(page - 1) * per_page}'
    
    cursor.execute(query, params)
    users = cursor.fetchall()
    
    # Get total count
    count_query = 'SELECT COUNT(*) FROM users'
    if search:
        count_query += ' WHERE username LIKE ? OR email LIKE ?'
        cursor.execute(count_query, [f'%{search}%', f'%{search}%'])
    else:
        cursor.execute(count_query)
    
    total = cursor.fetchone()[0]
    conn.close()
    
    user_list = []
    for user in users:
        user_list.append({
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'role': user[3],
            'is_active': bool(user[4]),
            'created_at': user[5],
            'last_login': user[6]
        })
    
    return jsonify({
        'users': user_list,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })

@app.route('/api/v1/admin/users', methods=['POST'])
@require_auth
@require_admin
def create_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email', '')
    role = data.get('role', 'user')
    
    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400
    
    if role not in ['admin', 'moderator', 'user']:
        return jsonify({'message': 'Invalid role'}), 400
    
    conn = sqlite3.connect('data/drop_analyzer.db')
    cursor = conn.cursor()
    
    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute('INSERT INTO users (username, password_hash, email, role) VALUES (?, ?, ?, ?)', 
                      (username, password_hash, email, role))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'id': user_id,
            'username': username,
            'email': email,
            'role': role,
            'message': 'User created successfully'
        }), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'message': 'Username already exists'}), 400

@app.route('/api/v1/admin/users/<int:user_id>', methods=['PUT'])
@require_auth
@require_admin
def update_user(user_id):
    data = request.get_json()
    
    conn = sqlite3.connect('data/drop_analyzer.db')
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'message': 'User not found'}), 404
    
    # Update user
    updates = []
    params = []
    
    if 'email' in data:
        updates.append('email = ?')
        params.append(data['email'])
    
    if 'role' in data and data['role'] in ['admin', 'moderator', 'user']:
        updates.append('role = ?')
        params.append(data['role'])
    
    if 'is_active' in data:
        updates.append('is_active = ?')
        params.append(data['is_active'])
    
    if 'password' in data and data['password']:
        updates.append('password_hash = ?')
        params.append(hashlib.sha256(data['password'].encode()).hexdigest())
    
    if updates:
        params.append(user_id)
        query = f'UPDATE users SET {", ".join(updates)} WHERE id = ?'
        cursor.execute(query, params)
        conn.commit()
    
    conn.close()
    return jsonify({'message': 'User updated successfully'})

@app.route('/api/v1/admin/users/<int:user_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_user(user_id):
    conn = sqlite3.connect('data/drop_analyzer.db')
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'message': 'User not found'}), 404
    
    # Delete user
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'User deleted successfully'})

# Domain routes
@app.route('/api/v1/domains/analyze', methods=['POST'])
@require_auth
def analyze_domains():
    data = request.get_json()
    domains = data.get('domains', [])
    
    if not domains:
        return jsonify({'message': 'No domains provided'}), 400
    
    results = domain_scanner.batch_analyze_domains(domains)
    
    # Save to database
    conn = sqlite3.connect('data/drop_analyzer.db')
    cursor = conn.cursor()
    
    for result in results['domains']:
        if 'error' not in result:
            dns_json = json.dumps(result['dns_records'])
            whois_json = json.dumps(result['whois_info'])
            ssl_json = json.dumps(result['ssl_info'])
            
            cursor.execute('''
                INSERT OR REPLACE INTO domains 
                (domain, quality_score, dns_records, whois_data, ssl_info, is_available, analyzed_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (result['domain'], result['quality_score'], dns_json, whois_json, ssl_json, result['is_available']))
    
    conn.commit()
    conn.close()
    
    return jsonify(results)

@app.route('/api/v1/domains/llm-analyze', methods=['POST'])
@require_auth
def llm_analyze_domains():
    data = request.get_json()
    domains_data = data.get('domains', [])
    
    if not domains_data:
        return jsonify({'message': 'No domains provided'}), 400
    
    results = llm_analyzer.analyze_domains_with_llm(domains_data)
    
    return jsonify(results)

@app.route('/api/v1/domains', methods=['GET'])
@require_auth
def get_domains():
    conn = sqlite3.connect('data/drop_analyzer.db')
    cursor = conn.cursor()
    
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    cursor.execute('''
        SELECT * FROM domains
        ORDER BY analyzed_at DESC
        LIMIT ? OFFSET ?
    ''', (per_page, (page - 1) * per_page))
    
    domains = cursor.fetchall()
    
    cursor.execute('SELECT COUNT(*) FROM domains')
    total = cursor.fetchone()[0]
    
    conn.close()
    
    domain_list = []
    for domain in domains:
        domain_dict = {
            'id': domain[0],
            'domain': domain[1],
            'quality_score': domain[2],
            'total_snapshots': domain[3],
            'years_covered': domain[4],
            'ai_category': domain[5],
            'is_good': bool(domain[6]),
            'recommended': bool(domain[7]),
            'has_snapshot': bool(domain[8]),
            'first_snapshot': domain[9],
            'last_snapshot': domain[10],
            'description': domain[11],
            'dns_records': json.loads(domain[12]) if domain[12] else {},
            'whois_data': json.loads(domain[13]) if domain[13] else {},
            'ssl_info': json.loads(domain[14]) if domain[14] else {},
            'is_available': bool(domain[15]) if domain[15] is not None else None,
            'created_at': domain[16],
            'analyzed_at': domain[17]
        }
        domain_list.append(domain_dict)
    
    return jsonify({
        'domains': domain_list,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })

# Reports routes
@app.route('/api/v1/reports', methods=['GET'])
@require_auth
def get_reports():
    conn = sqlite3.connect('data/drop_analyzer.db')
    cursor = conn.cursor()
    
    user_id = request.current_user['user_id']
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    cursor.execute('''
        SELECT r.id, r.report_type, r.report_data, r.created_at, d.domain
        FROM reports r
        LEFT JOIN domains d ON r.domain_id = d.id
        WHERE r.user_id = ?
        ORDER BY r.created_at DESC
        LIMIT ? OFFSET ?
    ''', (user_id, per_page, (page - 1) * per_page))
    
    reports = cursor.fetchall()
    
    cursor.execute('SELECT COUNT(*) FROM reports WHERE user_id = ?', (user_id,))
    total = cursor.fetchone()[0]
    
    conn.close()
    
    report_list = []
    for report in reports:
        report_list.append({
            'id': report[0],
            'type': report[1],
            'data': json.loads(report[2]) if report[2] else {},
            'created_at': report[3],
            'domain': report[4]
        })
    
    return jsonify({
        'reports': report_list,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })

@app.route('/api/v1/reports/<int:report_id>', methods=['DELETE'])
@require_auth
def delete_report(report_id):
    conn = sqlite3.connect('data/drop_analyzer.db')
    cursor = conn.cursor()
    
    user_id = request.current_user['user_id']
    
    cursor.execute('DELETE FROM reports WHERE id = ? AND user_id = ?', (report_id, user_id))
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'message': 'Report not found or access denied'}), 404
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Report deleted successfully'})

# Settings routes
@app.route('/api/v1/settings', methods=['GET'])
@require_auth
@require_admin
def get_settings():
    conn = sqlite3.connect('data/drop_analyzer.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT key, value FROM settings')
    settings = dict(cursor.fetchall())
    
    conn.close()
    
    return jsonify(settings)

@app.route('/api/v1/settings', methods=['PUT'])
@require_auth
@require_admin
def update_settings():
    data = request.get_json()
    
    conn = sqlite3.connect('data/drop_analyzer.db')
    cursor = conn.cursor()
    
    for key, value in data.items():
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
        ''', (key, value))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Settings updated successfully'})

# Health check
@app.route('/api/v1/health', methods=['GET'])
def health():
    return jsonify({
        'success': True,
        'message': 'API is healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)