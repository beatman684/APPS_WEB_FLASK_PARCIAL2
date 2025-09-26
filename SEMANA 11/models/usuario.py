from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id_usuario, nombre, email, password, role):
        self.id = id_usuario
        self.nombre = nombre
        self.email = email
        self.password = password
        self.role = role
        self.authenticated = False

    def is_active(self):
        return True

    def get_id(self):
        return str(self.id)

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False
        
    def is_admin(self):
        return self.role == 'administrador'
        
    def is_vendedor(self):
        return self.role == 'vendedor'