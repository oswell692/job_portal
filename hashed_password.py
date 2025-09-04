import bcrypt

password = b"Myscape@2025"

hashed = bcrypt.hashpw(password, bcrypt.gensalt())

print("Hashed password:", hashed.decode())  

