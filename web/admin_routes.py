from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from .models import User, Comments, YoutubeUrl
from . import db

admin_bp = Blueprint('admin', __name__)

def admin_required(view):
    @login_required
    def wrapped_view(**kwargs):
        if not current_user.is_authenticated or current_user.email != 'admin':
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    wrapped_view.__name__ = view.__name__
    return wrapped_view

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    user_count = User.query.count()
    comment_count = Comments.query.count()
    url_count = YoutubeUrl.query.count()
    
    return render_template('admin_dashboard.html', user_count=user_count, comment_count=comment_count, url_count=url_count)

@admin_bp.route('/audit-trail')
@admin_required
def audit_trail():
    return render_template('admin_audit_trail.html')

@admin_bp.route('/summary-history')
@admin_required
def summary_history():
    return render_template('admin_summary_history.html')

@admin_bp.route('/users')
@admin_required
def users():
    users = User.query.all()
    users_dict = [user.to_dict() for user in users]  # Convert User objects to dictionaries
    return render_template('admin_users.html', users=users_dict)

@admin_bp.route('/add-user', methods=['POST'])
@admin_required
def add_user():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    profile_pic = request.form.get('profile_pic')
    confirmed_email = bool(int(request.form.get('confirmed_email')))

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('Email address already exists.', 'error')
        return redirect(url_for('admin.users'))

    new_user = User(
        username=username,
        email=email,
        password=generate_password_hash(password, method='sha256'),
        profile_pic=profile_pic,
        confirmed_email=confirmed_email
    )
    db.session.add(new_user)
    db.session.commit()
    flash('User added successfully!', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/edit-user', methods=['POST'])
@admin_required
def edit_user():
    user_id = request.form.get('id')
    username = request.form.get('username')
    email = request.form.get('email')
    profile_pic = request.form.get('profile_pic')
    confirmed_email = bool(int(request.form.get('confirmed_email')))
    password = request.form.get('password')  # Optional field for password

    user = User.query.get(user_id)
    if user:
        user.username = username
        user.email = email
        user.profile_pic = profile_pic
        user.confirmed_email = confirmed_email
        if password:
            user.password = generate_password_hash(password, method='sha256')

        db.session.commit()
        flash('User updated successfully!', 'success')
    else:
        flash('User not found.', 'error')

    return redirect(url_for('admin.users'))

@admin_bp.route('/delete-user', methods=['POST'])
@admin_required
def delete_user():
    user_id = request.json.get('id')

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    else:
        flash('User not found.', 'error')

    return jsonify(success=True)
