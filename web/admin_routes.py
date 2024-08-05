from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from .models import User, Comments, YoutubeUrl

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
    return render_template('admin_users.html', users=users)
