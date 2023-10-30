import os
from model import Order, Trackable, Base

from dotenv import load_dotenv
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import sessionmaker

load_dotenv()

db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
engine = create_engine(db_uri)
Session = sessionmaker(bind=engine)

# Check if the database exists
# inspector = inspect(engine)
# if not inspector.has_table('order'):
#     Base.metadata.create_all(engine)

if not os.path.exists(db_uri):
    Base.metadata.create_all(engine)

session = Session()

def create_user_order(userid, username, fName, primary_phone, secondary_phone: None, address_details, latitude, longitude, lang, subscription_type):
    order = Order(userid, username, fName, primary_phone, secondary_phone, address_details, latitude, longitude, lang, subscription_type)
    session.add(order)
    session.commit()
    return order

def add_order(username):
    order = session.query(Order).filter(Order.userid == username).first()
    order.add_order()
    session.commit()
    return {"user": order.userid, "order_count": order.order_count}

def delete_order(username):
    order = session.query(Order).filter(Order.userid == username).first()
    if order:
        session.delete(order)
        session.commit()
        return {"user": order.userid, "order_count": order.order_count}
    else:
        return False

def change_lang(username, lang):
    order = session.query(Order).filter(Order.userid == username).first()
    if order:
        order.language = lang
        session.commit()
        return {"user": order.userid, "lang": order.language}
    else:
        return False

def track(order_id):
    tracker = Trackable(order_id)
    session.add(tracker)
    session.commit()
    return tracker.id