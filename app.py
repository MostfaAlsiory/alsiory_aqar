import os
import io
import zipfile
import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import uuid

# إنشاء قاعدة البيانات
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# إنشاء تطبيق فلاسك
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SESSION_SECRET") or "sayouriaqar-secret-key-12345"

# إعداد Cloudinary
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', 'due2rm5cb'),
    api_key=os.environ.get('CLOUDINARY_API_KEY', '494883843628169'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET', 'TnEHyxax7uSePlBh4EwS8QjJdBs')
)

# إضافة فلتر لتحويل أسطر النص الجديدة إلى وسوم HTML
@app.template_filter('nl2br')
def nl2br_filter(s):
    if s is None:
        return ""
    return s.replace('\n', '<br>')






# إعداد قاعدة البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# إعداد نظام تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'
login_manager.login_message_category = 'info'


# نماذج قاعدة البيانات
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='customer')  # admin, agent, customer
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    properties = db.relationship('Property', backref='owner', lazy=True, foreign_keys='Property.owner_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Region(db.Model):
    __tablename__ = 'regions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # العلاقات
    cities = db.relationship('City', backref='region', lazy=True)
    
    def __repr__(self):
        return f'<Region {self.name}>'

class City(db.Model):
    __tablename__ = 'cities'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)
    
    # العلاقات
    districts = db.relationship('District', backref='city', lazy=True)
    
    def __repr__(self):
        return f'<City {self.name}>'

class District(db.Model):
    __tablename__ = 'districts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    
    # العلاقات
    properties = db.relationship('Property', backref='district', lazy=True)
    
    def __repr__(self):
        return f'<District {self.name}>'

class PropertyType(db.Model):
    __tablename__ = 'property_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    
    # العلاقات
    properties = db.relationship('Property', backref='property_type', lazy=True)
    
    def __repr__(self):
        return f'<PropertyType {self.name}>'

class Property(db.Model):
    __tablename__ = 'properties'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    area = db.Column(db.Float, nullable=False)  # المساحة بالمتر المربع
    bedrooms = db.Column(db.Integer, default=0)
    bathrooms = db.Column(db.Integer, default=0)
    
    # الموقع
    address = db.Column(db.String(200), nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    
    # التصنيفات
    property_type_id = db.Column(db.Integer, db.ForeignKey('property_types.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # sale, rent
    
    # معلومات أخرى
    is_featured = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='available')  # available, sold, rented
    
    # الملكية والتوقيت
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Property {self.title}>'

class PropertyImage(db.Model):
    __tablename__ = 'property_images'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    cloudinary_public_id = db.Column(db.String(255), nullable=True)  # معرف الصورة في Cloudinary
    is_main = db.Column(db.Boolean, default=False)
    
    # العلاقات
    property_rel = db.relationship('Property', backref='images')
    
    def get_image_url(self):
        """إرجاع رابط الصورة (محلي أو من Cloudinary)"""
        if self.cloudinary_public_id:
            return cloudinary.CloudinaryImage(self.cloudinary_public_id).build_url()
        else:
            from flask import url_for
            return url_for('static', filename=self.image_path)
    
    def __repr__(self):
        return f'<PropertyImage {self.id}>'


    def get_id(self):
        return str(self.id)
    
    @property
    def is_active(self):
        return self.is_active
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    property = db.relationship('Property', backref='bookings')
    user = db.relationship('User', backref='bookings')
    
    def __repr__(self):
        return f'<Booking {self.id}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# وظائف مساعدة
def upload_image_to_cloudinary(file):
    """رفع صورة إلى Cloudinary وإرجاع معرف الصورة"""
    if not file:
        return None
    
    try:
        # توليد اسم فريد للصورة
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # رفع الصورة إلى Cloudinary
        result = cloudinary.uploader.upload(
            file,
            public_id=f"sayouriaqar/{unique_filename}",
            overwrite=True,
            resource_type="image"
        )
        
        # إرجاع معرف الصورة في Cloudinary
        return result['public_id']
    
    except Exception as e:
        print(f"خطأ في رفع الصورة إلى Cloudinary: {str(e)}")
        return None

# طرق التطبيق Routes
@app.route('/')
def index():
    """الصفحة الرئيسية"""
    latest_properties = Property.query.order_by(Property.created_at.desc()).limit(8).all()
    featured_properties = Property.query.filter_by(is_featured=True).order_by(Property.created_at.desc()).limit(6).all()
    property_count = Property.query.count()
    regions = Region.query.all()
    property_types = PropertyType.query.all()
    
    # إضافة متغير التاريخ للاستخدام في تذييل الصفحة
    current_date = datetime.now()
    
    return render_template('index.html', 
                          latest_properties=latest_properties,
                          featured_properties=featured_properties,
                          property_count=property_count,
                          regions=regions,
                          property_types=property_types,
                          date=current_date)

@app.route('/properties')
def properties():
    """صفحة عرض العقارات"""
    # تطبيق مرشحات البحث
    query = Property.query.filter_by(status='available')
    
    region_id = request.args.get('region_id', type=int)
    if region_id and region_id > 0:
        districts = District.query.join(City).filter(City.region_id == region_id).all()
        district_ids = [d.id for d in districts]
        query = query.filter(Property.district_id.in_(district_ids))
    
    property_type_id = request.args.get('property_type_id', type=int)
    if property_type_id and property_type_id > 0:
        query = query.filter_by(property_type_id=property_type_id)
    
    transaction_type = request.args.get('transaction_type')
    if transaction_type:
        query = query.filter_by(transaction_type=transaction_type)
    
    min_price = request.args.get('min_price', type=float)
    if min_price:
        query = query.filter(Property.price >= min_price)
    
    max_price = request.args.get('max_price', type=float)
    if max_price:
        query = query.filter(Property.price <= max_price)
    
    bedrooms = request.args.get('bedrooms', type=int)
    if bedrooms and bedrooms > 0:
        query = query.filter(Property.bedrooms >= bedrooms)
    
    bathrooms = request.args.get('bathrooms', type=int)
    if bathrooms and bathrooms > 0:
        query = query.filter(Property.bathrooms >= bathrooms)
    
    min_area = request.args.get('min_area', type=float)
    if min_area:
        query = query.filter(Property.area >= min_area)
    
    keyword = request.args.get('keyword')
    if keyword:
        query = query.filter(Property.title.ilike(f'%{keyword}%') | 
                             Property.description.ilike(f'%{keyword}%') |
                             Property.address.ilike(f'%{keyword}%'))
    
    # التصنيف والصفحات
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    if sort_by == 'price':
        if sort_order == 'asc':
            query = query.order_by(Property.price.asc())
        else:
            query = query.order_by(Property.price.desc())
    elif sort_by == 'created_at':
        if sort_order == 'asc':
            query = query.order_by(Property.created_at.asc())
        else:
            query = query.order_by(Property.created_at.desc())
    elif sort_by == 'area':
        if sort_order == 'asc':
            query = query.order_by(Property.area.asc())
        else:
            query = query.order_by(Property.area.desc())
    
    # الصفحات
    page = request.args.get('page', 1, type=int)
    per_page = 9  # عدد العقارات في كل صفحة
    properties = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # الحصول على المناطق وأنواع العقارات للفلتر
    regions = Region.query.all()
    property_types = PropertyType.query.all()
    
    # إضافة متغير التاريخ للاستخدام في تذييل الصفحة
    current_date = datetime.now()
    
    return render_template('properties.html', 
                          properties=properties,
                          regions=regions,
                          property_types=property_types,
                          sort_by=sort_by,
                          sort_order=sort_order,
                          date=current_date)

@app.route('/property/<int:property_id>')
def property_detail(property_id):
    """صفحة تفاصيل العقار"""
    property = Property.query.get_or_404(property_id)
    
    # البحث عن عقارات مشابهة (نفس نوع العقار ونوع المعاملة)
    similar_properties = Property.query.filter(
        Property.id != property_id,
        Property.property_type_id == property.property_type_id,
        Property.transaction_type == property.transaction_type,
        Property.status == 'available'
    ).limit(3).all()
    
    # إضافة متغير التاريخ للاستخدام في تذييل الصفحة
    current_date = datetime.now()
    
    return render_template('property_detail.html',
                          property=property,
                          similar_properties=similar_properties,
                          date=current_date)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """صفحة تسجيل حساب جديد"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        # التحقق من عدم وجود المستخدم بالفعل
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('البريد الإلكتروني مستخدم بالفعل!', 'danger')
            return redirect(url_for('register'))
        
        # إنشاء مستخدم جديد
        new_user = User(username=username, email=email, phone=phone)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.', 'success')
        return redirect(url_for('login'))
    
    # إضافة متغير التاريخ للاستخدام في تذييل الصفحة
    current_date = datetime.now()
    
    return render_template('register.html', date=current_date)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """صفحة تسجيل الدخول"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        # التحقق من وجود المستخدم
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('البريد الإلكتروني غير مسجل!', 'danger')
            return redirect(url_for('login'))
        
        # التحقق من كلمة المرور
        if not user.check_password(password):
            flash('كلمة المرور غير صحيحة!', 'danger')
            return redirect(url_for('login'))
        
        # التحقق من حالة الحساب
        if not user.is_active:
            flash('حسابك معطل، يرجى التواصل مع المسؤول', 'danger')
            return redirect(url_for('login'))
        
        # تسجيل الدخول
        login_user(user, remember=remember)
        next_page = request.args.get('next')
        flash(f'مرحباً بعودتك، {user.username}!', 'success')
        return redirect(next_page or url_for('index'))
    
    return render_template('login.html', date=datetime.now())


@app.route('/logout')
@login_required
def logout():
    """تسجيل الخروج"""
    logout_user()
    flash('تم تسجيل الخروج بنجاح.', 'info')
    return redirect(url_for('index'))

@app.route('/property/<int:property_id>/book', methods=['POST'])
@login_required
def book_property(property_id):
    """حجز موعد لمعاينة العقار"""
    property = Property.query.get_or_404(property_id)
    
    if request.method == 'POST':
        booking_date_str = request.form.get('booking_date')
        notes = request.form.get('notes', '')
        
        try:
            booking_date = datetime.fromisoformat(booking_date_str)
            
            # التحقق من أن تاريخ الحجز ليس في الماضي
            if booking_date < datetime.now():
                flash('يجب أن يكون تاريخ الحجز في المستقبل', 'danger')
                return redirect(url_for('property_detail', property_id=property_id))
            
            # إنشاء حجز جديد
            booking = Booking(
                property_id=property_id,
                user_id=current_user.id,
                booking_date=booking_date,
                notes=notes,
                status='pending'
            )
            
            db.session.add(booking)
            db.session.commit()
            
            flash('تم حجز موعد المعاينة بنجاح. سيتم التواصل معك قريباً.', 'success')
        except Exception as e:
            flash(f'حدث خطأ أثناء محاولة الحجز: {str(e)}', 'danger')
        
    return redirect(url_for('property_detail', property_id=property_id))

@app.route('/profile')
@login_required
def profile():
    """صفحة الملف الشخصي للمستخدم"""
    user_properties = Property.query.filter_by(owner_id=current_user.id).all()
    user_bookings = Booking.query.filter_by(user_id=current_user.id).all()
    
    # إضافة متغير التاريخ للاستخدام في تذييل الصفحة
    current_date = datetime.now()
    
    return render_template('profile.html', 
                          user=current_user, 
                          properties=user_properties,
                          bookings=user_bookings,
                          date=current_date)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """لوحة التحكم الإدارية"""
    # تحقق من صلاحيات المستخدم
    if current_user.role != 'admin':
        flash('ليس لديك صلاحية الوصول إلى لوحة التحكم.', 'danger')
        return redirect(url_for('index'))
    
    # إحصائيات عامة
    total_properties = Property.query.count()
    active_properties = Property.query.filter_by(status='available').count()
    total_users = User.query.count()
    pending_bookings = Booking.query.filter_by(status='pending').count()
    
    # أحدث المستخدمين
    latest_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # أحدث العقارات
    latest_properties = Property.query.order_by(Property.created_at.desc()).limit(5).all()
    
    # أحدث الحجوزات
    latest_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    
    # إضافة متغير التاريخ للاستخدام في تذييل الصفحة
    current_date = datetime.now()
    
    return render_template('admin/dashboard.html',
                           total_properties=total_properties,
                           active_properties=active_properties,
                           total_users=total_users,
                           pending_bookings=pending_bookings,
                           latest_users=latest_users,
                           latest_properties=latest_properties,
                           latest_bookings=latest_bookings,
                           date=current_date)















# ==============================================
# قسم إدارة العقارات (للمدير فقط)
# ==============================================

@app.route('/admin/properties')
@login_required
def admin_properties():
    """عرض جميع العقارات مع أدوات التحكم للمدير"""
    if current_user.role != 'admin':
        abort(403)
    
    # فلترة العقارات
    status_filter = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    
    query = Property.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    properties_pagination = query.order_by(Property.created_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('admin/properties.html',
                         properties=properties_pagination.items,
                         pagination=properties_pagination,
                         status_filter=status_filter,
                         date=datetime.now()
                         )

# ... (الاستيرادات والإعدادات السابقة)

@app.route('/admin/properties/add', methods=['GET', 'POST'])
@login_required
def add_property():
    """إضافة عقار جديد مع كل الحقول المطلوبة"""
    if current_user.role != 'admin':
        abort(403)
    
    form = PropertyForm()
    
    # تعبئة خيارات القوائم المنسدلة
    form.region_id.choices = [(r.id, r.name) for r in Region.query.order_by(Region.name).all()]
    form.city_id.choices = [(c.id, c.name) for c in City.query.order_by(City.name).all()]
    form.district_id.choices = [(d.id, d.name) for d in District.query.order_by(District.name).all()]
    form.property_type_id.choices = [(pt.id, pt.name) for pt in PropertyType.query.order_by(PropertyType.name).all()]
    form.amenities.choices = [(a.id, a.name) for a in Amenity.query.order_by(Amenity.name).all()]
    
    if form.validate_on_submit():
        try:
            # إنشاء العقار
            new_property = Property(
                title=form.title.data,
                description=form.description.data,
                price=form.price.data,
                area=form.area.data,
                bedrooms=form.bedrooms.data or 0,
                bathrooms=form.bathrooms.data or 0,
                floors=form.floors.data or 1,
                year_built=form.year_built.data,
                address=form.address.data,
                district_id=form.district_id.data,
                latitude=form.latitude.data,
                longitude=form.longitude.data,
                property_type_id=form.property_type_id.data,
                transaction_type=form.transaction_type.data,
                owner_id=current_user.id,
                status='available'
            )
            
            db.session.add(new_property)
            db.session.flush()  # للحصول على ID العقار قبل الـ commit
            
            # إضافة المميزات
            for amenity_id in form.amenities.data:
                amenity = Amenity.query.get(amenity_id)
                if amenity:
                    new_property.amenities.append(amenity)
            
            # معالجة الصور
            for image in form.images.data:
                if image.filename != '':
                    public_id = upload_image_to_cloudinary(image)
                    if public_id:
                        new_image = PropertyImage(
                            property_id=new_property.id,
                            cloudinary_public_id=public_id,
                            is_main=False
                        )
                        db.session.add(new_image)
            
            db.session.commit()
            flash('تم إضافة العقار بنجاح', 'success')
            return redirect(url_for('admin_properties'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة العقار: {str(e)}', 'danger')
    
    return render_template('admin/add_property.html', form=form)

@app.route('/admin/properties/<int:property_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_property(property_id):
    """تعديل عقار موجود"""
    if current_user.role != 'admin':
        abort(403)
    
    property = Property.query.get_or_404(property_id)
    form = PropertyForm(obj=property)
    
    # تعبئة خيارات القوائم المنسدلة
    form.region_id.choices = [(r.id, r.name) for r in Region.query.order_by(Region.name).all()]
    form.city_id.choices = [(c.id, c.name) for c in City.query.order_by(City.name).all()]
    form.district_id.choices = [(d.id, d.name) for d in District.query.order_by(District.name).all()]
    form.property_type_id.choices = [(pt.id, pt.name) for pt in PropertyType.query.order_by(PropertyType.name).all()]
    form.amenities.choices = [(a.id, a.name) for a in Amenity.query.order_by(Amenity.name).all()]
    
    # تحديد القيم المبدئية للمنطقة والمدينة
    if request.method == 'GET':
        form.region_id.data = property.district.city.region.id
        form.city_id.data = property.district.city.id
        form.amenities.data = [a.id for a in property.amenities]
    
    if form.validate_on_submit():
        try:
            # تحديث بيانات العقار
            form.populate_obj(property)
            
            # تحديث المميزات
            property.amenities = []
            for amenity_id in form.amenities.data:
                amenity = Amenity.query.get(amenity_id)
                if amenity:
                    property.amenities.append(amenity)
            
            # معالجة الصور الجديدة
            for image in form.images.data:
                if image.filename != '':
                    public_id = upload_image_to_cloudinary(image)
                    if public_id:
                        new_image = PropertyImage(
                            property_id=property.id,
                            cloudinary_public_id=public_id,
                            is_main=False
                        )
                        db.session.add(new_image)
            
            db.session.commit()
            flash('تم تحديث العقار بنجاح', 'success')
            return redirect(url_for('admin_properties'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث العقار: {str(e)}', 'danger')
    
    return render_template('admin/edit_property.html', form=form, property=property)
    """تعديل عقار موجود"""
    if current_user.role != 'admin':
        abort(403)
    
    property = Property.query.get_or_404(property_id)
    form = PropertyForm(obj=property)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(property)
            
            # معالجة الصور الجديدة
            for image in form.images.data:
                if image.filename != '':
                    public_id = upload_image_to_cloudinary(image)
                    if public_id:
                        new_image = PropertyImage(
                            property_id=property.id,
                            cloudinary_public_id=public_id,
                            is_main=False
                        )
                        db.session.add(new_image)
            
            db.session.commit()
            flash('تم تحديث العقار بنجاح', 'success')
            return redirect(url_for('admin_properties'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث العقار: {str(e)}', 'danger')
    
    # تعبئة القوائم المنسدلة
    form.property_type_id.choices = [(pt.id, pt.name) for pt in PropertyType.query.all()]
    form.district_id.choices = [(d.id, f"{d.city.region.name} - {d.city.name} - {d.name}") 
                              for d in District.query.join(City).join(Region).all()]
    
    return render_template('admin/edit_property.html', form=form, property=property)

@app.route('/admin/properties/<int:property_id>/delete', methods=['POST'])
@login_required
def delete_property(property_id):
    """حذف عقار"""
    if current_user.role != 'admin':
        abort(403)
    
    property = Property.query.get_or_404(property_id)
    
    try:
        # حذف الصور من Cloudinary أولاً
        for image in property.images:
            if image.cloudinary_public_id:
                cloudinary.uploader.destroy(image.cloudinary_public_id)
        
        db.session.delete(property)
        db.session.commit()
        flash('تم حذف العقار بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف العقار: {str(e)}', 'danger')
    
    return redirect(url_for('admin_properties'))

@app.route('/admin/properties/<int:property_id>/toggle_featured', methods=['POST'])
@login_required
def toggle_featured(property_id):
    """تبديل حالة العقار المميز"""
    if current_user.role != 'admin':
        abort(403)
    
    property = Property.query.get_or_404(property_id)
    property.is_featured = not property.is_featured
    db.session.commit()
    
    status = "تم تمييز العقار" if property.is_featured else "تم إلغاء تمييز العقار"
    flash(status, 'success')
    return redirect(url_for('admin_properties'))

























@app.route('/api/cities')
def get_cities():
    region_id = request.args.get('region_id')
    if region_id:
        cities = City.query.filter_by(region_id=region_id).order_by(City.name).all()
    else:
        cities = []
    return jsonify([{'id': city.id, 'name': city.name} for city in cities])

@app.route('/api/districts')
def get_districts():
    city_id = request.args.get('city_id')
    if city_id:
        districts = District.query.filter_by(city_id=city_id).order_by(District.name).all()
    else:
        districts = []
    return jsonify([{'id': district.id, 'name': district.name} for district in districts])















@app.route('/admin/users')
@login_required
def admin_users():
    """إدارة المستخدمين (للمسؤول)"""
    if current_user.role != 'admin':
        flash('ليس لديك صلاحية الوصول إلى هذه الصفحة.', 'danger')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', '')
    
    query = User.query
    
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    
    # إضافة متغير التاريخ للاستخدام في تذييل الصفحة
    current_date = datetime.now()
    
    return render_template('admin/users.html', 
                           users=users, 
                           role_filter=role_filter,
                           date=current_date)

@app.route('/admin/bookings')
@login_required
def admin_bookings():
    """إدارة الحجوزات (للمسؤول)"""
    if current_user.role != 'admin':
        flash('ليس لديك صلاحية الوصول إلى هذه الصفحة.', 'danger')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Booking.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    bookings = query.order_by(Booking.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    
    # إضافة متغير التاريخ للاستخدام في تذييل الصفحة
    current_date = datetime.now()
    
    return render_template('admin/bookings.html', 
                           bookings=bookings, 
                           status_filter=status_filter,
                           date=current_date)

@app.route('/admin/regions')
@login_required
def admin_regions():
    """إدارة المناطق والمدن والأحياء (للمسؤول)"""
    if current_user.role != 'admin':
        flash('ليس لديك صلاحية الوصول إلى هذه الصفحة.', 'danger')
        return redirect(url_for('index'))
    
    regions = Region.query.all()
    
    # إضافة متغير التاريخ للاستخدام في تذييل الصفحة
    current_date = datetime.now()
    
    return render_template('admin/regions.html', 
                           regions=regions,
                           date=current_date)

@app.route('/admin/booking/<int:booking_id>/update', methods=['POST'])
@login_required
def update_booking_status(booking_id):
    """تحديث حالة الحجز (للمسؤول)"""
    if current_user.role != 'admin':
        flash('ليس لديك صلاحية القيام بهذا الإجراء.', 'danger')
        return redirect(url_for('index'))
    
    booking = Booking.query.get_or_404(booking_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'confirmed', 'cancelled', 'completed']:
        booking.status = new_status
        db.session.commit()
        flash('تم تحديث حالة الحجز بنجاح.', 'success')
    else:
        flash('حالة الحجز غير صالحة.', 'danger')
    
    return redirect(url_for('admin_bookings'))

@app.route('/admin/user/<int:user_id>/update', methods=['POST'])
@login_required
def update_user_role(user_id):
    """تحديث دور المستخدم (للمسؤول)"""
    if current_user.role != 'admin':
        flash('ليس لديك صلاحية القيام بهذا الإجراء.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    
    if new_role in ['admin', 'agent', 'customer']:
        user.role = new_role
        db.session.commit()
        flash('تم تحديث دور المستخدم بنجاح.', 'success')
    else:
        flash('دور المستخدم غير صالح.', 'danger')
    
    return redirect(url_for('admin_users'))


@app.route('/admin/property/<int:property_id>/status', methods=['POST'])
@login_required
def update_property_status(property_id):
    """تحديث حالة العقار (للمسؤول)"""
    if current_user.role != 'admin':
        flash('ليس لديك صلاحية القيام بهذا الإجراء.', 'danger')
        return redirect(url_for('index'))
    
    property = Property.query.get_or_404(property_id)
    new_status = request.form.get('status')
    
    if new_status in ['available', 'sold', 'rented']:
        property.status = new_status
        db.session.commit()
        flash('تم تحديث حالة العقار بنجاح.', 'success')
    else:
        flash('حالة العقار غير صالحة.', 'danger')
    
    return redirect(url_for('admin_properties'))
    
@app.route('/download_project')
def download_project():
    """رابط لتنزيل المشروع كاملاً"""
    return redirect(url_for('download_project_zip'))

@app.route('/download_project_zip')
def download_project_zip():
    """رابط لتنزيل المشروع كاملاً مع قاعدة البيانات"""
    import tempfile
    import subprocess
    
    try:
        # إنشاء ملف مضغوط في الذاكرة
        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # نسخ الملفات الأساسية
            for root, dirs, files in os.walk('.'):
                # استثناء المجلدات غير المرغوب فيها
                if any(exclude in root for exclude in ['__pycache__', '.git', 'venv', 'env', '.env', '.venv', 'instance']):
                    continue
                    
                for file in files:
                    # تخطي أنواع الملفات غير المرغوب فيها
                    if file.endswith(('.pyc', '.zip', '.git')) or file.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    arc_path = os.path.join(root.replace('./', ''), file)
                    
                    # إضافة الملف إلى الأرشيف
                    try:
                        zf.write(file_path, arc_path)
                    except Exception:
                        continue
            
            # إضافة ملف للاتصال المباشر بقاعدة البيانات بدلاً من استعادة نسخة محلية
            try:
                # استخراج رابط قاعدة البيانات من متغير البيئة
                db_url = os.environ.get('DATABASE_URL')
                
                # إضافة ملف شرح الاتصال بقاعدة البيانات
                db_info = """# الاتصال بقاعدة البيانات عن بعد

هذا الملف يشرح كيفية تشغيل المشروع مع الاتصال المباشر بقاعدة البيانات عن بعد.

## مميزات استخدام قاعدة البيانات عن بعد
1. لا حاجة لتثبيت PostgreSQL محلياً
2. قاعدة البيانات تحتوي على جميع البيانات جاهزة للاستخدام
3. يمكن للفريق العمل على نفس البيانات

## كيفية الاتصال بقاعدة البيانات عن بعد
ملف `.env.example` يحتوي على رابط قاعدة البيانات جاهز للاستخدام.
قم بنسخه إلى ملف `.env` واستخدامه مباشرة بدون تعديل.

```bash
cp .env.example .env
```

## تشغيل التطبيق
بعد نسخ ملف .env، قم بتشغيل التطبيق:
```bash
flask run
```
أو
```bash
gunicorn --bind 0.0.0.0:5000 main:app
```
"""
                zf.writestr('database/README.md', db_info)
                
                # إضافة نصائح التنزيل
                download_info = """# ملاحظات هامة حول تنزيل المشروع

## الاتصال بقاعدة البيانات
تم إعداد هذا المشروع للاتصال مباشرة بقاعدة البيانات عن بعد، لذلك لا حاجة إلى:
- تثبيت PostgreSQL محلياً
- إنشاء قاعدة بيانات محلية
- استعادة نسخة احتياطية

## الخطوات المطلوبة للتشغيل
1. نسخ ملف .env.example إلى .env (كما هو بدون تعديل)
2. تثبيت المكتبات المطلوبة
3. تشغيل الخادم

## في حال الرغبة بإنشاء قاعدة بيانات محلية
إذا كنت ترغب في استخدام قاعدة بيانات محلية بدلاً من القاعدة البعيدة، قم بتعديل ملف .env
وتغيير قيمة DATABASE_URL لتشير إلى قاعدة البيانات المحلية الخاصة بك.
"""
                zf.writestr('DOWNLOAD_INFO.md', download_info)
                
                # إضافة ملف إعدادات بيئة العمل المحلية مع الاتصال بقاعدة البيانات عن بعد
                remote_db_url = os.environ.get('DATABASE_URL')
                secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
                cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', 'due2rm5cb')
                api_key = os.environ.get('CLOUDINARY_API_KEY', '494883843628169')
                api_secret = os.environ.get('CLOUDINARY_API_SECRET', 'TnEHyxax7uSePlBh4EwS8QjJdBs')
                
                # إنشاء محتوى ملف .env
                env_content = f"""# متغيرات البيئة لتشغيل التطبيق محلياً
FLASK_APP=main.py
FLASK_DEBUG=1
# رابط قاعدة البيانات الموجودة على الإنترنت - جاهز للاستخدام مباشرة
DATABASE_URL={remote_db_url}
# مفتاح سري للتطبيق (قم بتغييره في الإنتاج)
SECRET_KEY={secret_key}

# إعدادات Cloudinary (جاهزة للاستخدام)
CLOUDINARY_CLOUD_NAME={cloud_name}
CLOUDINARY_API_KEY={api_key}
CLOUDINARY_API_SECRET={api_secret}
"""
                zf.writestr('.env.example', env_content)
                
                # إضافة مجلد للصور المحملة
                zf.writestr('static/uploads/.gitkeep', '')
                
            except Exception as e:
                # في حالة حدوث خطأ، نضيف ملف يوضح المشكلة
                error_message = f"""
# ملاحظة حول استعادة قاعدة البيانات

تعذر إضافة نسخة احتياطية من قاعدة البيانات بسبب الخطأ التالي:
{str(e)}

## كيفية إنشاء قاعدة بيانات جديدة
1. قم بإنشاء قاعدة بيانات PostgreSQL جديدة
2. قم بتعديل ملف .env لاستخدام قاعدة البيانات الجديدة
3. قم بتشغيل التطبيق، وسيتم إنشاء هيكل قاعدة البيانات تلقائياً

البيانات الافتراضية ستكون فارغة، ولكن يمكنك تسجيل الدخول باستخدام:
البريد الإلكتروني: admin@sayouriaqar.com
كلمة المرور: adminpassword
"""
                zf.writestr('database/README.md', error_message)
            
            # إضافة ملف readme
            readme_content = """# تطبيق السيعوري عقار

## كيفية تشغيل التطبيق محلياً مع الاتصال بقاعدة البيانات عن بعد
1. قم بتثبيت Python 3.8 أو أحدث
2. قم بتثبيت المكتبات المطلوبة: `pip install -r requirements.txt`
3. قم بنسخ ملف `.env.example` إلى `.env`:
   ```bash
   cp .env.example .env
   ```
   (ملف .env يحتوي على جميع الإعدادات اللازمة للاتصال بقاعدة البيانات عن بعد وخدمة Cloudinary)
4. قم بتشغيل الخادم مباشرة: `flask run` أو `gunicorn --bind 0.0.0.0:5000 main:app`
5. افتح المتصفح على العنوان: `http://localhost:5000`

## معلومات تسجيل الدخول الافتراضية
- البريد الإلكتروني: admin@sayouriaqar.com
- كلمة المرور: adminpassword

## الميزات الرئيسية
- إدارة العقارات: إضافة، تعديل، حذف، وعرض العقارات
- إدارة المستخدمين: التحكم في الأدوار والصلاحيات
- إدارة الحجوزات: متابعة طلبات معاينة العقارات
- إدارة المناطق: تنظيم المناطق والمدن والأحياء
- واجهة سهلة الاستخدام باللغة العربية
- دعم تحميل الصور وعرضها
- خرائط تفاعلية لعرض مواقع العقارات
"""
            zf.writestr('README.md', readme_content)
            
            # إضافة ملف متطلبات النظام
            requirements = """# متطلبات تشغيل التطبيق
Flask==2.3.3
Flask-SQLAlchemy==3.1.0
Flask-Login==0.6.2
Flask-WTF==1.1.1
Werkzeug==2.3.7
psycopg2-binary==2.9.7
email-validator==2.0.0
Pillow==10.0.0
python-dotenv==1.0.0
gunicorn==21.2.0
cloudinary==1.36.0
"""
            zf.writestr('requirements.txt', requirements)
        
        # إعادة ضبط المؤشر إلى بداية الملف
        memory_file.seek(0)
        
        # تحديد اسم الملف المضغوط مع التاريخ
        current_date = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"sayouri_aqar_project_{current_date}.zip"
        
        # إرسال الملف المضغوط كاستجابة للتنزيل
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'حدث خطأ أثناء محاولة تنزيل المشروع: {str(e)}', 'danger')
        return redirect(url_for('index'))
