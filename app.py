from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import hashlib
import sqlite3
from datetime import datetime
from database import init_database, get_db_connection
from price_predictor import CarPricePredictor
from invoice_generator import InvoiceGenerator
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id, username, email, full_name, is_admin=False):
        self.id = user_id
        self.username = username
        self.email = email
        self.full_name = full_name
        self.is_admin = is_admin

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user['id'], user['username'], user['email'], user['full_name'], user['is_admin'])
    return None

# Initialize database on first run
if not os.path.exists('car_predictor.db'):
    init_database()

predictor = CarPricePredictor()
invoice_gen = InvoiceGenerator()

# Indian number formatting function
def format_indian_currency(amount):
    """Format number in Indian style (lakhs/crores) with commas"""
    if amount == 0:
        return "0"
    
    amount = int(amount)
    if amount < 0:
        return "-" + format_indian_currency(-amount)
    
    # Convert to string and reverse for easier processing
    s = str(amount)
    
    # Handle numbers less than 1000
    if len(s) <= 3:
        return s
    
    # For numbers >= 1000, apply Indian formatting
    result = s[-3:]  # Last 3 digits
    s = s[:-3]
    
    # Add groups of 2 digits from right to left
    while len(s) > 0:
        if len(s) >= 2:
            result = s[-2:] + "," + result
            s = s[:-2]
        else:
            result = s + "," + result
            s = ""
    
    return result

# Register the filter with Jinja2
app.jinja_env.filters['indian_currency'] = format_indian_currency

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_home'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password_hash = ?',
            (username, password_hash)
        ).fetchone()
        
        if user:
            # Update last login
            conn.execute(
                'UPDATE users SET last_login = ? WHERE id = ?',
                (datetime.now(), user['id'])
            )
            conn.commit()
            conn.close()
            
            user_obj = User(user['id'], user['username'], user['email'], user['full_name'], user['is_admin'])
            login_user(user_obj)
            
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            conn.close()
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        phone = request.form['phone']
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, email, password_hash, full_name, phone) VALUES (?, ?, ?, ?, ?)',
                (username, email, password_hash, full_name, phone)
            )
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Username or email already exists', 'error')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/user/dashboard_old')
@login_required
def user_dashboard_old():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    conn = get_db_connection()
    predictions_rows = conn.execute('''
        SELECT p.*, c.brand, c.model, c.year 
        FROM predictions p 
        JOIN cars c ON p.car_id = c.id 
        WHERE p.user_id = ? 
        ORDER BY p.prediction_date DESC
    ''', (current_user.id,)).fetchall()
    conn.close()
    
    # Convert Row objects to dictionaries for JSON serialization
    predictions = [dict(prediction) for prediction in predictions_rows]
    
    return render_template('user_dashboard.html', predictions=predictions)

@app.route('/user/predict', methods=['GET', 'POST'])
@login_required
def predict_price():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        car_id = request.form['car_id']
        car_age = int(request.form['car_age'])
        condition = request.form['condition']
        kilometers_driven = int(request.form['kilometers_driven'])
        state = request.form['state']
        city = request.form['city']
        
        # Get car details
        conn = get_db_connection()
        car_row = conn.execute('SELECT * FROM cars WHERE id = ?', (car_id,)).fetchone()
        
        if car_row:
            car = dict(car_row)
            # Calculate predicted price with new parameters (without area_type)
            predicted_price = predictor.predict_price(car_id, car_age, condition, kilometers_driven, state, city)
            
            # Store prediction in database with new fields
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO predictions (user_id, car_id, car_age, car_condition, kilometers_driven, city, predicted_price, state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (current_user.id, car_id, car_age, condition, kilometers_driven, city, predicted_price, state))
            conn.commit()
            prediction_id = cursor.lastrowid
            conn.close()
            
            return redirect(url_for('prediction_result', prediction_id=prediction_id))
        else:
            flash('Error in price prediction', 'error')
    
    # Get all cars for dropdown
    conn = get_db_connection()
    cars_rows = conn.execute('SELECT * FROM cars ORDER BY brand, model').fetchall()
    conn.close()
    
    # Convert Row objects to dictionaries for JSON serialization
    cars = [dict(car) for car in cars_rows]
    
    return render_template('predict.html', cars=cars)

@app.route('/user/prediction/<int:prediction_id>')
@login_required
def prediction_result(prediction_id):
    conn = get_db_connection()
    prediction_row = conn.execute(
        '''SELECT p.*, c.brand, c.model, c.year, c.fuel_type, c.transmission
           FROM predictions p 
           JOIN cars c ON p.car_id = c.id 
           WHERE p.id = ? AND p.user_id = ?''',
        (prediction_id, current_user.id)
    ).fetchone()
    conn.close()
    
    if not prediction_row:
        flash('Prediction not found', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Convert Row object to dictionary
    prediction = dict(prediction_row)
    
    # Get detailed breakdown
    breakdown = predictor.get_price_breakdown(
        prediction['car_id'], 
        prediction['car_age'], 
        prediction['car_condition'], 
        prediction['kilometers_driven'], 
        prediction['state'],
        prediction['city']
    )
    
    return render_template('prediction_result.html', prediction=prediction, breakdown=breakdown)

@app.route('/user/generate_invoice/<int:prediction_id>')
@login_required
def generate_invoice(prediction_id):
    conn = get_db_connection()
    prediction_row = conn.execute(
        '''SELECT p.*, c.brand, c.model, c.year, u.full_name, u.email, u.phone
           FROM predictions p 
           JOIN cars c ON p.car_id = c.id 
           JOIN users u ON p.user_id = u.id
           WHERE p.id = ? AND p.user_id = ?''',
        (prediction_id, current_user.id)
    ).fetchone()
    
    if not prediction_row:
        conn.close()
        flash('Prediction not found', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Convert Row object to dictionary
    prediction = dict(prediction_row)
    
    # Check if invoice already exists
    existing_invoice_row = conn.execute(
        'SELECT * FROM invoices WHERE prediction_id = ?', (prediction_id,)
    ).fetchone()
    
    if existing_invoice_row:
        conn.close()
        return redirect(url_for('view_invoice', invoice_id=existing_invoice_row['id']))
    
    # Generate new invoice
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{prediction_id:04d}"
    service_charge = 500
    total_amount = service_charge
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO invoices (prediction_id, invoice_number, user_id, amount, service_charge, total_amount)
        VALUES (?, ?, ?, ?, ?, ?)''',
        (prediction_id, invoice_number, current_user.id, 0, service_charge, total_amount)
    )
    
    # Mark prediction as having invoice generated
    cursor.execute(
        'UPDATE predictions SET invoice_generated = TRUE WHERE id = ?', (prediction_id,)
    )
    
    conn.commit()
    invoice_id = cursor.lastrowid
    conn.close()
    
    return redirect(url_for('view_invoice', invoice_id=invoice_id))

@app.route('/user/invoice/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    conn = get_db_connection()
    invoice_row = conn.execute(
        '''SELECT i.*, p.predicted_price, p.car_condition, p.kilometers_driven, p.city,
                  c.brand, c.model, c.year, u.full_name, u.email, u.phone
           FROM invoices i
           JOIN predictions p ON i.prediction_id = p.id
           JOIN cars c ON p.car_id = c.id
           JOIN users u ON i.user_id = u.id
           WHERE i.id = ? AND i.user_id = ?''',
        (invoice_id, current_user.id)
    ).fetchone()
    conn.close()
    
    if not invoice_row:
        flash('Invoice not found', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Convert Row object to dictionary
    invoice = dict(invoice_row)
    
    return render_template('invoice.html', invoice=invoice)

@app.route('/user/home')
@login_required
def user_home():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    conn = get_db_connection()
    
    # Get user statistics
    user_predictions = conn.execute('''
        SELECT COUNT(*) as count FROM predictions WHERE user_id = ?
    ''', (current_user.id,)).fetchone()['count']
    
    user_invoices = conn.execute('''
        SELECT COUNT(*) as count FROM invoices 
        WHERE prediction_id IN (SELECT id FROM predictions WHERE user_id = ?)
    ''', (current_user.id,)).fetchone()['count']
    
    avg_prediction = conn.execute('''
        SELECT AVG(predicted_price) as avg FROM predictions WHERE user_id = ?
    ''', (current_user.id,)).fetchone()['avg']
    
    last_prediction = conn.execute('''
        SELECT prediction_date FROM predictions 
        WHERE user_id = ? ORDER BY prediction_date DESC LIMIT 1
    ''', (current_user.id,)).fetchone()
    
    # Get recent predictions with car details (limit to 3 for home page)
    recent_predictions_rows = conn.execute('''
        SELECT p.*, c.brand, c.model, c.year 
        FROM predictions p
        JOIN cars c ON p.car_id = c.id
        WHERE p.user_id = ?
        ORDER BY p.prediction_date DESC
        LIMIT 3
    ''', (current_user.id,)).fetchall()
    
    conn.close()
    
    # Convert to dictionaries for JSON serialization
    recent_predictions = [dict(row) for row in recent_predictions_rows]
    
    user_stats = {
        'total_predictions': user_predictions,
        'total_invoices': user_invoices,
        'avg_prediction': avg_prediction,
        'last_prediction_date': last_prediction['prediction_date'] if last_prediction else None
    }
    
    return render_template('user_home.html', 
                         user_stats=user_stats, 
                         recent_predictions=recent_predictions)

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    conn = get_db_connection()
    
    # Get user statistics
    user_predictions = conn.execute('''
        SELECT COUNT(*) as count FROM predictions WHERE user_id = ?
    ''', (current_user.id,)).fetchone()['count']
    
    user_invoices = conn.execute('''
        SELECT COUNT(*) as count FROM invoices 
        WHERE prediction_id IN (SELECT id FROM predictions WHERE user_id = ?)
    ''', (current_user.id,)).fetchone()['count']
    
    avg_prediction = conn.execute('''
        SELECT AVG(predicted_price) as avg FROM predictions WHERE user_id = ?
    ''', (current_user.id,)).fetchone()['avg']
    
    highest_prediction = conn.execute('''
        SELECT MAX(predicted_price) as max FROM predictions WHERE user_id = ?
    ''', (current_user.id,)).fetchone()['max']
    
    last_prediction = conn.execute('''
        SELECT prediction_date FROM predictions 
        WHERE user_id = ? ORDER BY prediction_date DESC LIMIT 1
    ''', (current_user.id,)).fetchone()
    
    # Get all predictions with car details for dashboard
    recent_predictions_rows = conn.execute('''
        SELECT p.*, c.brand, c.model, c.year 
        FROM predictions p
        JOIN cars c ON p.car_id = c.id
        WHERE p.user_id = ?
        ORDER BY p.prediction_date DESC
    ''', (current_user.id,)).fetchall()
    
    conn.close()
    
    # Convert to dictionaries for JSON serialization
    recent_predictions = [dict(row) for row in recent_predictions_rows]
    
    user_stats = {
        'total_predictions': user_predictions,
        'total_invoices': user_invoices,
        'avg_prediction': avg_prediction,
        'highest_prediction': highest_prediction,
        'last_prediction_date': last_prediction['prediction_date'] if last_prediction else None
    }
    
    return render_template('user_dashboard.html', 
                         user_stats=user_stats, 
                         predictions=recent_predictions)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('user_home'))
    
    conn = get_db_connection()
    
    # Get comprehensive analytics data
    total_users = conn.execute('SELECT COUNT(*) as count FROM users WHERE is_admin = FALSE').fetchone()['count']
    total_predictions = conn.execute('SELECT COUNT(*) as count FROM predictions').fetchone()['count']
    total_cars = conn.execute('SELECT COUNT(*) as count FROM cars').fetchone()['count']
    total_invoices = conn.execute('SELECT COUNT(*) as count FROM invoices').fetchone()['count']
    
    # Recent predictions
    recent_predictions_rows = conn.execute('''
        SELECT p.*, c.brand, c.model, c.year, u.username
        FROM predictions p
        JOIN cars c ON p.car_id = c.id
        JOIN users u ON p.user_id = u.id
        ORDER BY p.prediction_date DESC
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    # Convert to dictionaries for JSON serialization
    recent_predictions = [dict(row) for row in recent_predictions_rows]
    
    dashboard_stats = {
        'total_users': total_users,
        'total_predictions': total_predictions,
        'total_cars': total_cars,
        'total_invoices': total_invoices
    }
    
    return render_template('admin_dashboard.html', 
                         stats=dashboard_stats, 
                         recent_predictions=recent_predictions)

@app.route('/admin/cars')
@login_required
def admin_cars():
    if not current_user.is_admin:
        return redirect(url_for('user_dashboard'))
    
    conn = get_db_connection()
    cars_rows = conn.execute('SELECT * FROM cars ORDER BY brand, model').fetchall()
    conn.close()
    
    # Convert Row objects to dictionaries for JSON serialization
    cars = [dict(car) for car in cars_rows]
    
    return render_template('admin_cars.html', cars=cars)

@app.route('/admin/add_car', methods=['GET', 'POST'])
@login_required
def admin_add_car():
    if not current_user.is_admin:
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        brand = request.form['brand']
        model = request.form['model']
        year = int(request.form['year'])
        fuel_type = request.form['fuel_type']
        transmission = request.form['transmission']
        engine_capacity = float(request.form['engine_capacity'])
        mileage = float(request.form['mileage'])
        base_price = int(request.form['base_price'])
        depreciation_rate = float(request.form['depreciation_rate'])
        
        conn = get_db_connection()
        conn.execute(
            '''INSERT INTO cars (brand, model, year, fuel_type, transmission, engine_capacity, mileage, base_price, depreciation_rate)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (brand, model, year, fuel_type, transmission, engine_capacity, mileage, base_price, depreciation_rate)
        )
        conn.commit()
        conn.close()
        
        flash('Car added successfully!', 'success')
        return redirect(url_for('admin_cars'))
    
    return render_template('admin_add_car.html')

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        return redirect(url_for('user_dashboard'))
    
    conn = get_db_connection()
    users_rows = conn.execute('SELECT * FROM users WHERE is_admin = FALSE ORDER BY created_at DESC').fetchall()
    conn.close()
    
    # Convert Row objects to dictionaries for JSON serialization
    users = [dict(user) for user in users_rows]
    
    return render_template('admin_users.html', users=users)

@app.route('/admin/user/<int:user_id>/details')
@login_required
def admin_user_details(user_id):
    if not current_user.is_admin:
        return redirect(url_for('user_dashboard'))
    
    conn = get_db_connection()
    user_row = conn.execute('SELECT * FROM users WHERE id = ? AND is_admin = FALSE', (user_id,)).fetchone()
    
    if not user_row:
        conn.close()
        flash('User not found', 'error')
        return redirect(url_for('admin_users'))
    
    user = dict(user_row)
    
    # Get user statistics
    total_predictions = conn.execute('SELECT COUNT(*) as count FROM predictions WHERE user_id = ?', (user_id,)).fetchone()['count']
    total_invoices = conn.execute('SELECT COUNT(*) as count FROM invoices WHERE user_id = ?', (user_id,)).fetchone()['count']
    avg_prediction_price = conn.execute('SELECT AVG(predicted_price) as avg FROM predictions WHERE user_id = ?', (user_id,)).fetchone()['avg']
    
    conn.close()
    
    user_stats = {
        'total_predictions': total_predictions,
        'total_invoices': total_invoices,
        'avg_prediction_price': avg_prediction_price or 0
    }
    
    return render_template('admin_user_details.html', user=user, stats=user_stats)

@app.route('/admin/user/<int:user_id>/predictions')
@login_required
def admin_user_predictions(user_id):
    if not current_user.is_admin:
        return redirect(url_for('user_dashboard'))
    
    conn = get_db_connection()
    user_row = conn.execute('SELECT username, full_name FROM users WHERE id = ? AND is_admin = FALSE', (user_id,)).fetchone()
    
    if not user_row:
        conn.close()
        flash('User not found', 'error')
        return redirect(url_for('admin_users'))
    
    user = dict(user_row)
    
    # Get user's predictions
    predictions_rows = conn.execute('''
        SELECT p.*, c.brand, c.model, c.year 
        FROM predictions p 
        JOIN cars c ON p.car_id = c.id 
        WHERE p.user_id = ? 
        ORDER BY p.prediction_date DESC
    ''', (user_id,)).fetchall()
    
    conn.close()
    
    predictions = [dict(prediction) for prediction in predictions_rows]
    
    return render_template('admin_user_predictions.html', user=user, predictions=predictions)

@app.route('/admin/analytics')
@login_required
def admin_analytics():
    if not current_user.is_admin:
        return redirect(url_for('user_dashboard'))
    
    conn = get_db_connection()
    
    # Get comprehensive analytics data
    total_users = conn.execute('SELECT COUNT(*) as count FROM users WHERE is_admin = FALSE').fetchone()['count']
    total_predictions = conn.execute('SELECT COUNT(*) as count FROM predictions').fetchone()['count']
    total_cars = conn.execute('SELECT COUNT(*) as count FROM cars').fetchone()['count']
    total_invoices = conn.execute('SELECT COUNT(*) as count FROM invoices').fetchone()['count']
    
    # Monthly predictions
    monthly_predictions = conn.execute('''
        SELECT strftime('%Y-%m', prediction_date) as month, COUNT(*) as count
        FROM predictions 
        GROUP BY strftime('%Y-%m', prediction_date)
        ORDER BY month DESC LIMIT 12
    ''').fetchall()
    
    # Top car brands by predictions
    brand_stats = conn.execute('''
        SELECT c.brand, COUNT(*) as prediction_count
        FROM predictions p
        JOIN cars c ON p.car_id = c.id
        GROUP BY c.brand
        ORDER BY prediction_count DESC LIMIT 10
    ''').fetchall()
    
    # City-wise predictions
    city_stats = conn.execute('''
        SELECT city, COUNT(*) as count
        FROM predictions
        GROUP BY city
        ORDER BY count DESC LIMIT 10
    ''').fetchall()
    
    # Average predicted prices by brand
    avg_prices = conn.execute('''
        SELECT c.brand, AVG(p.predicted_price) as avg_price
        FROM predictions p
        JOIN cars c ON p.car_id = c.id
        GROUP BY c.brand
        ORDER BY avg_price DESC
    ''').fetchall()
    
    conn.close()
    
    # Convert Row objects to dictionaries for JSON serialization
    analytics_data = {
        'total_users': total_users,
        'total_predictions': total_predictions,
        'total_cars': total_cars,
        'total_invoices': total_invoices,
        'monthly_predictions': [dict(row) for row in monthly_predictions],
        'brand_stats': [dict(row) for row in brand_stats],
        'city_stats': [dict(row) for row in city_stats],
        'avg_prices': [dict(row) for row in avg_prices]
    }
    
    return render_template('admin_analytics.html', data=analytics_data)

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if not current_user.is_admin:
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        # Handle settings update
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin_settings'))
    
    return render_template('admin_settings.html')

@app.route('/admin/export')
@login_required
def admin_export():
    if not current_user.is_admin:
        return redirect(url_for('user_dashboard'))
    
    export_type = request.args.get('type', 'users')
    
    conn = get_db_connection()
    
    if export_type == 'users':
        data_rows = conn.execute('SELECT * FROM users WHERE is_admin = FALSE').fetchall()
        data = [dict(row) for row in data_rows]
        filename = 'users_export.csv'
    elif export_type == 'predictions':
        data_rows = conn.execute('''
            SELECT p.*, c.brand, c.model, u.username
            FROM predictions p
            JOIN cars c ON p.car_id = c.id
            JOIN users u ON p.user_id = u.id
        ''').fetchall()
        data = [dict(row) for row in data_rows]
        filename = 'predictions_export.csv'
    elif export_type == 'cars':
        data_rows = conn.execute('SELECT * FROM cars').fetchall()
        data = [dict(row) for row in data_rows]
        filename = 'cars_export.csv'
    else:
        data_rows = conn.execute('SELECT * FROM invoices').fetchall()
        data = [dict(row) for row in data_rows]
        filename = 'invoices_export.csv'
    
    conn.close()
    
    # Create CSV content
    import csv
    import io
    from flask import Response
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    if data:
        # Write header
        writer.writerow(data[0].keys())
        # Write data
        for row in data:
            writer.writerow([str(value) if value is not None else '' for value in row.values()])
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={filename}',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )

@app.route('/admin/export_page')
@login_required
def admin_export_page():
    if not current_user.is_admin:
        return redirect(url_for('user_dashboard'))
    
    return render_template('admin_export.html')

@app.route('/download_invoice_pdf/<int:invoice_id>')
@login_required
def download_invoice_pdf(invoice_id):
    # Add debug parameter to force download
    force_download = request.args.get('download', 'false').lower() == 'true'
    conn = get_db_connection()
    invoice = conn.execute('''
        SELECT i.*, p.predicted_price, p.car_age, p.kilometers_driven, p.car_condition, p.city, p.state, p.user_id,
               c.brand, c.model, c.year, u.username, u.email, u.full_name, u.phone
        FROM invoices i
        JOIN predictions p ON i.prediction_id = p.id
        JOIN cars c ON p.car_id = c.id
        JOIN users u ON p.user_id = u.id
        WHERE i.id = ?
    ''', (invoice_id,)).fetchone()
    
    if not invoice:
        conn.close()
        return "Invoice not found", 404
    
    # Check if user owns this invoice or is admin
    if not current_user.is_admin and invoice['user_id'] != current_user.id:
        conn.close()
        return "Access denied", 403
    
    conn.close()
    
    # Generate PDF using ReportLab
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from flask import Response
        import io
        from datetime import datetime
    except ImportError:
        return "PDF generation not available. Please install reportlab.", 500
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#2c3e50')
    )
    
    # Title
    elements.append(Paragraph("Car Price Predictor", title_style))
    elements.append(Paragraph("Price Prediction Invoice", styles['Heading2']))
    elements.append(Spacer(1, 20))
    
    # Invoice details
    invoice_data = [
        ['Invoice ID:', f"INV-{invoice['id']:06d}"],
        ['Date:', datetime.now().strftime('%d %B %Y')],
        ['Customer:', invoice['username']],
        ['Email:', invoice['email']],
    ]
    
    invoice_table = Table(invoice_data, colWidths=[2*inch, 4*inch])
    invoice_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    elements.append(invoice_table)
    elements.append(Spacer(1, 30))
    
    # Car details
    elements.append(Paragraph("Car Details", styles['Heading3']))
    car_data = [
        ['Brand:', invoice['brand']],
        ['Model:', invoice['model']],
        ['Year:', str(invoice['year'])],
        ['Age:', f"{invoice['car_age']} years"],
        ['Condition:', invoice['car_condition'].title()],
        ['Kilometers:', f"{invoice['kilometers_driven']:,} km"],
        ['Location:', f"{invoice['city']}, {invoice['state']}"],
    ]
    
    car_table = Table(car_data, colWidths=[2*inch, 4*inch])
    car_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
    ]))
    
    elements.append(car_table)
    elements.append(Spacer(1, 30))
    
    # Price details
    elements.append(Paragraph("Price Prediction", styles['Heading3']))
    price_style = ParagraphStyle(
        'PriceStyle',
        parent=styles['Normal'],
        fontSize=18,
        textColor=colors.HexColor('#27ae60'),
        alignment=1  # Center alignment
    )
    
    elements.append(Paragraph(f"Predicted Price: ₹{invoice['predicted_price']:,}", price_style))
    elements.append(Spacer(1, 20))
    
    # Footer
    elements.append(Spacer(1, 50))
    footer_text = """
    <para align="center">
    <b>Car Price Predictor</b><br/>
    Thank you for using our service!<br/>
    This prediction is based on current market conditions and provided information.
    </para>
    """
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF with error handling
    try:
        doc.build(elements)
    except Exception as e:
        buffer.close()
        return f"Error building PDF: {str(e)}", 500
    
    # Get the value of the BytesIO buffer and return as response
    pdf_data = buffer.getvalue()
    buffer.close()
    
    # Validate PDF starts with proper PDF header
    if not pdf_data.startswith(b'%PDF-'):
        return "Invalid PDF generated", 500
    
    filename = f"invoice_INV-{invoice['id']:06d}.pdf"
    
    # Validate PDF data
    if len(pdf_data) < 100:  # PDF should be at least 100 bytes
        return "Error generating PDF", 500
    
    # Ensure proper PDF file extension
    if not filename.endswith('.pdf'):
        filename = filename + '.pdf'
    
    # Try inline display first, fallback to attachment
    response = Response(
        pdf_data,
        mimetype='application/pdf'
    )
    
    # Always force download, no preview
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Length'] = str(len(pdf_data))
    
    return response

@app.route('/about')
@app.route('/about-us')
def about_us():
    return render_template('about_us.html')

@app.route('/contact', methods=['POST'])
def contact_form():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Here you could save to database or send email
        # For now, we'll just flash a success message
        flash('Thank you for your message! We will get back to you soon.', 'success')
        
        return redirect(url_for('about_us'))

@app.route('/api/cars/<brand>')
def api_cars_by_brand(brand):
    conn = get_db_connection()
    cars = conn.execute('SELECT * FROM cars WHERE brand = ? ORDER BY model', (brand,)).fetchall()
    conn.close()
    
    return jsonify([dict(car) for car in cars])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
