from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wifi_billing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), default='customer')  # admin or customer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with subscriptions
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)
    invoices = db.relationship('Invoice', backref='user', lazy=True)

class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    speed = db.Column(db.String(50), nullable=False)  # e.g., "10 Mbps"
    data_limit = db.Column(db.String(50), nullable=False)  # e.g., "Unlimited" or "100 GB"
    price = db.Column(db.Float, nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)  # e.g., 30 for monthly
    description = db.Column(db.Text)
    
    # Relationship with subscriptions
    subscriptions = db.relationship('Subscription', backref='package', lazy=True)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, expired, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, paid, overdue
    due_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    payment_date = db.Column(db.DateTime)

# Helper functions
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))
        
        password_hash = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=password_hash)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    active_subscription = Subscription.query.filter_by(
        user_id=user.id, 
        status='active'
    ).filter(Subscription.end_date > datetime.utcnow()).first()
    
    invoices = Invoice.query.filter_by(user_id=user.id).order_by(Invoice.created_at.desc()).limit(5).all()
    
    if user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    packages = Package.query.all()
    return render_template('dashboard.html', 
                         user=user, 
                         active_subscription=active_subscription,
                         invoices=invoices,
                         packages=packages)

@app.route('/subscribe/<int:package_id>', methods=['POST'])
@login_required
def subscribe(package_id):
    package = Package.query.get_or_404(package_id)
    user = User.query.get(session['user_id'])
    
    # Check for existing active subscription
    existing_active = Subscription.query.filter_by(
        user_id=user.id, 
        status='active'
    ).filter(Subscription.end_date > datetime.utcnow()).first()
    
    if existing_active:
        flash('You already have an active subscription.', 'warning')
        return redirect(url_for('dashboard'))
    
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=package.duration_days)
    
    new_subscription = Subscription(
        user_id=user.id,
        package_id=package.id,
        start_date=start_date,
        end_date=end_date,
        status='active'
    )
    
    # Create invoice
    new_invoice = Invoice(
        user_id=user.id,
        subscription_id=new_subscription.id,
        amount=package.price,
        status='paid',  # Simplified - in real system would process payment
        due_date=start_date,
        payment_date=datetime.utcnow()
    )
    
    try:
        db.session.add(new_subscription)
        db.session.add(new_invoice)
        db.session.commit()
        flash(f'Subscribed to {package.name} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while subscribing.', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/invoices')
@login_required
def invoices():
    user = User.query.get(session['user_id'])
    if user.role == 'admin':
        return redirect(url_for('admin_invoices'))
    
    user_invoices = Invoice.query.filter_by(user_id=user.id).order_by(Invoice.created_at.desc()).all()
    return render_template('invoices.html', invoices=user_invoices)

# Admin Routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    total_users = User.query.filter_by(role='customer').count()
    active_subscriptions = Subscription.query.filter_by(status='active').filter(
        Subscription.end_date > datetime.utcnow()
    ).count()
    total_revenue = db.session.query(db.func.sum(Invoice.amount)).filter(
        Invoice.status == 'paid'
    ).scalar() or 0
    
    recent_subscriptions = Subscription.query.order_by(Subscription.created_at.desc()).limit(10).all()
    packages = Package.query.all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_subscriptions=active_subscriptions,
                         total_revenue=total_revenue,
                         recent_subscriptions=recent_subscriptions,
                         packages=packages)

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.filter_by(role='customer').order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/packages', methods=['GET', 'POST'])
@admin_required
def admin_packages():
    if request.method == 'POST':
        name = request.form.get('name')
        speed = request.form.get('speed')
        data_limit = request.form.get('data_limit')
        price = float(request.form.get('price'))
        duration_days = int(request.form.get('duration_days'))
        description = request.form.get('description')
        
        new_package = Package(
            name=name,
            speed=speed,
            data_limit=data_limit,
            price=price,
            duration_days=duration_days,
            description=description
        )
        
        try:
            db.session.add(new_package)
            db.session.commit()
            flash('Package created successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred.', 'danger')
        
        return redirect(url_for('admin_packages'))
    
    packages = Package.query.order_by(Package.created_at.desc()).all() if hasattr(Package, 'created_at') else Package.query.all()
    return render_template('admin/packages.html', packages=packages)

@app.route('/admin/packages/delete/<int:id>')
@admin_required
def delete_package(id):
    package = Package.query.get_or_404(id)
    
    # Check if package has active subscriptions
    active_subs = Subscription.query.filter_by(package_id=id, status='active').count()
    if active_subs > 0:
        flash('Cannot delete package with active subscriptions.', 'danger')
        return redirect(url_for('admin_packages'))
    
    try:
        db.session.delete(package)
        db.session.commit()
        flash('Package deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'danger')
    
    return redirect(url_for('admin_packages'))

@app.route('/admin/invoices')
@admin_required
def admin_invoices():
    invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
    return render_template('admin/invoices.html', invoices=invoices)

# Initialize database and create default admin
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create default admin if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin_password = generate_password_hash('admin123')
            admin = User(
                username='admin',
                email='admin@wifibilling.com',
                password_hash=admin_password,
                role='admin'
            )
            db.session.add(admin)
            
            # Create sample packages
            packages = [
                Package(name='Basic', speed='5 Mbps', data_limit='50 GB', price=9.99, duration_days=30, description='Perfect for light browsing'),
                Package(name='Standard', speed='10 Mbps', data_limit='150 GB', price=19.99, duration_days=30, description='Great for streaming'),
                Package(name='Premium', speed='25 Mbps', data_limit='Unlimited', price=39.99, duration_days=30, description='Best for heavy usage'),
                Package(name='Family', speed='50 Mbps', data_limit='Unlimited', price=59.99, duration_days=30, description='Multiple devices')
            ]
            
            for package in packages:
                db.session.add(package)
            
            db.session.commit()
            print("Database initialized with default admin (username: admin, password: admin123)")

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=5000)
