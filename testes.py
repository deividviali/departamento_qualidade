#gera senha hash
from werkzeug.security import generate_password_hash
print(generate_password_hash("12345"))
