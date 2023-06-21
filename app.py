'''
This is the main file for the application. 
It contains the routes and views for the application.
'''

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import opendb, DB_URL
from database import *
from db_helper import *
from validators import *
from logger import log
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import stripe

app = Flask(__name__)

pkey = 'pk_test_51NLJp2SHtET9itmsOwQYkLRNorir5JmAZWuK4kGjbLhCYBkNMV2dvGeENbTmwZQQa4CPvY7Zev4oKSeFzF454z9v00F7CUrdCs'
skey = 'sk_test_51NLJp2SHtET9itms2Qe80NSY3kXypBJfZllQV06YsAaBhME8FsIywj1aEeBuNR8ES90i34Jn278uVwbmFtpncpUQ00YCDV2v91'

app = Flask(__name__)
app.secret_key  = '()*(#@!@#)'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.debug = True

def session_add(key, value):
    session[key] = value

def is_admin():
    return session.get('user_id') == 1

def save_file(file):
    filename = secure_filename(file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    return path  

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    if not validate_email(email):
        flash('Invalid email', 'danger')
        return redirect(url_for('index'))
    if not validate_password(password):
        flash('Invalid password', 'danger')
        return redirect(url_for('index'))
    db = opendb()
    user = db.query(User).filter_by(email=email).first()
    if user is not None and user.verify_password(password):
        session_add('user_id', user.id)
        session_add('user_name', user.name)
        session_add('user_email', user.email)
        session_add('isauth', True)
        session_add('isadmin', is_admin())
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid email or password', 'danger')
        return redirect(url_for('index'))
    
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    cpassword = request.form.get('cpassword')
    db = opendb()
    if not validate_username(name):
        flash('Invalid username', 'danger')
        return redirect(url_for('index'))
    if not validate_email(email):
        flash('Invalid email', 'danger')
        return redirect(url_for('index'))
    if not validate_password(password):
        flash('Invalid password', 'danger')
        return redirect(url_for('index'))
    if password != cpassword:
        flash('Passwords do not match', 'danger')
        return redirect(url_for('index'))
    if db.query(User).filter_by(email=email).first() is not None    :
        flash('Email already exists', 'danger')
        return redirect(url_for('index'))
    elif db.query(User).filter_by(name=name).first() is not None:
        flash('Username already exists', 'danger')
        return redirect(url_for('index'))
    else:
        db_save(User(name=name, email=email, password=password))
        flash('User registered successfully', 'success')
        return redirect(url_for('index'))
    
@app.route('/dashboard')
def dashboard():
    if session.get('isauth'):
        user_id = session.get('user_id')
        db = opendb()
        attendees = db.query(Attendee).filter_by(user_id=user_id).all()
        print(attendees)
        my_events = []
        for attendee in attendees:
            print('--------------')
            print(attendee)
            event = db.query(Event).filter_by(id=attendee.event).first()
            my_events.append(event)
        
        return render_template('dashboard.html', my_events=my_events)
    else:
        return redirect(url_for('index'))

@app.route('/profile/add', methods=['POST'])
def add_profile():
    if session.get('isauth'):
        user_id = session.get('user_id')
        if request.method == 'POST':
            print(request.form)
            city = request.form.get('city')
            gender = request.form.get('gender')
            avatar = request.files.get('avatar')
            db = opendb()
            if not validate_city(city):
                flash('Invalid city', 'danger')
                return redirect(url_for('dashboard'))
            if not validate_avatar(avatar):
                flash('Invalid avatar file', 'danger')
                return redirect(url_for('dashboard'))
            if db.query(Profile).filter_by(user_id=user_id).first() is not None:
                flash('Profile already exists', 'danger')
                return redirect(url_for('view_profile'))
            else:
                db_save(Profile(user_id = user_id, city=city, gender=gender, avatar=save_file(avatar)))
                flash('Profile added successfully', 'success')
                return redirect(url_for('dashboard'))
    else:
        flash('Please login to continue', 'danger')
        return redirect(url_for('index'))
        
@app.route('/profile/edit', methods=['POST'])
def edit_profile():
    if session.get('isauth'):
        profile = db_get_by_field(Profile, user_id=session.get('user_id'))
        if profile is not None:
            profile.city = request.form.get('city')
            profile.gender = request.form.get('gender')
            avatar = request.files.get('avatar')
            if avatar is not None:
                profile.avatar = save_file(avatar)
            db_save(profile)
            flash('Profile updated successfully', 'success')
            return redirect(url_for('dashboard'))
    else:
        flash('Please login to continue', 'danger')
        return redirect(url_for('index'))    

@app.route('/profile')
def view_profile():
    if session.get('isauth'):
        profile = db_get_by_field(Profile, user_id=session.get('user_id'))
        if profile is not None:
            # return render_template('profile.html', profile=profile)
            return redirect(url_for('dashboard'))
        else:
            flash(f'<a class="text-danger" href="#" data-bs-toggle="modal" data-bs-target="#profileModal">Create a profile</a>', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Please login to continue', 'danger')
        return redirect(url_for('index'))

@app.route('/home')  
def home():
    return render_template('index.html') 

@app.route('/events')
def events():
    if session.get('isauth'):
#  get all upcoming events from current date
      db = opendb()
      events = db.query(Event).filter(Event.date >= datetime.now()).all()
      return render_template('events.html', events=events)
    else:
        flash('Please login to continue', 'danger')
        return redirect(url_for('index'))

@app.route('/event/create', methods=[ 'POST'])
def event_create():
    if request.method == 'POST':
        organization = request.form.get('organization')
        name = request.form.get('name')
        description = request.form.get('description')
        date = request.form.get('date')
        time = request.form.get('time')
        location = request.form.get('location')
        days = request.form.get('days')
        avtar = request.files.get('avatar')
        date_sql = datetime.strptime(date, '%Y-%m-%d')
        time_sql = datetime.strptime(time, '%H:%M')
        if len(organization) < 3:
            flash('Invalid organization', 'danger')
            return redirect(url_for('events'))
        if len(name) < 3:
            flash('Invalid name', 'danger')
            return redirect(url_for('events'))
        if len(description) < 3:
            flash('Invalid description', 'danger')
            return redirect(url_for('events'))
        if len(location) < 3:
            flash('Invalid location', 'danger')
            return redirect(url_for('events'))

        db = opendb()
        user_id = session.get('user_id')
        db_save(Event(organization=organization, name=name, 
                      description=description, date=date_sql, time=time_sql, 
                      location=location, days=days, avatar=save_file(avtar), user_id=user_id))
        flash('Event created successfully', 'success')
        return redirect(url_for('events'))
    flash('Create event', 'warning')
    return redirect(url_for('events'))

@app.route('/event/detail/<int:id>')
def event_detail(id):
    db = opendb()
    event = db.query(Event).filter_by(id=id).first()
    # get all seminars for this event
    seminars = db.query(Seminar).filter_by(event=id).all()
    # check if user is attending
    if session.get('isauth'):
        print(session)
        user_id = session.get('user_id')
        print(f'{user_id} {id}')
        print(f'{db.query(Attendee).filter_by(user_id=user_id, event=id)}')
        if db.query(Attendee).filter_by(user_id=user_id, event=id).first() is not None:
            is_attending = True
        else:
            is_attending = False
        return render_template('event_detail.html', event=event, seminars=seminars, eid=id, is_attending=is_attending)
    else:
        flash('Please login to register for this event', 'danger')
    return render_template('event_detail.html', event=event, seminars=seminars, eid=id)


@app.route('/seminar')
def seminar():
    if session.get('isauth'):
       events = db_get_all(Event)
       seminars = db_get_all(Seminar)
       return render_template('seminar.html', seminars=seminars,events=events)
    else:
        flash('Please login to continue', 'danger')
        return redirect(url_for('index'))

@app.route('/seminar/create', methods=[ 'POST'])
def seminar_create():
   
    if request.method == 'POST':
        topic = request.form.get('topic')
        sem_description = request.form.get('sem_description')
        sem_date = request.form.get('sem_date')
        sem_time = request.form.get('sem_time')
        address = request.form.get('address')
        notes = request.files.get('notes')
        event = request.form.get('event_id')
        date_sql = datetime.strptime(sem_date, '%Y-%m-%d')
        time_sql = datetime.strptime(sem_time, '%H:%M')
        if len(topic) < 3:
            flash('Invalid topic', 'danger')
            return redirect(url_for('seminar'))
        if len(sem_description) < 3:
            flash('Invalid sem_description', 'danger')
            return redirect(url_for('seminar'))
        if len(address) < 3:
            flash('Invalid sem_location', 'danger')
            return redirect(url_for('seminar'))
        
        db = opendb()
        user_id = session.get('user_id')
        db_save(Seminar(topic=topic, sem_description=sem_description, sem_date=date_sql, 
                        sem_time=time_sql, address=address, 
                        notes=save_file(notes),event=event, user_id=user_id))
        
        flash('Seminar created successfully', 'success')
        return redirect(url_for('seminar'))
    flash('Create seminar', 'warning')
    return redirect(url_for('seminar'))

@app.route('/speaker/create', methods=['GET','POST'])
def speakercreate():
    if request.method == 'POST':
        speaker_image = request.files.get('profile_image')
        speakername = request.form.get('name')
        occupation = request.form.get('occupation') 
        company = request.form.get('company')
        gender = request.form.get('gender')
        linkedin = request.form.get('linkedin')
        seminar_id = request.form.get('seminar_id')

        # if (speaker_image) < None:
        #     flash('Invalid speaker_image', 'danger')
        #     return redirect(url_for('speakerprofiles'))
        if len(speakername) < 3:
            flash('Invalid speaker_name', 'danger')
            return redirect(url_for('speakerprofiles'))
        if len(occupation) < 3:
            flash('Invalid speaker_occupation', 'danger')
            return redirect(url_for('speakerprofiles'))
        if len(company) < 3:
            flash('Invalid speaker_company', 'danger')
            return redirect(url_for('speakerprofiles'))
        
        db = opendb()
        user_id = session.get('user_id')
        db_save(Speakerprofiles(profile_image=save_file(speaker_image),
                                occupation=occupation,
                                company=company, gender=gender, name=speakername, linkedin=linkedin , user_id=user_id, seminar=seminar_id ))
        flash('Speakerprofiles created successfully', 'success')
        return redirect(url_for('speakerprofiles'))
    flash('Create speakerprofiles', 'warning')
    return redirect(url_for('speakerprofiles'))

@app.route('/speaker/profiles', methods=[ 'GET', 'POST'])
def speakerprofiles():
    if session.get('isauth'):
        speakers = db_get_all(Speakerprofiles )
        seminars = db_get_all(Seminar)
        return render_template('speaker.html',  seminars=seminars, speakers=speakers)
    else:
        flash('Please login to continue', 'danger')
        return redirect(url_for('index'))
    
    
@app.route('/speakerprofile/detail/<int:id>')
def speakerprofile_detail(id):
    db = opendb()
    speaker = db.query(Speakerprofiles).filter_by(id=id).first()
    return render_template('speaker.html', speaker=speaker)

# seminar details
@app.route('/seminar/detail/<int:id>')
def seminar_detail(id):
    db = opendb()
    # get event for this seminar
    seminar = db.query(Seminar).filter_by(id=id).first()
    event = db.query(Event).filter_by(id=seminar.event).first()
    # speakers = db.query(Speakerprofiles).
    speakers = db.query(Speakerprofiles).filter_by(seminar=id).all()

    return render_template('seminar_detail.html', s=seminar, e=event, speakers=speakers)


@app.route('/event/register/<int:id>', methods=['GET', 'POST'])
def event_register(id):
    if session.get('isauth'):
        db = opendb()
        event = db.query(Event).filter_by(id=id).first()
        user_id = session.get('user_id')
        fees = event.fee
        if fees > 0:
            return redirect(url_for('event_payment', id=id))
        else:
            attendee = Attendee(event=event.id, user_id=user_id)
            db_save(attendee)   
            flash('You have registered for this event', 'success')
            return redirect(url_for('event_detail', id=id))


@app.route('/event/payment/<int:id>', methods=['GET', 'POST'])
def event_payment(id):
    if session.get('isauth'):
        db = opendb()
        event = db.query(Event).filter_by(id=id).first()
        user_id = session.get('user_id')
        fees = event.fee
        # stripe payment integration
        if request.method == 'POST':
            stripe.api_key = skey
            customer = stripe.Customer.create(email=request.form['email'])
            ephemeralKey = stripe.EphemeralKey.create(
                customer=customer['id'],
                stripe_version='2022-11-15',
            )
            paymentIntent = stripe.PaymentIntent.create(
                amount=int(float(request.form['amount'])),
                currency='inr',
                customer=customer['id'],
                automatic_payment_methods={
                'enabled': True,
                },
            )
            print(f"Log: {request.form.values()}")
            return jsonify(paymentIntent=paymentIntent.client_secret,
                            ephemeralKey=ephemeralKey.secret,
                            customer=customer.id,
                            publishableKey=pkey)
        return render_template('event_payment.html', event=event, fees=fees)
    else:
        flash('Please login to continue', 'danger')
        return redirect(url_for('index'))
    
@app.route('/checkout', methods=['GET','POST'])
def checkout():
    if request.method == 'POST':
        stripe.api_key = skey
        customer = stripe.Customer.create(email=request.form['email'])
        ephemeralKey = stripe.EphemeralKey.create(
            customer=customer['id'],
            stripe_version='2022-11-15',
        )
        paymentIntent = stripe.PaymentIntent.create(
            amount=int(float(request.form['amount'])),
            currency='inr',
            customer=customer['id'],
            automatic_payment_methods={
            'enabled': True,
            },
        )
        print(f"Log: {request.form.values()}")
        return jsonify(paymentIntent=paymentIntent.client_secret,
                        ephemeralKey=ephemeralKey.secret,
                        customer=customer.id,
                        publishableKey=pkey)
    return render_template('index.html')

@app.route('/config')
def get_publishable_key():
    return jsonify({'publicKey': pkey})

@app.route('/create-checkout-session', methods=['GET','POST'])
def create_checkout_session():
    try:
        stripe.api_key = skey
        amount = request.form['amount']
        email = request.form['email']
        name = request.form['title']
        event_id = request.form['event_id']
        user_id = session.get('user_id')
        session_add('event_id', event_id)
        session_add('user_id', user_id)
        # try:
        domain_url = "http://127.0.0.1:8000/"
        checkout_session = stripe.checkout.Session.create(
                success_url=domain_url + "success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=domain_url + "cancelled",
                payment_method_types=["card"],
                mode="payment",
                line_items=[
                    {   
                        'quantity': 1,
                        "price_data": {
                            "currency": "inr",
                            "unit_amount": int(float(amount))*100,
                            "product_data": {
                                "name": name,
                                "images": ["https://i.imgur.com/EHyR2nP.png"],
                            },
                        },
                    }
                ]
        )
        return jsonify({"sessionId": checkout_session["id"]})
    except Exception as e:
        print(e)
        return jsonify(error=str(e)), 403

@app.route('/success')
def success():
    if session.get('isauth'):
        db = opendb()
        event_id = session.get('event_id')
        user_id = session.get('user_id')
        # remove session data
        session['event_id'] = None
        event = db.query(Event).filter_by(id=event_id).first()
        payment = Payment(event=event_id, user_id=user_id, amount= event.fee, transaction_id=f'{user_id}{event_id}', is_paid=1)
        attendee = Attendee(event=event_id, user_id=user_id, is_paid=1)
        db_save(attendee)   
        flash('You have registered for this event', 'success')
        return redirect(url_for('event_detail', id=event_id))
    else:
        print(session)
    return render_template('success.html')

@app.route('/cancelled')
def cancelled():
    return render_template('cancelled.html')

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8000, debug=True)
 