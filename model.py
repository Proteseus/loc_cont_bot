import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, Integer, String, DECIMAL, DATE, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
aa = timezone(timedelta(hours=3))

class Order(Base):
    __tablename__ = 'order'
    
    id = Column(String, primary_key=True)
    username = Column(String(10))
    Name = Column(String, nullable=False)
    primary_phone = Column(Integer)
    secondary_phone = Column(Integer, nullable=True)
    address_details = Column(String(255))
    latitude = Column(DECIMAL)
    longitude = Column(DECIMAL)
    order_count = Column(Integer)
    language = Column(String(10), default='English')
    subscription = Column(String(10), default='No')
    subscription_date = Column(DATE, default=datetime.now(tz=aa).date())

    
    def __init__(self, username, Name, primary_phone, secondary_phone, address_details, latitude, longitude, lang, subscription_type):
        self.id = self.generate_id()
        self.username = username
        self.Name = Name
        self.primary_phone = primary_phone
        self.secondary_phone = secondary_phone
        self.address_details = address_details
        self.latitude = latitude
        self.longitude = longitude
        self.order_count = 1
        self.language = lang
        self.subscription = subscription_type
    
    @staticmethod
    def generate_id():
        # Generate a unique 4-digit numeric id without preceding zeros
        return str(uuid.uuid4().int % 90000 + 10000)
    
    def add_order(self):
        self.order_count += 1
    
    def change_lang(self, lang):
        self.language = lang

class Trackable(Base):
    __tablename__ = 'trackable'    
    id = Column(Integer, primary_key=True)
    order_id = Column(String, ForeignKey('order.id'))
    date = Column(DATETIME, default=datetime.now(tz=aa))

    def __init__(self, order_id):
        self.id = self.generate_id()
        self.order_id = order_id

    @staticmethod
    def generate_id():
        # Generate a unique 4-digit numeric id without preceding zeros
        return str(uuid.uuid4().int % 900000 + 100000)
