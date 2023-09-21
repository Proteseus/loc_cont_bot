import os
from model import Order, Base

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

load_dotenv()

engine = create_engine(os.getenv('SQLALCHEMY_DATABASE_URI'))
Session = sessionmaker(bind=engine)

# Check if the database file already exists
if not os.path.exists('db/database.db'):
    Base.metadata.create_all(engine)

session = Session()

def create_user_order(username, fName, lName: None, primary_phone, secondary_phone: None, address_details, latitude, longitude):
    order = Order(username, fName, lName, primary_phone, secondary_phone, address_details, latitude, longitude)
    session.add(order)
    session.commit()
    return order

def add_order(username):
    order = session.query(Order).filter(Order.username == username).first()
    order.add_order()
    session.commit()
    return {"user": order.username, "order_count": order.order_count}

# @event.listens_for(Order, 'after_insert')
# def trigger_add_order(mapper, connection, target):
#     add_order(target.username)
