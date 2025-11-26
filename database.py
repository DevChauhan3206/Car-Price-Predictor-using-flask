import sqlite3
from datetime import datetime
import hashlib

def init_database():
    """Initialize the SQLite database with all required tables"""
    conn = sqlite3.connect('car_predictor.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            phone VARCHAR(15),
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Cars table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand VARCHAR(50) NOT NULL,
            model VARCHAR(100) NOT NULL,
            year INTEGER NOT NULL,
            fuel_type VARCHAR(20) NOT NULL,
            transmission VARCHAR(20) NOT NULL,
            engine_capacity REAL NOT NULL,
            mileage REAL NOT NULL,
            base_price INTEGER NOT NULL,
            depreciation_rate REAL DEFAULT 0.15,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Predictions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            car_id INTEGER NOT NULL,
            car_age INTEGER NOT NULL,
            car_condition VARCHAR(20) NOT NULL,
            kilometers_driven INTEGER NOT NULL,
            city VARCHAR(50) NOT NULL,
            state VARCHAR(50),
            area_type VARCHAR(20),
            predicted_price INTEGER NOT NULL,
            prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            invoice_generated BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (car_id) REFERENCES cars (id)
        )
    ''')
    
    # Add new columns to existing predictions table if they don't exist
    try:
        cursor.execute('ALTER TABLE predictions ADD COLUMN state VARCHAR(50)')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE predictions ADD COLUMN area_type VARCHAR(20)')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Invoices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id INTEGER NOT NULL,
            invoice_number VARCHAR(20) UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            service_charge INTEGER DEFAULT 500,
            total_amount INTEGER NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prediction_id) REFERENCES predictions (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create default admin user
    admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password_hash, full_name, is_admin)
        VALUES (?, ?, ?, ?, ?)
    ''', ('admin', 'admin@carpredictor.com', admin_password, 'System Administrator', True))
    
    # Insert comprehensive car data with premium brands
    sample_cars = [
        # Maruti Suzuki
        ('Maruti Suzuki', 'Swift', 2023, 'Petrol', 'Manual', 1.2, 23.2, 650000, 0.12),
        ('Maruti Suzuki', 'Swift', 2022, 'Petrol', 'AMT', 1.2, 22.8, 620000, 0.12),
        ('Maruti Suzuki', 'Baleno', 2023, 'Petrol', 'Automatic', 1.2, 22.9, 750000, 0.12),
        ('Maruti Suzuki', 'Dzire', 2023, 'Petrol', 'Manual', 1.2, 24.1, 680000, 0.12),
        ('Maruti Suzuki', 'Vitara Brezza', 2023, 'Petrol', 'Automatic', 1.5, 18.7, 850000, 0.13),
        ('Maruti Suzuki', 'Ertiga', 2023, 'Petrol', 'Manual', 1.5, 19.3, 900000, 0.13),
        ('Maruti Suzuki', 'XL6', 2023, 'Petrol', 'Automatic', 1.5, 19.0, 1100000, 0.13),
        ('Maruti Suzuki', 'Wagon R', 2023, 'Petrol', 'Manual', 1.0, 25.2, 550000, 0.12),
        ('Maruti Suzuki', 'Alto K10', 2023, 'Petrol', 'Manual', 1.0, 24.9, 450000, 0.12),
        ('Maruti Suzuki', 'Celerio', 2023, 'Petrol', 'AMT', 1.0, 26.7, 520000, 0.12),
        
        # Hyundai
        ('Hyundai', 'i20', 2023, 'Petrol', 'Manual', 1.2, 20.4, 720000, 0.13),
        ('Hyundai', 'i20', 2022, 'Petrol', 'CVT', 1.0, 20.2, 690000, 0.13),
        ('Hyundai', 'Creta', 2023, 'Petrol', 'Automatic', 1.5, 17.4, 1200000, 0.14),
        ('Hyundai', 'Creta', 2023, 'Diesel', 'Manual', 1.5, 21.4, 1250000, 0.14),
        ('Hyundai', 'Venue', 2023, 'Petrol', 'Manual', 1.2, 18.2, 750000, 0.14),
        ('Hyundai', 'Verna', 2023, 'Petrol', 'CVT', 1.5, 18.4, 1100000, 0.14),
        ('Hyundai', 'Alcazar', 2023, 'Petrol', 'Automatic', 2.0, 14.2, 1650000, 0.15),
        ('Hyundai', 'Tucson', 2023, 'Petrol', 'Automatic', 2.0, 13.9, 2800000, 0.16),
        ('Hyundai', 'Elantra', 2022, 'Petrol', 'CVT', 2.0, 14.7, 2200000, 0.15),
        
        # Tata
        ('Tata', 'Nexon', 2023, 'Petrol', 'Manual', 1.2, 17.6, 850000, 0.13),
        ('Tata', 'Nexon', 2023, 'Electric', 'Automatic', 0.0, 312.0, 1600000, 0.10),
        ('Tata', 'Harrier', 2023, 'Diesel', 'Automatic', 2.0, 16.8, 1600000, 0.15),
        ('Tata', 'Safari', 2023, 'Diesel', 'Automatic', 2.0, 16.1, 1800000, 0.15),
        ('Tata', 'Punch', 2023, 'Petrol', 'Manual', 1.2, 18.8, 650000, 0.13),
        ('Tata', 'Altroz', 2023, 'Petrol', 'Manual', 1.2, 19.3, 700000, 0.13),
        ('Tata', 'Tigor', 2023, 'Petrol', 'AMT', 1.2, 20.0, 650000, 0.13),
        ('Tata', 'Tiago', 2023, 'Petrol', 'Manual', 1.2, 20.0, 550000, 0.13),
        
        # Mahindra
        ('Mahindra', 'XUV700', 2023, 'Petrol', 'Automatic', 2.0, 13.0, 1500000, 0.16),
        ('Mahindra', 'XUV700', 2023, 'Diesel', 'Manual', 2.2, 16.9, 1450000, 0.16),
        ('Mahindra', 'XUV300', 2023, 'Petrol', 'Manual', 1.2, 17.0, 900000, 0.16),
        ('Mahindra', 'Scorpio-N', 2023, 'Diesel', 'Manual', 2.2, 15.4, 1300000, 0.16),
        ('Mahindra', 'Scorpio Classic', 2023, 'Diesel', 'Manual', 2.2, 15.0, 1350000, 0.16),
        ('Mahindra', 'Thar', 2023, 'Petrol', 'Manual', 2.0, 15.2, 1400000, 0.15),
        ('Mahindra', 'Bolero', 2023, 'Diesel', 'Manual', 1.5, 17.0, 950000, 0.16),
        
        # Honda
        ('Honda', 'City', 2023, 'Petrol', 'CVT', 1.5, 17.8, 1200000, 0.14),
        ('Honda', 'City', 2023, 'Petrol', 'Manual', 1.5, 18.4, 1150000, 0.14),
        ('Honda', 'Amaze', 2023, 'Petrol', 'CVT', 1.2, 18.3, 750000, 0.14),
        ('Honda', 'Jazz', 2022, 'Petrol', 'CVT', 1.2, 17.1, 850000, 0.15),
        ('Honda', 'WR-V', 2022, 'Petrol', 'Manual', 1.2, 16.5, 900000, 0.15),
        ('Honda', 'Civic', 2022, 'Petrol', 'CVT', 1.8, 16.5, 2200000, 0.16),
        
        # Toyota
        ('Toyota', 'Innova Crysta', 2023, 'Diesel', 'Manual', 2.4, 15.6, 1900000, 0.12),
        ('Toyota', 'Innova Crysta', 2023, 'Petrol', 'Automatic', 2.7, 11.4, 1850000, 0.12),
        ('Toyota', 'Fortuner', 2023, 'Diesel', 'Automatic', 2.8, 14.2, 3500000, 0.13),
        ('Toyota', 'Urban Cruiser Hyryder', 2023, 'Petrol', 'Manual', 1.5, 20.6, 1100000, 0.13),
        ('Toyota', 'Glanza', 2023, 'Petrol', 'Manual', 1.2, 22.9, 680000, 0.13),
        ('Toyota', 'Camry', 2023, 'Petrol', 'Automatic', 2.5, 13.4, 4200000, 0.15),
        ('Toyota', 'Vellfire', 2023, 'Petrol', 'CVT', 2.5, 16.3, 9000000, 0.18),
        
        # Kia
        ('Kia', 'Seltos', 2023, 'Petrol', 'Automatic', 1.5, 16.8, 1100000, 0.15),
        ('Kia', 'Seltos', 2023, 'Diesel', 'Manual', 1.5, 20.8, 1150000, 0.15),
        ('Kia', 'Sonet', 2023, 'Petrol', 'Manual', 1.2, 18.4, 750000, 0.15),
        ('Kia', 'Carens', 2023, 'Petrol', 'Manual', 1.5, 16.2, 950000, 0.15),
        ('Kia', 'Carnival', 2023, 'Diesel', 'Automatic', 2.2, 14.1, 3500000, 0.16),
        
        # MG
        ('MG', 'Hector', 2023, 'Petrol', 'CVT', 1.5, 13.9, 1400000, 0.17),
        ('MG', 'Hector Plus', 2023, 'Petrol', 'Manual', 2.0, 13.4, 1600000, 0.17),
        ('MG', 'Astor', 2023, 'Petrol', 'CVT', 1.5, 15.7, 1100000, 0.17),
        ('MG', 'ZS EV', 2023, 'Electric', 'Automatic', 0.0, 419.0, 2500000, 0.12),
        ('MG', 'Gloster', 2023, 'Diesel', 'Automatic', 2.0, 13.9, 3200000, 0.18),
        
        # Skoda
        ('Skoda', 'Kushaq', 2023, 'Petrol', 'Automatic', 1.0, 18.1, 1200000, 0.16),
        ('Skoda', 'Kushaq', 2023, 'Petrol', 'Manual', 1.5, 16.2, 1150000, 0.16),
        ('Skoda', 'Slavia', 2023, 'Petrol', 'Automatic', 1.0, 18.7, 1200000, 0.16),
        ('Skoda', 'Kodiaq', 2022, 'Petrol', 'Automatic', 2.0, 13.1, 3700000, 0.18),
        ('Skoda', 'Superb', 2022, 'Petrol', 'Automatic', 2.0, 14.1, 3500000, 0.17),
        
        # Volkswagen
        ('Volkswagen', 'Taigun', 2023, 'Petrol', 'DSG', 1.0, 18.7, 1250000, 0.16),
        ('Volkswagen', 'Virtus', 2023, 'Petrol', 'Manual', 1.0, 19.4, 1200000, 0.16),
        ('Volkswagen', 'Tiguan', 2022, 'Petrol', 'Automatic', 2.0, 12.6, 3500000, 0.18),
        ('Volkswagen', 'T-Roc', 2022, 'Petrol', 'Automatic', 1.5, 16.3, 2200000, 0.18),
        
        # Nissan
        ('Nissan', 'Magnite', 2023, 'Petrol', 'CVT', 1.0, 20.0, 700000, 0.18),
        ('Nissan', 'Kicks', 2022, 'Petrol', 'CVT', 1.5, 14.2, 1000000, 0.18),
        ('Nissan', 'X-Trail', 2022, 'Petrol', 'CVT', 2.5, 13.2, 3500000, 0.19),
        
        # Renault
        ('Renault', 'Kiger', 2023, 'Petrol', 'AMT', 1.0, 20.5, 650000, 0.18),
        ('Renault', 'Triber', 2023, 'Petrol', 'Manual', 1.0, 20.0, 600000, 0.18),
        ('Renault', 'Duster', 2022, 'Petrol', 'CVT', 1.3, 16.4, 950000, 0.18),
        
        # BMW
        ('BMW', '3 Series', 2023, 'Petrol', 'Automatic', 2.0, 16.1, 4500000, 0.20),
        ('BMW', '5 Series', 2023, 'Petrol', 'Automatic', 2.0, 15.2, 6500000, 0.22),
        ('BMW', 'X1', 2023, 'Petrol', 'Automatic', 2.0, 14.8, 4200000, 0.20),
        ('BMW', 'X3', 2023, 'Petrol', 'Automatic', 2.0, 13.7, 6500000, 0.22),
        ('BMW', 'X5', 2023, 'Petrol', 'Automatic', 3.0, 12.1, 8500000, 0.24),
        ('BMW', 'X7', 2023, 'Petrol', 'Automatic', 3.0, 11.3, 12500000, 0.25),
        ('BMW', '7 Series', 2023, 'Petrol', 'Automatic', 3.0, 13.9, 15000000, 0.26),
        ('BMW', 'Z4', 2023, 'Petrol', 'Automatic', 2.0, 15.8, 7000000, 0.23),
        
        # Audi
        ('Audi', 'A3', 2023, 'Petrol', 'Automatic', 2.0, 16.3, 3800000, 0.20),
        ('Audi', 'A4', 2023, 'Petrol', 'Automatic', 2.0, 15.4, 4500000, 0.21),
        ('Audi', 'A6', 2023, 'Petrol', 'Automatic', 2.0, 14.2, 6200000, 0.22),
        ('Audi', 'A8', 2023, 'Petrol', 'Automatic', 3.0, 12.8, 13000000, 0.25),
        ('Audi', 'Q3', 2023, 'Petrol', 'Automatic', 2.0, 14.9, 4200000, 0.20),
        ('Audi', 'Q5', 2023, 'Petrol', 'Automatic', 2.0, 13.6, 6500000, 0.22),
        ('Audi', 'Q7', 2023, 'Petrol', 'Automatic', 3.0, 11.8, 8500000, 0.24),
        ('Audi', 'Q8', 2023, 'Petrol', 'Automatic', 3.0, 11.2, 10500000, 0.25),
        ('Audi', 'e-tron', 2023, 'Electric', 'Automatic', 0.0, 379.0, 10000000, 0.15),
        
        # Mercedes-Benz
        ('Mercedes-Benz', 'A-Class', 2023, 'Petrol', 'Automatic', 2.0, 15.8, 4000000, 0.20),
        ('Mercedes-Benz', 'C-Class', 2023, 'Petrol', 'Automatic', 2.0, 14.2, 5500000, 0.21),
        ('Mercedes-Benz', 'E-Class', 2023, 'Petrol', 'Automatic', 2.0, 13.1, 7500000, 0.22),
        ('Mercedes-Benz', 'S-Class', 2023, 'Petrol', 'Automatic', 3.0, 11.9, 16000000, 0.25),
        ('Mercedes-Benz', 'GLA', 2023, 'Petrol', 'Automatic', 2.0, 14.2, 4500000, 0.20),
        ('Mercedes-Benz', 'GLC', 2023, 'Petrol', 'Automatic', 2.0, 12.8, 6500000, 0.22),
        ('Mercedes-Benz', 'GLE', 2023, 'Petrol', 'Automatic', 3.0, 11.4, 8500000, 0.24),
        ('Mercedes-Benz', 'GLS', 2023, 'Petrol', 'Automatic', 3.0, 10.8, 12000000, 0.25),
        ('Mercedes-Benz', 'EQC', 2023, 'Electric', 'Automatic', 0.0, 414.0, 11000000, 0.18),
        
        # Jaguar
        ('Jaguar', 'XE', 2023, 'Petrol', 'Automatic', 2.0, 14.9, 4800000, 0.23),
        ('Jaguar', 'XF', 2023, 'Petrol', 'Automatic', 2.0, 13.8, 6000000, 0.24),
        ('Jaguar', 'F-Pace', 2023, 'Petrol', 'Automatic', 2.0, 12.9, 7000000, 0.24),
        ('Jaguar', 'E-Pace', 2023, 'Petrol', 'Automatic', 2.0, 13.4, 5500000, 0.23),
        ('Jaguar', 'I-Pace', 2023, 'Electric', 'Automatic', 0.0, 470.0, 11500000, 0.20),
        
        # Land Rover
        ('Land Rover', 'Discovery Sport', 2023, 'Petrol', 'Automatic', 2.0, 12.1, 6500000, 0.24),
        ('Land Rover', 'Range Rover Evoque', 2023, 'Petrol', 'Automatic', 2.0, 11.8, 7000000, 0.25),
        ('Land Rover', 'Range Rover Velar', 2023, 'Petrol', 'Automatic', 2.0, 11.2, 8500000, 0.25),
        ('Land Rover', 'Range Rover', 2023, 'Petrol', 'Automatic', 3.0, 10.4, 22000000, 0.27),
        
        # Volvo
        ('Volvo', 'XC40', 2023, 'Petrol', 'Automatic', 2.0, 14.1, 4500000, 0.22),
        ('Volvo', 'XC60', 2023, 'Petrol', 'Automatic', 2.0, 12.8, 6500000, 0.23),
        ('Volvo', 'XC90', 2023, 'Petrol', 'Automatic', 2.0, 11.9, 9500000, 0.24),
        ('Volvo', 'S60', 2023, 'Petrol', 'Automatic', 2.0, 15.1, 4800000, 0.22),
        
        # Lexus
        ('Lexus', 'ES', 2023, 'Petrol', 'Automatic', 2.5, 13.7, 6500000, 0.23),
        ('Lexus', 'NX', 2023, 'Petrol', 'Automatic', 2.5, 12.4, 6800000, 0.23),
        ('Lexus', 'LX', 2023, 'Petrol', 'Automatic', 3.5, 9.8, 25000000, 0.26),
        
        # Porsche
        ('Porsche', 'Macan', 2023, 'Petrol', 'Automatic', 2.0, 11.6, 8500000, 0.25),
        ('Porsche', 'Cayenne', 2023, 'Petrol', 'Automatic', 3.0, 10.2, 13500000, 0.26),
        ('Porsche', '911', 2023, 'Petrol', 'Automatic', 3.0, 12.1, 18000000, 0.27),
        ('Porsche', 'Panamera', 2023, 'Petrol', 'Automatic', 3.0, 11.8, 16000000, 0.26),
        
        # Maserati
        ('Maserati', 'Ghibli', 2023, 'Petrol', 'Automatic', 3.0, 10.9, 14000000, 0.27),
        ('Maserati', 'Levante', 2023, 'Petrol', 'Automatic', 3.0, 9.8, 16000000, 0.28),
        
        # Bentley
        ('Bentley', 'Continental GT', 2023, 'Petrol', 'Automatic', 4.0, 8.9, 35000000, 0.30),
        ('Bentley', 'Bentayga', 2023, 'Petrol', 'Automatic', 4.0, 8.2, 45000000, 0.32),
        
        # Rolls-Royce
        ('Rolls-Royce', 'Ghost', 2023, 'Petrol', 'Automatic', 6.6, 7.8, 55000000, 0.35),
        ('Rolls-Royce', 'Cullinan', 2023, 'Petrol', 'Automatic', 6.6, 7.2, 65000000, 0.35),
        
        # Ferrari
        ('Ferrari', 'Portofino', 2023, 'Petrol', 'Automatic', 3.9, 9.1, 35000000, 0.30),
        ('Ferrari', 'Roma', 2023, 'Petrol', 'Automatic', 3.9, 8.8, 38000000, 0.32),
        
        # Lamborghini
        ('Lamborghini', 'Huracan', 2023, 'Petrol', 'Automatic', 5.2, 7.2, 32000000, 0.35),
        ('Lamborghini', 'Urus', 2023, 'Petrol', 'Automatic', 4.0, 8.1, 42000000, 0.32),
        
        # McLaren
        ('McLaren', 'GT', 2023, 'Petrol', 'Automatic', 4.0, 8.9, 38000000, 0.35),
        
        # Jeep
        ('Jeep', 'Compass', 2023, 'Petrol', 'Automatic', 1.4, 14.1, 2000000, 0.18),
        ('Jeep', 'Meridian', 2023, 'Diesel', 'Automatic', 2.0, 16.9, 3500000, 0.19),
        ('Jeep', 'Wrangler', 2023, 'Petrol', 'Automatic', 2.0, 12.1, 6500000, 0.22),
        
        # Ford
        ('Ford', 'EcoSport', 2022, 'Petrol', 'Automatic', 1.5, 15.9, 950000, 0.17),
        ('Ford', 'Endeavour', 2022, 'Diesel', 'Automatic', 2.0, 12.4, 3600000, 0.18),
        ('Ford', 'Mustang', 2022, 'Petrol', 'Automatic', 5.0, 7.9, 7500000, 0.25),
        
        # Isuzu
        ('Isuzu', 'D-Max V-Cross', 2023, 'Diesel', 'Manual', 1.9, 16.2, 2200000, 0.18),
        ('Isuzu', 'MU-X', 2023, 'Diesel', 'Automatic', 1.9, 13.8, 3500000, 0.19),
        
        # Force Motors
        ('Force Motors', 'Gurkha', 2023, 'Diesel', 'Manual', 2.6, 14.2, 1600000, 0.17),
        
        # Citroen
        ('Citroen', 'C5 Aircross', 2023, 'Petrol', 'Automatic', 1.6, 16.1, 3600000, 0.19),
        ('Citroen', 'C3', 2023, 'Petrol', 'Manual', 1.2, 19.8, 650000, 0.16)
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO cars (brand, model, year, fuel_type, transmission, engine_capacity, mileage, base_price, depreciation_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_cars)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('car_predictor.db')
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == '__main__':
    init_database()
