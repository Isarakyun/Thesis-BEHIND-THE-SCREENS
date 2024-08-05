from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

admin_bp = Blueprint('admin', __name__)

def admin_required(view):
    @login_required
    def wrapped_view(**kwargs):
        if current_user.email != 'admin':
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    wrapped_view.__name__ = view.__name__
    return wrapped_view

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('admin_dashboard.html')

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
    return render_template('admin_users.html')
