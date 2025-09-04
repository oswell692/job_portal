
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import bcrypt
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = 'your-secret-key'

load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,   # Check if connection is alive before using it
    "pool_recycle": 300,     # Recycle connections every 5 minutes
    "pool_size": 5,          # Keep a small pool
    "max_overflow": 10       # Allow extra connections if needed
    # your options here
}



UPLOAD_FOLDER = os.path.join('static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


db = SQLAlchemy(app)

# Job Model
class JobAdvert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    company_name = db.Column(db.Text, nullable=False)
    position = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    job_type = db.Column(db.String(100), nullable=False)
    deadline = db.Column(db.Date, nullable=False)
    intro = db.Column(db.Text, nullable=False)
    responsibilities = db.Column(db.Text, nullable=False)
    candidate_profile = db.Column(db.Text, nullable=False)
    qualifications = db.Column(db.Text, nullable=False)
    whats_on_offer = db.Column(db.Text, nullable=False)
    application_email = db.Column(db.Text, nullable=False)
    apply_link = db.Column(db.String(255), nullable=False)
    logo_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Admin Login Credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = '$2b$12$i1QWmphEUxAGLVwZD8jq2OAhFwcsUB32TxwCgjwkLBdWRH5QHfBaG'

@app.route('/')
def index():
    search_query = request.args.get('q', '')
    if search_query:
        jobs = JobAdvert.query.filter(JobAdvert.position.ilike(f"%{search_query}%"))\
            .order_by(JobAdvert.deadline.asc()).all()
    else:
        jobs = JobAdvert.query.order_by(JobAdvert.deadline.asc()).all()
    return render_template('index.html', jobs=jobs, search_query=search_query)

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    job = JobAdvert.query.get_or_404(job_id)
    source = request.args.get('source', 'public')  # Default fallback
    return render_template('job_detail.html', job=job, source=source)


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password').encode('utf-8')  # Convert to bytes

        # Hashed password from your config (must be bytes too)
        stored_hash = ADMIN_PASSWORD.encode('utf-8')

        if username == ADMIN_USERNAME and bcrypt.checkpw(password, stored_hash):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('admin_login.html')
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

@app.route('/post-job')
def post_job():
    return render_template('post_job.html')

@app.route('/contact-us')
def contact_us():
    return render_template('contact_us.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    jobs = JobAdvert.query.order_by(JobAdvert.created_at.desc()).all()
    return render_template('admin_dashboard.html', jobs=jobs)

@app.route('/admin/add', methods=['GET', 'POST'])
def add_job():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        try:
            logo = request.files.get("logo")
            if logo and logo.filename != '':
                filename = secure_filename(logo.filename)
                logo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                logo_url = f"uploads/{filename}"
            else:
                logo_url = "uploads/default.png"

            job = JobAdvert(
                title=request.form['title'],
                company_name=request.form['company_name'],
                position=request.form['position'],
                location=request.form['location'],
                job_type=request.form['job_type'],
                deadline=datetime.strptime(request.form['deadline'], '%Y-%m-%d'),
                intro=request.form['intro'],
                responsibilities=request.form['responsibilities'],
                candidate_profile=request.form['candidate_profile'],
                qualifications=request.form['qualifications'],
                whats_on_offer=request.form['whats_on_offer'],
                application_email=request.form['application_email'],
                apply_link=request.form['apply_link'],
                logo_url=logo_url
            )
            db.session.add(job)
            db.session.commit()
            flash('Job advert added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            flash(f'Error adding job: {str(e)}', 'danger')
    return render_template('add_job.html', edit=False, job=None)

@app.route('/admin/edit/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    job = JobAdvert.query.get_or_404(job_id)
    if request.method == 'POST':
        job.title = request.form['title']
        job.company_name = request.form['company_name']
        job.position = request.form['position']
        job.location = request.form['location']
        job.job_type = request.form['job_type']
        job.deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%d')
        job.intro = request.form['intro']
        job.responsibilities = request.form['responsibilities']
        job.candidate_profile = request.form['candidate_profile']
        job.qualifications = request.form['qualifications']
        job.whats_on_offer = request.form['whats_on_offer']
        job.application_email = request.form['application_email']
        job.apply_link = request.form['apply_link']

        logo = request.files.get("logo")
        if logo and logo.filename != '':
            filename = secure_filename(logo.filename)
            logo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            job.logo_url = f"uploads/{filename}"
        db.session.commit()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('add_job.html', job=job, edit=True)

@app.route('/admin/delete/<int:job_id>')
def delete_job(job_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    job = JobAdvert.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    with app.app_context():   
        db.create_all()
    app.run(debug=True)
