# from web import create_app
from werkzeug.security import generate_password_hash
from web import db, create_app
from web.models import Admin
from dotenv import load_dotenv
import os

load_dotenv()

def create_admin(id, username, password):
    existing_admin = Admin.query.filter_by(username=username).first()
    if existing_admin:
        print(f"Admin account with username '{username}' already exists.")
        return

    hashed_password = generate_password_hash(password, method='sha256')
    new_admin = Admin(id=id, username=username, password=hashed_password)
    db.session.add(new_admin)
    db.session.commit()
    print(f"Admin account for {username} created successfully.")

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        admin_id = 0
        admin_username = os.getenv('ADMIN_USERNAME')
        admin_password = os.getenv('ADMIN_PASSWORD')
        create_admin(admin_id, admin_username, admin_password)
    app.run(host="0.0.0.0", port=5000)
