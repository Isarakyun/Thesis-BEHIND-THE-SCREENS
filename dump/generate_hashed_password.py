from werkzeug.security import generate_password_hash

hashed_password = generate_password_hash('1234', method='sha256', salt_length=8)
print(hashed_password)
