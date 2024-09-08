from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user, logout_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from .models import Users, Comments, YoutubeUrl, AdminLog, UserLog, Admin, SentimentCounter, FrequentWords, WordCloudImage, GetUrl, HighScoreComments
# fron .models import SummarizedComments
from datetime import datetime, timedelta
from . import db
import re
import os

admin_bp = Blueprint('admin', __name__)

mail = Mail()
valid_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,7}$'
valid_password = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$'

def admin_required(view):
    @login_required
    def wrapped_view(**kwargs):
        if not current_user.is_authenticated or current_user.username != 'admin':
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    wrapped_view.__name__ = view.__name__
    return wrapped_view

# Audit Trail Logger
def log_audit_trail(action):
    if current_user.is_authenticated and current_user.username == 'admin':
        admin_id = current_user.id
        timestamp = datetime.now()
        audit_trail = AdminLog(admin_id=admin_id, action=action, timestamp=timestamp)
        db.session.add(audit_trail)
        db.session.commit()

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    user_count = Users.query.count()
    comment_count = Comments.query.count()
    url_count = YoutubeUrl.query.count()

    users = Users.query.order_by(Users.created_at.desc()).limit(3).all()
    audit_trails = UserLog.query.order_by(UserLog.timestamp.desc()).limit(5).all()
    analysis_history = YoutubeUrl.query.order_by(YoutubeUrl.created_at.desc()).limit(5).all()
    
    return render_template('admin_dashboard.html', user_count=user_count, comment_count=comment_count, url_count=url_count, users=users, audit_trails=audit_trails, analysis_history=analysis_history)

@admin_bp.route('/user-logs')
@admin_required
def user_audit():
    audits = UserLog.query.order_by(UserLog.timestamp.desc()).all()
    audit_trails = []
    for audit in audits:
        # user = User.query.get(audit.user_id)
        audit_trails.append({
            'user_id': audit.user_id,
            'users': audit.users,
            'action': audit.action,
            'timestamp': audit.timestamp
        })
    return render_template('admin_logs_user.html', audit_trails=audit_trails)

@admin_bp.route('/admin-logs')
@admin_required
def admin_audit():
    audits = AdminLog.query.order_by(AdminLog.timestamp.desc()).all()
    audit_trails = []
    for audit in audits:
        admin = Admin.query.get(audit.admin_id)
        audit_trails.append({
            'admin_id': audit.admin_id,
            'username': admin.username,
            'action': audit.action,
            'timestamp': audit.timestamp
        })
    return render_template('admin_logs_admin.html', audit_trails=audit_trails)

@admin_bp.route('/all-analyses')
@admin_required
def summary_history():
    analyses = db.session.query(YoutubeUrl).order_by(YoutubeUrl.created_at.desc()).all()
    analysis_details = []
    for analysis in analyses:
        video = YoutubeUrl.query.get(analysis.id)
        user = Users.query.get(analysis.user_id)
        analysis_details.append({
            'created_at': video.created_at,
            'video_url': video.url,
            'video_name': video.video_name,
            'username': user.username
        })
    return render_template('admin_summary_history.html', summaries=analysis_details)

@admin_bp.route('/users')
@admin_required
def users():
    users = Users.query.all()
    users_dict = [user.to_dict() for user in users]
    return render_template('admin_users.html', users=users_dict)

@admin_bp.route('/user-requests')
@admin_required
def user_requests():
    requests = db.session.query(GetUrl).order_by(GetUrl.created_at.desc()).all()
    request_details = []
    for request in requests:
        user = Users.query.get(request.user_id)
        request_details.append({
            'created_at': request.created_at,
            'url': request.url,
            'username': user.username,
            'attempt': request.attempt
        })
    return render_template('admin_user_requests.html', requests=request_details)

@admin_bp.route('/edit-user', methods=['POST'])
@admin_required
def edit_user():
    user_id = request.form.get('id')
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')  # Optional field for password

    old_username = Users.query.get(user_id).username
    old_email = Users.query.get(user_id).email

    existing_email = Users.query.filter_by(email=email).first()
    existing_username = Users.query.filter_by(username=username).first()

    user = Users.query.get(user_id)

    if existing_email and existing_email.id != user.id:
        flash('Email address already exists.', 'error')
    elif existing_username and existing_username.id != user.id:
        flash('Username already exists.', 'error')
    elif username == 'admin':
        flash('Username cannot be "admin".', 'error')
    elif not re.match(valid_email, email):
        flash('Invalid email address.', 'error')
    elif not user:
        flash('User not found.', 'error')
    else:
        if username != old_username:
            user.username = username
            log_audit_trail(f"Edited USERNAME of ID: {user_id} | From: '{old_username}' To: '{username}'")
    
        if email != old_email:
            user.email = email
            log_audit_trail(f"Edited EMAIL of ID: {user_id} | User: {username}")

        if password:
            if not re.match(valid_password, password):
                flash('Password must be at least 8 characters long and contain alphanumeric characters.', category='error')
            else:
                user.password = generate_password_hash(password, method='sha256')
                log_audit_trail(f"Edited PASSWORD of ID: {user_id} | User: {username}")
        db.session.commit()
        flash(f'User: {username} updated successfully!', 'success')

    return redirect(url_for('admin.users'))

@admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    email = request.form.get('email')

    # getting the id from the user_id sent from the form since user_id is not in User, it should be id
    id = user_id 

    if not email:
        return jsonify({'error': 'Email is missing or invalid'}), 400

    user = Users.query.get(id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        print(f"Received request to delete user with ID: {user_id}")
        if user:
            # Send an email to the user informing them of the deletion
            msg = Message('Force Account Deletion', sender='behindthescreens.thesis@gmail.com', recipients=[email])
            msg.html = """
                <html>
                <head>
                    <style>
                        .email-content {{
                            margin: 20px;
                            padding: 20px;
                            background-color: #e5e7eb;
                        }}
                        .email-header {{
                            font-size: 24px;
                            line-height: 32px;
                            font-weight: 600;
                            color: #881337;
                            text-align: center;
                        }}
                        .email-body {{
                            font-weight: 500;
                            font-size: 18px;
                            line-height: 28px;
                            margin-top: 8px;
                            color: #4b5563;
                        }}
                        .email-footer {{
                            margin-top: 8px;
                            font-size: 14px;
                            line-height: 20px;
                            color: #fb7185;
                        }}
                        .text-center {{
                            text-align: center;
                        }}
                    </style>
                </head>
                <body>
                    <div class="email-outline">
                        <div class="text-center">
                            <div class="text-center">
                            <img src="https://pbs.twimg.com/media/GSYY7T8XsAALUY1?format=png&name=small" height="25%" viewBox="0 0 524.67004 531.39694">
                            </div>
                            <div class="email-header">Your Account Has Been Deleted</div>
                            <div class="email-body">
                                Thank you for using our platform. We have deleted your account. It's either that this action was requested or there are suspicious actions detected from your account. It is also possible that you didn't verify your account for too long that the admins had to delete your account. <br> A reminder that you can always sign up again. <br>
                                Behind the Screens is a platform that allows you to analyze the sentiment of YouTube comments.
                            </div>
                            <div class="email-footer">
                                Once your account has been deleted, you can no longer retrieve it. This email is automated, please do not reply.
                            </div>
                        </div>
                    </div>
                </body>
                </html>
            """.format()
            mail.send(msg)

            log_audit_trail(f"Deleted User ID: {user.id} | User: {user.username}")

            # Delete related records
            db.session.query(WordCloudImage).filter_by(user_id=user_id).delete()
            # db.session.query(SummarizedComments).filter_by(user_id=user_id).delete()
            db.session.query(HighScoreComments).filter_by(user_id=user_id).delete()
            db.session.query(SentimentCounter).filter_by(user_id=user_id).delete()
            db.session.query(FrequentWords).filter_by(user_id=user_id).delete()
            db.session.query(Comments).filter_by(user_id=user_id).delete()
            db.session.query(YoutubeUrl).filter_by(user_id=user_id).delete()
            db.session.query(GetUrl).filter_by(user_id=user_id).delete()

            # Delete images from the web/static/wordcloud directory
            wordcloud_dir = os.path.join('web', 'static', 'wordcloud')
            for filename in os.listdir(wordcloud_dir):
                if filename.startswith(f"{user_id}_"):
                    file_path = os.path.join(wordcloud_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)

            # Finally, delete the user
            db.session.delete(user)
            db.session.commit()

            flash('User deleted successfully!', 'success')
            return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting user: {e}")
        return jsonify({'error': str(e)}), 500

    # return redirect(url_for('admin.users'))

@admin_bp.route('/delete-user-logs', methods=['POST'])
@admin_required
def delete_user_logs():
    thirty_days_ago = datetime.now() - timedelta(days=30)
    db.session.query(UserLog).filter(UserLog.timestamp < thirty_days_ago).delete()
    db.session.commit()
    flash('User logs deleted successfully!', 'success')
    return redirect(url_for('admin.user_audit'))

@admin_bp.route('/delete-admin-logs', methods=['POST'])
@admin_required
def delete_admin_logs():
    thirty_days_ago = datetime.now() - timedelta(days=30)
    db.session.query(AdminLog).filter(AdminLog.timestamp < thirty_days_ago).delete()
    db.session.commit()
    flash('Admin logs deleted successfully!', 'success')
    return redirect(url_for('admin.admin_audit'))

@admin_bp.route('/logout')
@admin_required
def admin_logout():
    log_audit_trail("Logged out")  # Simplify the logout action message
    logout_user()
    flash('Admin logged out successfully!', 'success')
    return redirect(url_for('auth.login'))
