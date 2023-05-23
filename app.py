'''
This is the main file for the application. 
It contains the routes and views for the application.
'''

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import opendb, DB_URL
from database import User, Profile, Event, Seminar,Speakerprofiles
from db_helper import *
from validators import *
from templates.logger import log
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key  = '()*(#@!@#)'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.debug = True

def session_add(key, value):
    session[key] = value

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
        return render_template('dashboard.html')
    else:
        return redirect(url_for('index'))

@app.route('/profile/add', methods=['POST'])
def add_profile():
    if session.get('isauth'):
        user_id = session.get('user_id')
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
            return render_template('profile.html', profile=profile)
        else:
            flash(f'<a class="text-danger" href="#" data-bs-toggle="modal" data-bs-target="#profileModal">Create a profile</a>', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Please login to continue', 'danger')
        return redirect(url_for('index'))
    
@app.route('/events')
def events():
#  get all upcoming events from current date
    db = opendb()
    events = db.query(Event).filter(Event.date >= datetime.now()).all()
    return render_template('events.html', events=events)

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
    flash('Create event', 'warning')
    return redirect(url_for('events'))

@app.route('/event/detail/<int:id>')
def event_detail(id):
    db = opendb()
    event = db.query(Event).filter_by(id=id).first()
    # get all seminars for this event
    seminars = db.query(Seminar).filter_by(event=id).all()
    return render_template('event_detail.html', event=event, seminars=seminars)


@app.route('/seminar')
def seminar():
    events = db_get_all(Event)
    seminars = db_get_all(Seminar)
    return render_template('seminar.html', seminars=seminars)

@app.route('/seminar/create', methods=[ 'POST'])
def seminar_create():
    if request.method == 'POST':
        topic = request.form.get('topic')
        speaker = request.form.get('speaker')
        linkedin = request.form.get('Linkedin')
        sem_description = request.form.get('sem_description')
        sem_date = request.form.get('sem_date')
        sem_time = request.form.get('sem_time')
        sem_location = request.form.get('sem_location')
        notes = request.files.get('notes')
        city= request.form.get('city')
        event = request.form.get('event_id')
        if len(topic) < 3:
            flash('Invalid topic', 'danger')
            return redirect(url_for('seminar'))
        if len(speaker) < 3:
            flash('Invalid speaker', 'danger')
            return redirect(url_for('seminar'))
        if len(linkedin) < 3:
            flash('Invalid linkedin', 'danger')
            return redirect(url_for('seminar'))
        if len(sem_description) < 3:
            flash('Invalid sem_description', 'danger')
            return redirect(url_for('seminar'))
        if len(sem_location) < 3:
            flash('Invalid sem_location', 'danger')
            return redirect(url_for('seminar'))
        if len(city) < 3:
            flash('Invalid city', 'danger')
            return redirect(url_for('seminar'))
        db = opendb()
        user_id = session.get('user_id')
        db_save(Seminar(topic=topic, speaker=speaker, linkedin=linkedin, 
                        sem_description=sem_description, sem_date=sem_date, 
                        sem_time=sem_time, sem_location=sem_location, 
                        notes=save_file(notes), city=city), event=event, user_id=user_id)
        flash('Seminar created successfully', 'success')
        pass
    flash('Create seminar', 'warning')
    return redirect(url_for('seminar'))

@app.route('/speaker/create', methods=[ 'POST'])
def speakerprofiles():
    if request.method == 'POST':
        speaker_image = request.files.get('speaker_image')
        speaker_name = request.form.get('speaker_name')
        occupation = request.form.get('occupation') 
        company = request.form.get('company')
        gender = request.form.get('gender')

        if (speaker_image) < None:
            flash('Invalid speaker_image', 'danger')
            return redirect(url_for('speakerprofiles'))
        if (speaker_name) < 3:
            flash('Invalid speaker_name', 'danger')
            return redirect(url_for('speakerprofiles'))
        if (occupation) < 3:
            flash('Invalid speaker_occupation', 'danger')
            return redirect(url_for('speakerprofiles'))
        if (company) < 3:
            flash('Invalid speaker_company', 'danger')
            return redirect(url_for('speakerprofiles'))
        
        db = opendb()
        db_save(Speakerprofiles(speaker_image=save_file(speaker_image),
                                speaker_name=speaker_name,occupation=occupation,
                                company=company, gender=gender))
        flash('Speakerprofiles created successfully', 'success')
        flash('Create speakerprofiles', 'warning')
        return redirect(url_for('speakerprofiles'))

@app.route('/speaker/create', methods=[ 'POST'])
def speakercreate():
    if session.get('isauth'):
        speakercreate = db_get_all(Profile )
        return render_template('speakerprofiles.html', speakercreate=speakercreate)
    else:
        flash('Please login to continue', 'danger')
        return redirect(url_for('index'))
if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8000, debug=True)
 