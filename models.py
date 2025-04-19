from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# نموذج المستخدم
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='customer') # admin, agent, customer
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    properties = db.relationship('Property', backref='owner', lazy=True, foreign_keys='Property.owner_id')
    reviews = db.relationship('Review', backref='user', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)
    bookings = db.relationship('Booking', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

# نموذج المنطقة (المحافظة)
class Region(db.Model):
    __tablename__ = 'regions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # العلاقات
    cities = db.relationship('City', backref='region', lazy=True)
    
    def __repr__(self):
        return f'<Region {self.name}>'

# نموذج المدينة
class City(db.Model):
    __tablename__ = 'cities'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)
    
    # العلاقات
    districts = db.relationship('District', backref='city', lazy=True)
    
    def __repr__(self):
        return f'<City {self.name}>'

# نموذج الحي
class District(db.Model):
    __tablename__ = 'districts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    
    # العلاقات
    properties = db.relationship('Property', backref='district', lazy=True)
    
    def __repr__(self):
        return f'<District {self.name}>'

# نموذج نوع العقار
class PropertyType(db.Model):
    __tablename__ = 'property_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    
    # العلاقات
    properties = db.relationship('Property', backref='property_type', lazy=True)
    
    def __repr__(self):
        return f'<PropertyType {self.name}>'

# نموذج العقار


class Amenity(db.Model):
    __tablename__ = 'amenities'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    icon = db.Column(db.String(50))  # أيقونة FontAwesome مثلاً
    
    def __repr__(self):
        return f'<Amenity {self.name}>'

# علاقة many-to-many بين العقار والمميزات
property_amenity = db.Table('property_amenity',
    db.Column('property_id', db.Integer, db.ForeignKey('properties.id'), primary_key=True),
    db.Column('amenity_id', db.Integer, db.ForeignKey('amenities.id'), primary_key=True)
)

class Property(db.Model):
    __tablename__ = 'properties'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    area = db.Column(db.Float, nullable=False)
    bedrooms = db.Column(db.Integer, default=0)
    bathrooms = db.Column(db.Integer, default=0)
    floors = db.Column(db.Integer, default=1)
    year_built = db.Column(db.Integer)
    address = db.Column(db.String(200), nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    property_type_id = db.Column(db.Integer, db.ForeignKey('property_types.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # sale, rent
    is_featured = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='available')  # available, sold, rented
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    district = db.relationship('District', backref='properties')
    property_type = db.relationship('PropertyType', backref='properties')
    owner = db.relationship('User', backref='properties')
    images = db.relationship('PropertyImage', backref='property', cascade='all, delete-orphan')
    amenities = db.relationship('Amenity', secondary=property_amenity, backref='properties')
    
    def __repr__(self):
        return f'<Property {self.title}>'
# نموذج صور العقار
class PropertyImage(db.Model):
    __tablename__ = 'property_images'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    is_main = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<PropertyImage {self.id} for Property {self.property_id}>'

# نموذج مميزات العقار
class Amenity(db.Model):
    __tablename__ = 'amenities'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(50))
    
    properties = db.relationship('PropertyAmenity', backref='amenity', lazy=True)
    
    def __repr__(self):
        return f'<Amenity {self.name}>'

# جدول العلاقة بين العقارات والمميزات
class PropertyAmenity(db.Model):
    __tablename__ = 'property_amenities'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    amenity_id = db.Column(db.Integer, db.ForeignKey('amenities.id'), nullable=False)
    
    def __repr__(self):
        return f'<PropertyAmenity {self.property_id}-{self.amenity_id}>'

# نموذج تقييمات العقار
class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Review {self.id} by User {self.user_id} for Property {self.property_id}>'

# نموذج العقارات المفضلة
class Favorite(db.Model):
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Favorite {self.id} by User {self.user_id} for Property {self.property_id}>'

# نموذج حجز موعد معاينة العقار
class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Booking {self.id} by User {self.user_id} for Property {self.property_id}>'

# نموذج المعاملات
class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # sale, rent
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    property = db.relationship('Property', backref=db.backref('transactions', lazy=True))
    buyer = db.relationship('User', foreign_keys=[buyer_id], backref='purchases')
    seller = db.relationship('User', foreign_keys=[seller_id], backref='sales')
    
    def __repr__(self):
        return f'<Transaction {self.id} for Property {self.property_id}>'