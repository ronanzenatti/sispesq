from app import db, Usuario
from werkzeug.security import generate_password_hash

# Buscar o usuário administrador
admin = Usuario.query.filter_by(email='admin@example.com').first()

if admin:
    # Definir uma nova senha
    admin.senha_hash = generate_password_hash('senha123')
    db.session.commit()
    print("Senha do administrador alterada com sucesso para 'nova_senha123'")
else:
    print("Usuário administrador não encontrado")