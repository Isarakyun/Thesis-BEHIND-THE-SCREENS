from werkzeug.security import generate_password_hash
from web import db, create_app
from web.models import Admin
from dotenv import load_dotenv
import os

def create_admin(email, password):
    hashed_password = generate_password_hash(password, method='sha256')
    new_admin = Admin(email=email, password=hashed_password)
    db.session.add(new_admin)
    db.session.commit()
    print(f"Admin account for {email} created successfully.")

load_dotenv()

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        admin_email = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')
        create_admin(admin_email, admin_password)