# Add these lines at the very top of app.py
import sys
import os

# Apply compatibility patches
try:
    import app_patch
except ImportError:
    pass

# Then the rest of your imports
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
# ... rest of your code
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_bcrypt import Bcrypt
import os
import uuid
from dotenv import load_dotenv
from models import db, User, Summary
from forms import RegistrationForm, LoginForm
#from utils.youtube import get_video_info, get_transcript
from utils.summarizer import generate_summary
from utils.pdf_generator import create_pdf
from utils.youtube_api import get_video_info
from utils.youtube import get_transcript
# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'pdfs')

# Create the upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/summarize', methods=['POST'])
@login_required
def summarize():
    youtube_url = request.form.get('youtube_url')
    
    if not youtube_url:
        return render_template('index.html', error="Please enter a YouTube URL")
    
    try:
        # Get video information
        video_info = get_video_info(youtube_url)
        
        # Get video transcript
        transcript_text = get_transcript(youtube_url)
        
        if not transcript_text:
            return render_template('index.html', error="Could not retrieve transcript for this video")
        
        # Generate summary
        summary = generate_summary(transcript_text, video_info['title'])
        
        # Create unique filename
        filename = f"{uuid.uuid4()}.pdf"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Generate PDF
        create_pdf(
            pdf_path=pdf_path,
            title=video_info['title'],
            thumbnail_url=video_info['thumbnail_url'],
            channel=video_info['channel'],
            summary=summary,
            duration=video_info['duration']
        )
        
        # Save summary record to database
        summary_record = Summary(
            video_id=video_info['video_id'],
            video_title=video_info['title'],
            pdf_filename=filename,
            user_id=current_user.id
        )
        db.session.add(summary_record)
        db.session.commit()
        
        return render_template(
            'result.html',
            video_info=video_info,
            summary=summary,
            pdf_url=url_for('static', filename=f'pdfs/{filename}')
        )
        
    except Exception as e:
        return render_template('index.html', error=f"An error occurred: {str(e)}")

@app.route('/dashboard')
@login_required
def dashboard():
    summaries = Summary.query.filter_by(user_id=current_user.id).order_by(Summary.date_created.desc()).all()
    return render_template('dashboard.html', summaries=summaries)

@app.route('/download/<path:filename>')
@login_required
def download(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080,debug=True)