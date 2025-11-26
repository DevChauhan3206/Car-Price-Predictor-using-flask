import random
from database import get_db_connection

class CarPricePredictor:
    def __init__(self):
        # State-based multipliers for market demand
        self.state_multipliers = {
            'maharashtra': 1.15,
            'delhi': 1.12,
            'karnataka': 1.10,
            'tamil-nadu': 1.08,
            'telangana': 1.06,
            'gujarat': 1.05,
            'west-bengal': 1.03,
            'haryana': 1.08,
            'uttar-pradesh': 0.96,
            'rajasthan': 0.98,
            'punjab': 1.02,
            'madhya-pradesh': 0.97,
            'bihar': 0.90,
            'odisha': 0.92,
            'kerala': 1.04,
            'andhra-pradesh': 0.95,
            'jharkhand': 0.91,
            'assam': 0.88,
            'chhattisgarh': 0.89,
            'himachal-pradesh': 0.94,
            'uttarakhand': 0.93,
            'goa': 1.07,
            'jammu-kashmir': 0.87,
            'ladakh': 0.85,
            'arunachal-pradesh': 0.86,
            'manipur': 0.87,
            'meghalaya': 0.86,
            'mizoram': 0.85,
            'nagaland': 0.86,
            'sikkim': 0.88,
            'tripura': 0.87
        }
        
        # Area type multipliers
        self.area_type_multipliers = {
            'metro': 1.10,
            'urban': 1.00,
            'suburban': 0.95,
            'rural': 0.85
        }
        
        # City-specific adjustments within states
        self.city_adjustments = {
            'mumbai': 1.05,
            'pune': 1.02,
            'new-delhi': 1.03,
            'bangalore': 1.04,
            'chennai': 1.02,
            'hyderabad': 1.01,
            'kolkata': 1.01,
            'ahmedabad': 1.02,
            'surat': 1.01,
            'jaipur': 1.01,
            'lucknow': 1.00,
            'kanpur': 0.98,
            'nagpur': 0.99,
            'indore': 1.00,
            'bhopal': 0.99,
            'visakhapatnam': 0.99,
            'kochi': 1.02,
            'thiruvananthapuram': 1.01,
            'coimbatore': 1.01,
            'gurgaon': 1.03,
            'faridabad': 1.02
        }
        
        self.condition_multipliers = {
            'excellent': 1.0,
            'good': 0.85,
            'fair': 0.70,
            'poor': 0.55
        }
        
        self.fuel_type_adjustments = {
            'petrol': 1.0,
            'diesel': 1.08,
            'cng': 0.95,
            'electric': 1.20,
            'hybrid': 1.15
        }
        
        self.transmission_adjustments = {
            'manual': 1.0,
            'automatic': 1.12,
            'cvt': 1.08,
            'dsg': 1.15,
            'amt': 1.05
        }

    def get_car_details(self, car_id):
        """Get car details from database"""
        conn = get_db_connection()
        car_row = conn.execute('SELECT * FROM cars WHERE id = ?', (car_id,)).fetchone()
        conn.close()
        return dict(car_row) if car_row else None

    def calculate_depreciation(self, base_price, car_age, depreciation_rate):
        """Calculate depreciation based on car age - more realistic rates"""
        # More realistic depreciation rates
        if car_age == 0:
            return base_price
        elif car_age == 1:
            return base_price * 0.85  # 15% first year depreciation
        elif car_age <= 3:
            return base_price * 0.85 * ((1 - 0.08) ** (car_age - 1))  # 8% per year for years 2-3
        elif car_age <= 5:
            return base_price * 0.85 * (0.92 ** 2) * ((1 - 0.06) ** (car_age - 3))  # 6% per year for years 4-5
        else:
            # 4% per year after 5 years
            return base_price * 0.85 * (0.92 ** 2) * (0.94 ** 2) * ((1 - 0.04) ** (car_age - 5))

    def calculate_mileage_adjustment(self, kilometers_driven, car_age):
        """Adjust price based on kilometers driven"""
        if car_age == 0:
            expected_km = 0
        else:
            expected_km = car_age * 15000  # Average 15,000 km per year
        
        actual_km = kilometers_driven
        
        if actual_km <= expected_km:
            # Low mileage bonus
            return 1.0 + (expected_km - actual_km) / 100000 * 0.05
        else:
            # High mileage penalty
            excess_km = actual_km - expected_km
            penalty = min(excess_km / 50000 * 0.1, 0.3)  # Max 30% penalty
            return 1.0 - penalty

    def predict_price(self, car_id, car_age, condition, kilometers_driven, state, city):
        """Main price prediction function with state-city support"""
        car = self.get_car_details(car_id)
        if not car:
            return None
        
        # Start with base price
        base_price = car['base_price']
        
        # Apply depreciation
        depreciated_price = self.calculate_depreciation(
            base_price, car_age, car['depreciation_rate']
        )
        
        # Apply condition multiplier
        condition_adjusted = depreciated_price * self.condition_multipliers.get(
            condition.lower(), 0.7
        )
        
        # Apply mileage adjustment
        mileage_adjusted = condition_adjusted * self.calculate_mileage_adjustment(
            kilometers_driven, car_age
        )
        
        # Apply state multiplier
        state_multiplier = self.state_multipliers.get(state.lower(), 0.92)
        state_adjusted = mileage_adjusted * state_multiplier
        
        # Apply city adjustment within state
        city_adjustment = self.city_adjustments.get(city.lower(), 1.0)
        city_adjusted = state_adjusted * city_adjustment
        
        # Apply fuel type adjustment
        fuel_adjusted = city_adjusted * self.fuel_type_adjustments.get(
            car['fuel_type'].lower(), 1.0
        )
        
        # Apply transmission adjustment
        final_price = fuel_adjusted * self.transmission_adjustments.get(
            car['transmission'].lower(), 1.0
        )
        
        # Add market price percentage and fluctuation
        # Market demand factor based on current trends (±10%)
        market_factor = random.uniform(0.90, 1.10)
        
        # Add market price percentage calculation
        market_price_percentage = 0.85 + (0.30 * (1 - (car_age / 25)))  # 85-115% of calculated price based on age
        
        final_price = final_price * market_factor * market_price_percentage
        
        # Round to nearest thousand
        final_price = round(final_price / 1000) * 1000
        
        return max(int(final_price), 50000)  # Minimum price of ₹50,000

    def get_price_breakdown(self, car_id, car_age, condition, kilometers_driven, state, city):
        """Get detailed price breakdown for transparency"""
        car = self.get_car_details(car_id)
        if not car:
            return None
        
        breakdown = {
            'base_price': car['base_price'],
            'car_details': {
                'brand': car['brand'],
                'model': car['model'],
                'year': car['year'],
                'fuel_type': car['fuel_type'],
                'transmission': car['transmission']
            }
        }
        
        # Calculate step by step
        current_price = car['base_price']
        
        # Depreciation
        if car_age > 0:
            depreciated_price = self.calculate_depreciation(
                current_price, car_age, car['depreciation_rate']
            )
            breakdown['depreciation'] = {
                'amount': current_price - depreciated_price,
                'percentage': car['depreciation_rate'] * 100,
                'price_after': depreciated_price
            }
            current_price = depreciated_price
        
        # Condition
        condition_multiplier = self.condition_multipliers.get(condition.lower(), 0.7)
        condition_adjusted = current_price * condition_multiplier
        breakdown['condition'] = {
            'multiplier': condition_multiplier,
            'adjustment': condition_adjusted - current_price,
            'price_after': condition_adjusted
        }
        current_price = condition_adjusted
        
        # Mileage
        mileage_multiplier = self.calculate_mileage_adjustment(kilometers_driven, car_age)
        mileage_adjusted = current_price * mileage_multiplier
        breakdown['mileage'] = {
            'multiplier': mileage_multiplier,
            'adjustment': mileage_adjusted - current_price,
            'price_after': mileage_adjusted
        }
        current_price = mileage_adjusted
        
        # State
        state_multiplier = self.state_multipliers.get(state.lower(), 0.92)
        state_adjusted = current_price * state_multiplier
        breakdown['state'] = {
            'multiplier': state_multiplier,
            'adjustment': state_adjusted - current_price,
            'price_after': state_adjusted
        }
        current_price = state_adjusted
        
        # City
        city_adjustment = self.city_adjustments.get(city.lower(), 1.0)
        city_adjusted = current_price * city_adjustment
        breakdown['city'] = {
            'multiplier': city_adjustment,
            'adjustment': city_adjusted - current_price,
            'price_after': city_adjusted
        }
        
        breakdown['final_price'] = self.predict_price(car_id, car_age, condition, kilometers_driven, state, city)
        
        return breakdown
