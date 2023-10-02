import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, Integer, String, DECIMAL, DATE
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
aa = timezone(timedelta(hours=3))

class Order(Base):
    __tablename__ = 'order'
    
    id = Column(String, primary_key=True, default=str(uuid.uuid4()))
    username = Column(String(10))
    fName = Column(String, nullable=False)
    lName = Column(String, nullable=True)
    primary_phone = Column(Integer)
    secondary_phone = Column(Integer, nullable=True)
    address_details = Column(String(255))
    latitude = Column(DECIMAL)
    longitude = Column(DECIMAL)
    order_count = Column(Integer)
    subscription_date = Column(DATE, default=datetime.now(tz=aa).date())
    
    def __init__(self, username, fName, lName, primary_phone, secondary_phone, address_details, latitude, longitude):
        self.username = username
        self.fName = fName
        self.lName = lName
        self.primary_phone = primary_phone
        self.secondary_phone = secondary_phone
        self.address_details = address_details
        self.latitude = latitude
        self.longitude = longitude
        self.order_count = 1
    
    def add_order(self):
        self.order_count += 1
