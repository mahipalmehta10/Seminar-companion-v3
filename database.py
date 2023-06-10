'''
This file contains the database models and the database connection code.
'''
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm import relationship, backref
from sqlalchemy import func
from datetime import datetime

DB_NAME = 'database.sqlite'
DB_URL = f'sqlite:///{DB_NAME}'

Base = declarative_base()
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    email = Column(String(64), nullable=False, unique=True)
    password = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def verify_password(self, password):
        return self.password == password
    
    def __repr__(self):
        return f'<User {self.name}>'
    
    def __str__(self):
        return self.name

class Profile(Base):
    __tablename__ = 'profiles'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    city = Column(String(64), default='Lucknow')
    gender = Column(String(2), default='M')
    avatar = Column(String(255), nullable=False)
    # todo add more fields
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __repr__(self):
        return f'<Profile {self.user.name}>'
    
    def __str__(self):
        return self.user.name
    
class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    organization = Column(String(64), nullable=False)
    name = Column(String(64), nullable=False)
    description = Column(String(255), nullable=False)
    date= Column(DateTime, nullable=False)
    time= Column(DateTime, nullable=False)
    location = Column(String(64), nullable=False)
    days = Column(Integer, nullable=False)
    avatar=Column(String(255), nullable=False)
    fee = Column(Float, nullable=False, default=0.0)
   
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
    
    def __repr__(self):
        return f'<Event {self.name}>'
    
    def __str__(self):
        return self.name
    
class Seminar(Base):
    __tablename__ = 'seminars'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    topic = Column(String(64), nullable=False)
    sem_description = Column(String(255), nullable=False)
    sem_date= Column(DateTime, nullable=False)
    sem_time= Column(DateTime, nullable=False)
    address = Column(String(64), nullable=False)
    notes = Column(String(255), nullable=False)
    event = Column(ForeignKey('events.id'))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Seminar'
        verbose_name_plural = 'Seminars'
    
    def __repr__(self):
        return f'<Seminar {self.topic}>'
    
    def __str__(self):
        return self.topic
    
class Speakerprofiles(Base):
    __tablename__ = 'speakerprofiles'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(64), nullable=False)
    occupation = Column(String(255), nullable=False)
    company = Column(String(64), nullable=False)
    profile_image=Column(String(255), nullable=False)
    linkedin = Column(String(255), nullable=False, default="https://www.linkedin.com/")
    gender = Column(String(2), default='M')
    seminar = Column(ForeignKey('seminars.id'))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Speakerprofile'
        verbose_name_plural = 'Speakerprofiles'
    
    def __repr__(self):
        return f'<Speakerprofile {self.name}>'
    
    def __str__(self):
        return self.name
    
class Attendee(Base):
    __tablename__ = 'attendee'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    event = Column(ForeignKey('events.id'))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_paid = Column(Integer, default=0)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Attendee'
        verbose_name_plural = 'Attendees'

    def __repr__(self):
        return f'<Attendee {self.user_id}>'
    
    def __str__(self):
        return str(self.user_id)    

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    event = Column(ForeignKey('events.id'))
    amount = Column(Float, nullable=False, default=0.0)
    transaction_id = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_paid = Column(Integer, default=0)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __repr__(self):
        return f'<Payment {self.user.name}>'
    
    def __str__(self):
        return self.user.name


def get_list_of_attendees(event_id):
    session = opendb()
    attendees = session.query(Attendee).filter_by(event=event_id).all()
    return attendees

def get_list_of_speakers(seminar_id):
    session = opendb()
    speakers = session.query(Speakerprofiles).filter_by(seminar=seminar_id).all()
    return speakers

def get_list_of_seminars(event_id):
    session = opendb()
    seminars = session.query(Seminar).filter_by(event=event_id).all()
    return seminars

def save_payment(user_id, event_id, amount, transaction_id):
    session = opendb()
    payment = Payment(user_id=user_id, event=event_id, amount=amount, transaction_id=transaction_id)
    session.add(payment)
    session.commit()
    session.close()

def check_payment(user_id, event_id):
    session = opendb()
    payment = session.query(Payment).filter_by(user_id=user_id, event=event_id).first()
    if payment:
        return True
    else:
        return False
    
def save_attendee(user_id, event_id):
    session = opendb()
    attendee = Attendee(user_id=user_id, event=event_id)
    session.add(attendee)
    session.commit()
    session.close()



    
def opendb():
    engine = create_engine(DB_URL)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    return Session()

if __name__ == '__main__':
    engine = create_engine(DB_URL, echo=True)
    Base.metadata.create_all(engine)
    