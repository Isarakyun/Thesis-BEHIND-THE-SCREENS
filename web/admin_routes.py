from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user, logout_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from .models import User, Comments, YoutubeUrl, AdminLog, UserLog, Admin, SentimentCounter, FrequentWords, SummarizedComments, WordCloudImage
from . import db
import re

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
    if current_user.is_authenticated:
        admin_id = current_user.id
        audit_trail = AdminLog(admin_id=admin_id, action=action)
        db.session.add(audit_trail)
        db.session.commit()

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    user_count = User.query.count()
    comment_count = Comments.query.count()
    url_count = YoutubeUrl.query.count()

    users = User.query.order_by(User.created_at.desc()).limit(3).all()
    audit_trails = UserLog.query.order_by(UserLog.timestamp.desc()).limit(5).all()
    analysis_history = YoutubeUrl.query.order_by(YoutubeUrl.created_at.desc()).limit(5).all()
    
    return render_template('admin_dashboard.html', user_count=user_count, comment_count=comment_count, url_count=url_count, users=users, audit_trails=audit_trails, analysis_history=analysis_history)

@admin_bp.route('/user-logs')
@admin_required
def user_audit():
    audits = UserLog.query.order_by(UserLog.timestamp.desc()).all()
    audit_trails = []
    for audit in audits:
        user = User.query.get(audit.user_id)
        audit_trails.append({
            'user_id': audit.user_id,
            'username': user.username,
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
        user = User.query.get(analysis.user_id)
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
    users = User.query.all()
    users_dict = [user.to_dict() for user in users]
    return render_template('admin_users.html', users=users_dict)

# @admin_bp.route('/add-user', methods=['POST'])
# @admin_required
# def add_user():
#     username = request.form.get('username')
#     email = request.form.get('email')
#     password = request.form.get('password')
#     profile_pic = request.form.get('profile_pic')
#     confirmed_email = bool(int(request.form.get('confirmed_email')))

#     existing_user = User.query.filter_by(email=email).first()
#     if existing_user:
#         flash('Email address already exists.', 'error')
#         return redirect(url_for('admin.users'))

#     new_user = User(
#         username=username,
#         email=email,
#         password=generate_password_hash(password, method='sha256'),
#         profile_pic=profile_pic,
#         confirmed_email=confirmed_email
#     )
#     db.session.add(new_user)
#     db.session.commit()
#     log_audit_trail(f"Admin added {username}'s account")
#     flash('User added successfully!', 'success')
#     return redirect(url_for('admin.users'))

@admin_bp.route('/edit-user', methods=['POST'])
@admin_required
def edit_user():
    user_id = request.form.get('id')
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')  # Optional field for password

    existing_email = User.query.filter_by(email=email).first()
    existing_username = User.query.filter_by(username=username).first()

    user = User.query.get(user_id)

    if existing_email and existing_email.id != user.id:
        flash('Email address already exists.', 'error')
    elif existing_username and existing_username.id != user.id:
        flash('Username already exists.', 'error')
    elif not re.match(valid_email, email):
        flash('Invalid email address.', 'error')
    elif not user:
        flash('User not found.', 'error')
    else:
        user.username = username
        user.email = email
        if password:
            if not re.match(valid_password, password):
                flash('Password must be at least 8 characters long and contain alphanumeric characters.', category='error')
            else:
                user.password = generate_password_hash(password, method='sha256')
        db.session.commit()
        log_audit_trail(f"Edited user {username}")
        flash(f'User:{username} updated successfully!', 'success')

    return redirect(url_for('admin.users'))

@admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    # user_id = request.json.get('id')
    user_id = request.form.get('id')
    email = request.form.get('email')

    user = User.query.get(user_id)
    try:
        print(f"Received request to delete user with ID: {user_id}")
        if user:
            # send mail user's email to inform them that their account has been deleted by the admin
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
            db.session.query(WordCloudImage).filter_by(user_id=user_id).delete()
            db.session.query(SummarizedComments).filter_by(user_id=user_id).delete()
            db.session.query(SentimentCounter).filter_by(user_id=user_id).delete()
            db.session.query(FrequentWords).filter_by(user_id=user_id).delete()
            db.session.query(Comments).filter_by(user_id=user_id).delete()
            db.session.query(YoutubeUrl).filter_by(user_id=user_id).delete()
            db.session.delete(user)
            log_audit_trail(f"Deleted user {user.username}")
            db.session.commit()
            flash('User deleted successfully!', 'success')
            return jsonify({'message': 'User deleted successfully'}), 200
        else:
            flash('User not found.', 'error')
    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify({'error': str(e)}), 500

    # return redirect(url_for('admin.users'))

@admin_bp.route('/logout')
@admin_required
def admin_logout():
    log_audit_trail("Logged out")  # Simplify the logout action message
    logout_user()
    flash('Admin logged out successfully!', 'success')
    return redirect(url_for('auth.login'))
