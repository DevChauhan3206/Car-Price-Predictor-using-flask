# Car Price Predictor

A comprehensive web application for predicting car prices in the Indian market. Built with Python Flask, featuring user authentication, admin panel, invoice generation, and modern responsive UI.

## Features

### User Features
- **User Registration & Authentication**: Secure user accounts with login/logout functionality
- **Car Price Prediction**: Accurate price predictions based on multiple factors
- **Price Breakdown**: Detailed analysis showing how the price is calculated
- **Invoice Generation**: Professional PDF invoices for predictions
- **User Dashboard**: Track prediction history and manage account
- **Responsive Design**: Modern UI with animations and transitions

### Admin Features
- **Admin Dashboard**: Comprehensive overview with statistics
- **Car Management**: Add, view, and manage car models in database
- **User Management**: View registered users and their activity
- **Analytics**: Track platform usage and predictions

### Technical Features
- **No Machine Learning**: Rule-based prediction algorithm
- **SQLite Database**: Lightweight database for data storage
- **PDF Generation**: Professional invoices using ReportLab
- **Indian Market Focus**: Prices in INR with local market considerations
- **Modern UI**: CSS animations, transitions, and responsive design

## Installation

1. **Clone or download the project**
   ```bash
   cd C:\Users\admin\CascadeProjects\car-price-predictor
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   ```bash
   python database.py
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Open your browser and go to `http://localhost:5000`

## Default Admin Account

- **Username**: admin
- **Password**: admin123

## Project Structure

```
car-price-predictor/
├── app.py                 # Main Flask application
├── database.py           # Database initialization and connection
├── price_predictor.py    # Price prediction logic
├── invoice_generator.py  # PDF invoice generation
├── requirements.txt      # Python dependencies
├── README.md            # Project documentation
├── static/
│   ├── css/
│   │   └── style.css    # Modern CSS with animations
│   ├── js/
│   │   └── main.js      # JavaScript for interactions
│   └── images/          # Static images
└── templates/           # HTML templates
    ├── base.html        # Base template
    ├── index.html       # Homepage
    ├── login.html       # Login page
    ├── register.html    # Registration page
    ├── user_dashboard.html
    ├── predict.html     # Price prediction form
    ├── prediction_result.html
    ├── invoice.html     # Invoice display
    ├── admin_dashboard.html
    ├── admin_cars.html  # Car management
    ├── admin_add_car.html
    └── admin_users.html # User management
```

## How Price Prediction Works

The application uses a rule-based algorithm that considers:

1. **Base Price**: Current market price of the car model
2. **Depreciation**: Age-based depreciation with brand-specific rates
3. **Condition**: Adjustments based on car condition (Excellent/Good/Fair/Poor)
4. **Mileage**: Comparison with expected kilometers driven
5. **Location**: City-specific market demand multipliers
6. **Specifications**: Fuel type and transmission adjustments

## Database Schema

### Users Table
- User authentication and profile information
- Admin flag for administrative access

### Cars Table
- Car specifications and pricing information
- Brand, model, year, fuel type, transmission
- Base price and depreciation rates

### Predictions Table
- User prediction history
- Car details and predicted prices
- Timestamp and location information

### Invoices Table
- Generated invoices for predictions
- Service charges and billing information

## Supported Car Brands

The database comes pre-loaded with popular Indian car models:
- Maruti Suzuki
- Hyundai
- Tata
- Mahindra
- Honda
- Toyota
- Kia
- MG
- Skoda
- Volkswagen
- Nissan
- Renault

## City Coverage

Price adjustments for major Indian cities:
- Mumbai, Delhi, Bangalore, Chennai
- Hyderabad, Pune, Kolkata, Ahmedabad
- Jaipur, Lucknow, Kanpur, Nagpur
- Indore, Bhopal, Visakhapatnam
- Other cities (with standard rates)

## Technologies Used

- **Backend**: Python Flask
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3, JavaScript
- **Authentication**: Flask-Login
- **PDF Generation**: ReportLab
- **UI Framework**: Custom CSS with animations
- **Icons**: Font Awesome
- **Fonts**: Google Fonts (Poppins)

## Security Features

- Password hashing with SHA-256
- Session management with Flask-Login
- CSRF protection
- Input validation and sanitization
- Secure database queries

## Future Enhancements

- Advanced analytics dashboard
- Email notifications
- SMS integration
- Car image uploads
- Comparison features
- Market trend analysis
- API endpoints
- Mobile app integration

## Support

For any issues or questions, please contact:
- Email: support@carpredictor.com

## License

This project is for educational and demonstration purposes.
