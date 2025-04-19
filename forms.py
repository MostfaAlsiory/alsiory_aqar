from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms import IntegerField, FloatField, SelectField, SelectMultipleField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional
from datetime import datetime
from werkzeug.security import safe_str_cmp
class UserRegistrationForm(FlaskForm):
    """نموذج تسجيل مستخدم جديد"""
    username = StringField('اسم المستخدم', validators=[
        DataRequired(), 
        Length(min=3, max=50, message='يجب أن يكون اسم المستخدم بين 3 و 50 حرفًا')
    ])
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(), 
        Email(message='يرجى إدخال بريد إلكتروني صالح')
    ])
    phone = StringField('رقم الهاتف', validators=[
        DataRequired(), 
        Length(min=9, max=20, message='يرجى إدخال رقم هاتف صالح')
    ])
    password = PasswordField('كلمة المرور', validators=[
        DataRequired(), 
        Length(min=8, message='يجب أن تكون كلمة المرور 8 أحرف على الأقل')
    ])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[
        DataRequired(), 
        EqualTo('password', message='يجب أن تتطابق كلمات المرور')
    ])
    submit = SubmitField('تسجيل')

class LoginForm(FlaskForm):
    """نموذج تسجيل الدخول"""
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(), 
        Email(message='يرجى إدخال بريد إلكتروني صالح')
    ])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    remember = BooleanField('تذكرني')
    submit = SubmitField('تسجيل الدخول')

class PropertyForm(FlaskForm):
    """نموذج إضافة أو تعديل عقار"""
    title = StringField('عنوان العقار', validators=[
        DataRequired(), 
        Length(min=5, max=150, message='يجب أن يكون العنوان بين 5 و 150 حرفًا')
    ])
    description = TextAreaField('الوصف', validators=[
        DataRequired(), 
        Length(min=20, max=2000, message='يجب أن يكون الوصف بين 20 و 2000 حرف')
    ])
    price = FloatField('السعر', validators=[
        DataRequired(), 
        NumberRange(min=1, message='يجب أن يكون السعر أكبر من صفر')
    ])
    area = FloatField('المساحة (متر مربع)', validators=[
        DataRequired(), 
        NumberRange(min=1, message='يجب أن تكون المساحة أكبر من صفر')
    ])
    bedrooms = IntegerField('عدد غرف النوم', validators=[Optional()])
    bathrooms = IntegerField('عدد الحمامات', validators=[Optional()])
    floors = IntegerField('عدد الطوابق', validators=[Optional()])
    year_built = IntegerField('سنة البناء', validators=[Optional()])
    
    # معلومات الموقع
    region_id = SelectField('المنطقة', coerce=int, validators=[DataRequired()])
    city_id = SelectField('المدينة', coerce=int, validators=[DataRequired()])
    district_id = SelectField('الحي', coerce=int, validators=[DataRequired()])
    address = StringField('العنوان التفصيلي', validators=[
        DataRequired(), 
        Length(min=5, max=200, message='يجب أن يكون العنوان بين 5 و 200 حرف')
    ])
    latitude = FloatField('خط العرض', validators=[
        DataRequired(), 
        NumberRange(min=-90, max=90, message='يجب أن يكون خط العرض بين -90 و 90')
    ])
    longitude = FloatField('خط الطول', validators=[
        DataRequired(), 
        NumberRange(min=-180, max=180, message='يجب أن يكون خط الطول بين -180 و 180')
    ])
    
    # معلومات التصنيف
    property_type_id = SelectField('نوع العقار', coerce=int, validators=[DataRequired()])
    transaction_type = SelectField('نوع المعاملة', choices=[
        ('sale', 'بيع'), 
        ('rent', 'إيجار')
    ], validators=[DataRequired()])
    
    # المميزات
    amenities = SelectMultipleField('المميزات', coerce=int)
    
    # الصور
    images = MultipleFileField('صور العقار', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'الصور فقط!')
    ])
    
    submit = SubmitField('حفظ العقار')

class PropertySearchForm(FlaskForm):
    """نموذج البحث عن عقارات"""
    keyword = StringField('البحث')
    region_id = SelectField('المنطقة', coerce=int)
    property_type_id = SelectField('نوع العقار', coerce=int)
    transaction_type = SelectField('نوع المعاملة', choices=[
        ('', 'الكل'), 
        ('sale', 'بيع'), 
        ('rent', 'إيجار')
    ])
    min_price = FloatField('السعر من', validators=[Optional()])
    max_price = FloatField('السعر إلى', validators=[Optional()])
    bedrooms = IntegerField('الحد الأدنى لغرف النوم', validators=[Optional()])
    bathrooms = IntegerField('الحد الأدنى للحمامات', validators=[Optional()])
    min_area = FloatField('الحد الأدنى للمساحة', validators=[Optional()])
    
    submit = SubmitField('بحث')

class BookingForm(FlaskForm):
    """نموذج حجز موعد معاينة"""
    booking_date = DateTimeField('تاريخ ووقت المعاينة', 
                                 validators=[DataRequired()], 
                                 format='%Y-%m-%d %H:%M',
                                 default=datetime.now)
    notes = TextAreaField('ملاحظات', validators=[Optional(), Length(max=500)])
    
    submit = SubmitField('حجز موعد')

class ReviewForm(FlaskForm):
    """نموذج تقييم عقار"""
    rating = IntegerField('التقييم (1-5)', validators=[
        DataRequired(), 
        NumberRange(min=1, max=5, message='يجب أن يكون التقييم بين 1 و 5')
    ])
    comment = TextAreaField('التعليق', validators=[
        Optional(), 
        Length(max=500, message='يجب ألا يتجاوز التعليق 500 حرف')
    ])
    
    submit = SubmitField('إرسال التقييم')

class AdminPropertyForm(PropertyForm):
    """نموذج إدارة العقار للمسؤول"""
    status = SelectField('الحالة', choices=[
        ('available', 'متاح'), 
        ('sold', 'تم البيع'), 
        ('rented', 'تم التأجير')
    ])
    is_featured = BooleanField('عقار مميز')
    
    agent_id = SelectField('الوكيل المسؤول', coerce=int, validators=[Optional()])

class AdminUserForm(FlaskForm):
    """نموذج إدارة المستخدم للمسؤول"""
    username = StringField('اسم المستخدم', validators=[
        DataRequired(), 
        Length(min=3, max=50)
    ])
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(), 
        Email()
    ])
    phone = StringField('رقم الهاتف', validators=[
        DataRequired(), 
        Length(min=9, max=20)
    ])
    role = SelectField('الدور', choices=[
        ('customer', 'عميل'), 
        ('agent', 'وكيل'), 
        ('admin', 'مسؤول')
    ])
    is_active = BooleanField('نشط')
    
    submit = SubmitField('حفظ التغييرات')