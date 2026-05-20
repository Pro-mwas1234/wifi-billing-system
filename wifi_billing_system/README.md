# WiFi Billing System

A complete WiFi billing and subscription management system built with Python (Flask) backend and HTML/CSS/JavaScript frontend.

## Features

### Customer Features
- User registration and authentication
- View available WiFi packages
- Subscribe to packages
- Track active subscription status
- View invoice history
- Dashboard with subscription details

### Admin Features
- Admin dashboard with statistics
- Manage users (view customer accounts)
- Create and manage WiFi packages
- View all invoices and revenue
- Track active subscriptions
- Revenue analytics

## Tech Stack

- **Backend**: Python 3, Flask
- **Database**: SQLite (via Flask-SQLAlchemy)
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Icons**: Font Awesome

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. **Navigate to the project directory:**
   ```bash
   cd wifi_billing_system
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Access the application:**
   Open your browser and navigate to: `http://localhost:5000`

## Default Credentials

- **Admin Login:**
  - Username: `admin`
  - Password: `admin123`

## Project Structure

```
wifi_billing_system/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── home.html         # Landing page
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── dashboard.html    # Customer dashboard
│   ├── invoices.html     # Customer invoices
│   └── admin/            # Admin templates
│       ├── dashboard.html
│       ├── users.html
│       ├── packages.html
│       └── invoices.html
└── static/               # Static files (CSS, JS, images)
    ├── css/
    └── js/
```

## Database

The application uses SQLite database which will be automatically created on first run (`wifi_billing.db`).

### Database Models:
- **User**: Customer and admin accounts
- **Package**: WiFi subscription packages
- **Subscription**: User subscriptions to packages
- **Invoice**: Billing records

## Usage Guide

### For Customers:
1. Register a new account
2. Login with your credentials
3. Browse available packages
4. Subscribe to a package
5. View your subscription status and invoices

### For Administrators:
1. Login with admin credentials
2. Access admin dashboard
3. Create new WiFi packages
4. Manage users and view subscriptions
5. Monitor revenue and invoices

## Customization

### Change Secret Key
Edit the `SECRET_KEY` in `app.py`:
```python
app.config['SECRET_KEY'] = 'your-secure-secret-key'
```

### Database Configuration
To use a different database, modify the `SQLALCHEMY_DATABASE_URI` in `app.py`.

## Security Notes

- Change the default admin password after first login
- Use a strong secret key in production
- Enable HTTPS in production
- Consider adding email verification for new users
- Implement proper payment gateway integration for production use

## License

This project is open-source and available for educational and commercial use.

## Support

For issues and questions, please check the code documentation or create an issue in the repository.
