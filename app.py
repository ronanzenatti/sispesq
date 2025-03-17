import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from sqlalchemy import func
from datetime import datetime, timedelta
import json
import click

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'desenvolvimentotemporario')
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projetos_pesquisa.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///projetos_pesquisa.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@app.context_processor
def inject_now():
    return {'now': datetime.now}

# Tabelas de Relacionamento (Associativas)
projeto_pesquisador = db.Table('projeto_pesquisador',
    db.Column('projeto_id', db.Integer, db.ForeignKey('projeto.id'), primary_key=True),
    db.Column('pesquisador_id', db.Integer, db.ForeignKey('pesquisador.id'), primary_key=True),
    db.Column('funcao', db.String(50)),
    db.Column('data_entrada', db.DateTime, default=datetime.now),
    db.Column('ativo', db.Boolean, default=True)
)

projeto_evento = db.Table('projeto_evento',
    db.Column('projeto_id', db.Integer, db.ForeignKey('projeto.id'), primary_key=True),
    db.Column('evento_id', db.Integer, db.ForeignKey('evento.id'), primary_key=True),
    db.Column('data_participacao', db.DateTime)
)

projeto_referencia = db.Table('projeto_referencia',
    db.Column('projeto_id', db.Integer, db.ForeignKey('projeto.id'), primary_key=True),
    db.Column('referencia_id', db.Integer, db.ForeignKey('referencia.id'), primary_key=True)
)

# Modelo para Usuários (Pesquisadores são usuários do sistema)
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.now)
    ultimo_acesso = db.Column(db.DateTime)
    ativo = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)  # Campo para controle de admin
    
    pesquisador = db.relationship('Pesquisador', backref='usuario', uselist=False)
    
    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)
        
    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

# Modelo para Pesquisadores (normalizado da tabela original)
class Pesquisador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    lattes_id = db.Column(db.String(20), unique=True)
    orcid = db.Column(db.String(20), unique=True)
    instituicao_id = db.Column(db.Integer, db.ForeignKey('instituicao.id'))
    departamento = db.Column(db.String(100))
    titulacao = db.Column(db.String(50))
    area_atuacao = db.Column(db.String(100))
    
    projetos = db.relationship('Projeto', secondary=projeto_pesquisador,
                               backref=db.backref('pesquisadores', lazy='dynamic'))
    
    instituicao = db.relationship('Instituicao')


# Modelo para Instituições
class Instituicao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    sigla = db.Column(db.String(20))
    tipo = db.Column(db.String(50))  # Universidade, Instituto de Pesquisa, etc.
    endereco = db.Column(db.String(200))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    cep = db.Column(db.String(10))
    pais = db.Column(db.String(50), default="Brasil")
    
    pesquisadores = db.relationship('Pesquisador', backref='instituicao_ref')


# Modelo para Projetos (normalizado da tabela original)
class Projeto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), unique=True, nullable=False)
    descricao = db.Column(db.Text)
    area_conhecimento = db.Column(db.String(100))
    data_inicio = db.Column(db.Date)
    data_fim = db.Column(db.Date)
    status = db.Column(db.String(50), default="Em andamento")  # Em andamento, Concluído, etc.
    avaliacao = db.Column(db.Float, default=0.0)
    financiamento = db.Column(db.String(100))
    valor_financiamento = db.Column(db.Float, default=0.0)
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    data_atualizacao = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    data_lembrete = db.Column(db.Date)
    
    instituicao_id = db.Column(db.Integer, db.ForeignKey('instituicao.id'))
    criador_id = db.Column(db.Integer, db.ForeignKey('pesquisador.id'))
    
    eventos = db.relationship('Evento', secondary=projeto_evento,
                              backref=db.backref('projetos', lazy='dynamic'))
    
    referencias = db.relationship('Referencia', secondary=projeto_referencia,
                                  backref=db.backref('projetos', lazy='dynamic'))
                                  
    instituicao = db.relationship('Instituicao')
    criador = db.relationship('Pesquisador', foreign_keys=[criador_id])


# Modelo para Eventos
class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(50))  # Conferência, Workshop, etc.
    descricao = db.Column(db.Text)
    local = db.Column(db.String(200))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    pais = db.Column(db.String(50))
    data_inicio = db.Column(db.Date)
    data_fim = db.Column(db.Date)
    url = db.Column(db.String(200))
    qualis = db.Column(db.String(5))  # Classificação Qualis (A1, A2, B1, etc.)


# Modelo para Referências Bibliográficas
class Referencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50))  # Artigo, Livro, etc.
    titulo = db.Column(db.String(300), nullable=False)
    autores = db.Column(db.Text)
    ano = db.Column(db.Integer)
    publicacao = db.Column(db.String(200))
    volume = db.Column(db.String(20))
    numero = db.Column(db.String(20))
    paginas = db.Column(db.String(20))
    doi = db.Column(db.String(100))
    url = db.Column(db.String(300))
    data_acesso = db.Column(db.Date)


# Configuração do login_manager
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def check_projeto_permission(projeto_id):
    """Verifica se o usuário atual tem permissão para acessar/editar o projeto."""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Administradores têm acesso total
    if current_user.is_admin:
        return True
    
    # Verifica se o usuário é o criador ou está na lista de pesquisadores
    pesquisador = current_user.pesquisador
    if projeto.criador_id == pesquisador.id:
        return True
    
    # Verificar se é um pesquisador associado ao projeto
    participacao = db.session.query(projeto_pesquisador).filter(
        projeto_pesquisador.c.projeto_id == projeto_id,
        projeto_pesquisador.c.pesquisador_id == pesquisador.id,
        projeto_pesquisador.c.ativo == True
    ).first()
    
    return participacao is not None

# Rotas
@app.route('/')
def index():
    projetos_recentes = Projeto.query.order_by(Projeto.data_atualizacao.desc()).limit(5).all()
    return render_template('index.html', projetos=projetos_recentes)

@app.route('/sobre')
def sobre():   
    return render_template('sobre.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.check_senha(senha):
            login_user(usuario)
            usuario.ultimo_acesso = datetime.now()
            db.session.commit()
            return redirect(url_for('dashboard'))
        else:
            flash('E-mail ou senha inválidos', 'danger')
    
    return render_template('login.html')


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        nome = request.form.get('nome')
        instituicao_id = request.form.get('instituicao_id')
        
        # Verificar se o e-mail já está sendo usado
        if Usuario.query.filter_by(email=email).first():
            flash('E-mail já cadastrado', 'danger')
            return redirect(url_for('cadastro'))
        
        # Criar novo usuário
        novo_usuario = Usuario(email=email)
        novo_usuario.set_senha(senha)
        db.session.add(novo_usuario)
        db.session.flush()  # Para obter o ID do usuário
        
        # Criar registro de pesquisador
        novo_pesquisador = Pesquisador(
            usuario_id=novo_usuario.id,
            nome=nome,
            instituicao_id=instituicao_id
        )

        db.session.add(novo_pesquisador)
        db.session.commit()
        
        flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('login'))
    
    instituicoes = Instituicao.query.all()
    return render_template('pesquisadores/cadastro.html', instituicoes=instituicoes)

@app.route('/pesquisador/novo', methods=['GET', 'POST'])
def novo_pesquisador():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        nome = request.form.get('nome')
        instituicao_id = request.form.get('instituicao_id')
        
        # Verificar se o e-mail já está sendo usado
        if Usuario.query.filter_by(email=email).first():
            flash('E-mail já cadastrado', 'danger')
            return redirect(url_for('cadastro'))
        
        # Criar novo usuário
        novo_usuario = Usuario(email=email)
        novo_usuario.set_senha(senha)
        db.session.add(novo_usuario)
        db.session.flush()  # Para obter o ID do usuário
        
        # Criar registro de pesquisador
        novo_pesquisador = Pesquisador(
            usuario_id=novo_usuario.id,
            nome=nome,
            instituicao_id=instituicao_id
        )

        db.session.add(novo_pesquisador)
        db.session.commit()
        
        flash('Pesquisador criado com sucesso!', 'success')
        return redirect(url_for('perfil', usuario_id=novo_usuario.id))
    
    instituicoes = Instituicao.query.all()
    return render_template('pesquisadores/novo_pesquisador.html', instituicoes=instituicoes)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    pesquisador = current_user.pesquisador
    """
    # Projetos onde o usuário é pesquisador
    projetos = Projeto.query.join(projeto_pesquisador).filter(
        projeto_pesquisador.c.pesquisador_id == pesquisador.id,
        projeto_pesquisador.c.ativo == True
    ).all()"""
    
    projetos = Projeto.query.all()
    
    # Projetos próximos da data limite

    # Data atual
    data_atual = datetime.now().date()
    # Data 30 dias à frente
    data_limite = data_atual + timedelta(days=30)

    # Projetos próximos da data limite
    projetos_proximos = Projeto.query.filter(
        #projeto_pesquisador.c.pesquisador_id == pesquisador.id,
        Projeto.data_fim != None,
        Projeto.data_fim >= data_atual,
        Projeto.data_fim <= data_limite
    ).all()
    
    # Estatísticas
    total_projetos = len(projetos)
    total_eventos = db.session.query(func.count(projeto_evento.c.evento_id)).filter(
        projeto_evento.c.projeto_id.in_([p.id for p in projetos])
    ).scalar()
    
    return render_template('dashboard.html', 
                          pesquisador=pesquisador,
                          projetos=projetos,
                          projetos_proximos=projetos_proximos,
                          total_projetos=total_projetos,
                          total_eventos=total_eventos)

@app.route('/projetos')
@login_required
def lista_projetos():
    # Filtros
    status = request.args.get('status')
    area = request.args.get('area')
    
    # Consulta base
    if current_user.is_admin:
        # Administradores veem todos os projetos
        query = Projeto.query
    else:
        # Usuários normais só veem seus próprios projetos
        pesquisador = current_user.pesquisador
        query = Projeto.query.join(projeto_pesquisador).filter(
            projeto_pesquisador.c.pesquisador_id == pesquisador.id,
            projeto_pesquisador.c.ativo == True
        )
    
    # Aplicar filtros
    if status:
        query = query.filter(Projeto.status == status)
    if area:
        query = query.filter(Projeto.area_conhecimento == area)
    
    projetos = query.order_by(Projeto.data_atualizacao.desc()).all()
    
    areas = db.session.query(Projeto.area_conhecimento).distinct().all()
    status_list = db.session.query(Projeto.status).distinct().all()
    
    return render_template('projetos/projetos.html', 
                          projetos=projetos,
                          areas=areas,
                          status_list=status_list)


@app.route('/projeto/<int:projeto_id>')
@login_required
def visualizar_projeto(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Verificar se o usuário tem acesso ao projeto
    if not current_user.is_admin and projeto.criador_id != current_user.pesquisador.id:
        participacao = db.session.query(projeto_pesquisador).filter(
            projeto_pesquisador.c.projeto_id == projeto_id,
            projeto_pesquisador.c.pesquisador_id == current_user.pesquisador.id,
            projeto_pesquisador.c.ativo == True
        ).first()
        
        if not participacao:
            flash('Você não tem acesso a este projeto', 'danger')
            return redirect(url_for('lista_projetos'))
    
    # Buscar pesquisadores com suas funções
    pesquisadores_projeto = db.session.query(
        Pesquisador, 
        projeto_pesquisador.c.funcao,
        projeto_pesquisador.c.data_entrada
    ).join(
        projeto_pesquisador, 
        Pesquisador.id == projeto_pesquisador.c.pesquisador_id
    ).filter(
        projeto_pesquisador.c.projeto_id == projeto_id,
        projeto_pesquisador.c.ativo == True
    ).all()
    
    return render_template('projetos/visualizar_projeto.html', 
                          projeto=projeto,
                          pesquisadores_projeto=pesquisadores_projeto)


@app.route('/projeto/novo', methods=['GET', 'POST'])
@login_required
def novo_projeto():
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        area_conhecimento = request.form.get('area_conhecimento')
        data_inicio = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d').date()
        data_fim = datetime.strptime(request.form.get('data_fim'), '%Y-%m-%d').date() if request.form.get('data_fim') else None
        
        pesquisador = current_user.pesquisador
        
        # Verificar se já existe projeto com o mesmo nome
        if Projeto.query.filter_by(nome=nome).first():
            flash('Já existe um projeto com este nome', 'danger')
            return redirect(url_for('novo_projeto'))
        
        novo_projeto = Projeto(
            nome=nome,
            descricao=descricao,
            area_conhecimento=area_conhecimento,
            data_inicio=data_inicio,
            data_fim=data_fim,
           # instituicao_id=pesquisador.instituicao_id,
            criador_id=pesquisador.id
        )
        
        db.session.add(novo_projeto)
        db.session.flush()
        
        # Adicionar o criador como pesquisador do projeto se for um pesquisador
        if not current_user.is_admin:
            stmt = projeto_pesquisador.insert().values(
                projeto_id=novo_projeto.id,
                pesquisador_id=pesquisador.id,
                funcao='Coordenador',
                data_entrada=datetime.now(),
                ativo=True
            )
            db.session.execute(stmt)
            
        db.session.commit()
        
        flash('Projeto criado com sucesso!', 'success')
        return redirect(url_for('visualizar_projeto', projeto_id=novo_projeto.id))
    
    return render_template('projetos/novo_projeto.html')


@app.route('/projeto/<int:projeto_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_projeto(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Verificar se o usuário tem permissão para editar
    if not check_projeto_permission(projeto_id) and not current_user.is_admin:
        flash('Você não tem permissão para editar este projeto', 'danger')
        return redirect(url_for('visualizar_projeto', projeto_id=projeto_id))
    
    if request.method == 'POST':
        projeto.nome = request.form.get('nome')
        projeto.descricao = request.form.get('descricao')
        projeto.area_conhecimento = request.form.get('area_conhecimento')
        projeto.data_inicio = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d').date()
        projeto.data_fim = datetime.strptime(request.form.get('data_fim'), '%Y-%m-%d').date() if request.form.get('data_fim') else None
        projeto.status = request.form.get('status')
        
        db.session.commit()
        
        flash('Projeto atualizado com sucesso!', 'success')
        return redirect(url_for('visualizar_projeto', projeto_id=projeto_id))
    
    return render_template('projetos/editar_projeto.html', projeto=projeto)

# Substituir a rota existente no arquivo app.py

@app.route('/projeto/<int:projeto_id>/adicionar_pesquisador', methods=['GET', 'POST'])
@login_required
def adicionar_pesquisador(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Verificar se o usuário tem permissão para adicionar pesquisadores
    if not current_user.is_admin and projeto.criador_id != current_user.pesquisador.id:
        participacao = db.session.query(projeto_pesquisador).filter(
            projeto_pesquisador.c.projeto_id == projeto_id,
            projeto_pesquisador.c.pesquisador_id == current_user.pesquisador.id,
            projeto_pesquisador.c.ativo == True
        ).first()
        
        if not participacao:
            flash('Você não tem permissão para adicionar pesquisadores a este projeto', 'danger')
            return redirect(url_for('visualizar_projeto', projeto_id=projeto_id))
    
    if request.method == 'POST':
        email_pesquisador = request.form.get('email_pesquisador')
        funcao = request.form.get('funcao')
        
        # Buscar pesquisador pelo e-mail
        usuario = Usuario.query.filter_by(email=email_pesquisador).first()
        
        if not usuario or not usuario.pesquisador:
            flash('Pesquisador não encontrado', 'danger')
            return redirect(url_for('adicionar_pesquisador', projeto_id=projeto_id))
        
        novo_pesquisador = usuario.pesquisador
        
        # Verificar se já está no projeto
        participacao_existente = db.session.query(projeto_pesquisador).filter(
            projeto_pesquisador.c.projeto_id == projeto_id,
            projeto_pesquisador.c.pesquisador_id == novo_pesquisador.id
        ).first()
        
        if participacao_existente:
            flash('Este pesquisador já participa deste projeto', 'danger')
            return redirect(url_for('adicionar_pesquisador', projeto_id=projeto_id))
        
        # Adicionar ao projeto
        stmt = projeto_pesquisador.insert().values(
            projeto_id=projeto_id,
            pesquisador_id=novo_pesquisador.id,
            funcao=funcao,
            data_entrada=datetime.now(),
            ativo=True
        )
        db.session.execute(stmt)
        db.session.commit()
        
        flash(f'Pesquisador {novo_pesquisador.nome} adicionado com sucesso!', 'success')
        return redirect(url_for('visualizar_projeto', projeto_id=projeto_id))
    
    return render_template('projetos/adicionar_pesquisador.html', projeto=projeto)

@app.route('/projeto/<int:projeto_id>/remover_pesquisador/<int:pesquisador_id>', methods=['POST'])
@login_required
def remover_pesquisador(projeto_id, pesquisador_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    pesquisador = Pesquisador.query.get_or_404(pesquisador_id)
    
    # Verificar se o usuário atual é admin ou dono do projeto
    is_owner = projeto.criador_id == current_user.pesquisador.id
    
    if not current_user.is_admin and not is_owner:
        flash('Você não tem permissão para remover pesquisadores deste projeto', 'danger')
        return redirect(url_for('visualizar_projeto', projeto_id=projeto_id))
    
    # Remover associação do pesquisador ao projeto
    stmt = projeto_pesquisador.delete().where(
        db.and_(
            projeto_pesquisador.c.projeto_id == projeto_id,
            projeto_pesquisador.c.pesquisador_id == pesquisador_id
        )
    )
    
    db.session.execute(stmt)
    db.session.commit()
    
    flash(f'Pesquisador removido do projeto com sucesso!', 'success')
    return redirect(url_for('visualizar_projeto', projeto_id=projeto_id))

@app.route('/projeto/<int:projeto_id>/atualizar_funcao/<int:pesquisador_id>', methods=['POST'])
@login_required
def atualizar_funcao_pesquisador(projeto_id, pesquisador_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Verificar se o usuário atual é admin ou dono do projeto
    is_owner = projeto.criador_id == current_user.pesquisador.id
    
    if not current_user.is_admin and not is_owner:
        flash('Você não tem permissão para alterar funções neste projeto', 'danger')
        return redirect(url_for('visualizar_projeto', projeto_id=projeto_id))
    
    nova_funcao = request.form.get('funcao')
    if not nova_funcao:
        flash('Função não especificada', 'danger')
        return redirect(url_for('visualizar_projeto', projeto_id=projeto_id))
    
    # Atualizar a função do pesquisador
    stmt = projeto_pesquisador.update().where(
        db.and_(
            projeto_pesquisador.c.projeto_id == projeto_id,
            projeto_pesquisador.c.pesquisador_id == pesquisador_id
        )
    ).values(funcao=nova_funcao)
    
    db.session.execute(stmt)
    db.session.commit()
    
    flash('Função do pesquisador atualizada com sucesso!', 'success')
    return redirect(url_for('visualizar_projeto', projeto_id=projeto_id))

@app.route('/projeto/<int:projeto_id>/adicionar_evento', methods=['GET', 'POST'])
@login_required
def adicionar_evento(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Verificar se o usuário tem acesso ao projeto
    if not current_user.is_admin and projeto.criador_id != current_user.pesquisador.id:
        participacao = db.session.query(projeto_pesquisador).filter(
            projeto_pesquisador.c.projeto_id == projeto_id,
            projeto_pesquisador.c.pesquisador_id == current_user.pesquisador.id,
            projeto_pesquisador.c.ativo == True
        ).first()
        
        if not participacao:
            flash('Você não tem permissão para adicionar eventos a este projeto', 'danger')
            return redirect(url_for('visualizar_projeto', projeto_id=projeto_id))
    
    if request.method == 'POST':
        # Verificar se é um evento existente ou novo
        evento_id = request.form.get('evento_existente')
        
        if evento_id and evento_id != '0':
            # Evento existente
            evento = Evento.query.get(evento_id)
        else:
            # Novo evento
            nome = request.form.get('nome')
            tipo = request.form.get('tipo')
            descricao = request.form.get('descricao')
            local = request.form.get('local')
            cidade = request.form.get('cidade')
            estado = request.form.get('estado')
            pais = request.form.get('pais', 'Brasil')
            url = request.form.get('url')
            qualis = request.form.get('qualis')
            
            # Processamento das datas
            data_inicio = None
            if request.form.get('data_inicio'):
                data_inicio = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d').date()
                
            data_fim = None
            if request.form.get('data_fim'):
                data_fim = datetime.strptime(request.form.get('data_fim'), '%Y-%m-%d').date()
            
            # Criar o novo evento
            evento = Evento(
                nome=nome,
                tipo=tipo,
                descricao=descricao,
                local=local,
                cidade=cidade,
                estado=estado,
                pais=pais,
                data_inicio=data_inicio,
                data_fim=data_fim,
                url=url,
                qualis=qualis
            )
            
            db.session.add(evento)
            db.session.flush()
        
        # Adicionar participação no evento
        data_participacao = None
        if request.form.get('data_participacao'):
            data_participacao = datetime.strptime(request.form.get('data_participacao'), '%Y-%m-%d')
        
        # Verificar se já existe participação neste evento
        participacao_existente = db.session.query(projeto_evento).filter(
            projeto_evento.c.projeto_id == projeto_id,
            projeto_evento.c.evento_id == evento.id
        ).first()
        
        if participacao_existente:
            flash('Este projeto já foi vinculado a este evento', 'warning')
        else:
            stmt = projeto_evento.insert().values(
                projeto_id=projeto_id,
                evento_id=evento.id,
                data_participacao=data_participacao
            )
            db.session.execute(stmt)
        
        db.session.commit()
        
        flash('Evento adicionado com sucesso!', 'success')
        return redirect(url_for('visualizar_projeto', projeto_id=projeto_id))
    
    # Lista de eventos existentes para seleção
    eventos = Evento.query.order_by(Evento.nome).all()
    
    return render_template('projetos/eventos/adicionar_evento.html', projeto=projeto, eventos=eventos)

@app.route('/evento/<int:evento_id>')
@login_required
def visualizar_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    
    # Verificar se o usuário tem alguma relação com esse evento
    projeto_relacionado = db.session.query(projeto_evento).filter(
        projeto_evento.c.evento_id == evento_id
    ).first()
    
    # Se não for admin e não houver projeto relacionado, redirecionar
    if not current_user.is_admin and not projeto_relacionado:
        flash('Você não tem permissão para visualizar este evento', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('projetos/eventos/visualizar_evento.html', evento=evento)

@app.route('/evento/<int:evento_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    
    # Verificar se o usuário tem permissão (é admin ou criador de algum projeto relacionado)
    # Buscar projetos relacionados a este evento
    projetos_ids = db.session.query(projeto_evento.c.projeto_id).filter(
        projeto_evento.c.evento_id == evento_id
    ).all()
    projetos_ids = [p[0] for p in projetos_ids]
    
    tem_permissao = False
    if current_user.is_admin:
        tem_permissao = True
    else:
        for projeto_id in projetos_ids:
            projeto = Projeto.query.get(projeto_id)
            if projeto.criador_id == current_user.pesquisador.id:
                tem_permissao = True
                break
    
    if not tem_permissao:
        flash('Você não tem permissão para editar este evento', 'danger')
        return redirect(url_for('visualizar_evento', evento_id=evento_id))
    
    if request.method == 'POST':
        evento.nome = request.form.get('nome')
        evento.tipo = request.form.get('tipo')
        evento.descricao = request.form.get('descricao')
        evento.local = request.form.get('local')
        evento.cidade = request.form.get('cidade')
        evento.estado = request.form.get('estado')
        evento.pais = request.form.get('pais', 'Brasil')
        evento.url = request.form.get('url')
        evento.qualis = request.form.get('qualis')
        
        # Processamento das datas
        if request.form.get('data_inicio'):
            evento.data_inicio = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d').date()
            
        if request.form.get('data_fim'):
            evento.data_fim = datetime.strptime(request.form.get('data_fim'), '%Y-%m-%d').date()
        else:
            evento.data_fim = None
        
        db.session.commit()
        flash('Evento atualizado com sucesso!', 'success')
        return redirect(url_for('visualizar_evento', evento_id=evento_id))
    
    return render_template('projetos/eventos/editar_evento.html', evento=evento)

@app.route('/projeto/<int:projeto_id>/remover_evento/<int:evento_id>', methods=['POST'])
@login_required
def remover_evento_projeto(projeto_id, evento_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Verificar se o usuário tem permissão (é admin ou criador do projeto)
    tem_permissao = current_user.is_admin or projeto.criador_id == current_user.pesquisador.id
    
    if not tem_permissao:
        flash('Você não tem permissão para remover eventos deste projeto', 'danger')
        return redirect(url_for('visualizar_projeto', projeto_id=projeto_id))
    
    # Remover associação do evento ao projeto
    stmt = projeto_evento.delete().where(
        db.and_(
            projeto_evento.c.projeto_id == projeto_id,
            projeto_evento.c.evento_id == evento_id
        )
    )
    
    db.session.execute(stmt)
    db.session.commit()
    
    flash('Evento removido do projeto com sucesso!', 'success')
    return redirect(url_for('visualizar_projeto', projeto_id=projeto_id))

@app.route('/projeto/<int:projeto_id>/adicionar_referencia', methods=['GET', 'POST'])
@login_required
def adicionar_referencia(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Verificar se o usuário tem acesso ao projeto
    """pesquisador = current_user.pesquisador
    participacao = db.session.query(projeto_pesquisador).filter(
        projeto_pesquisador.c.projeto_id == projeto_id,
        projeto_pesquisador.c.pesquisador_id == pesquisador.id,
        projeto_pesquisador.c.ativo == True
    ).first()
    
    if not participacao:
        flash('Você não tem permissão para adicionar referências a este projeto', 'danger')
        return redirect(url_for('visualizar_projeto', projeto_id=projeto_id))"""
    
    if request.method == 'POST':
        tipo = request.form.get('tipo')
        titulo = request.form.get('titulo')
        autores = request.form.get('autores')
        ano = request.form.get('ano')
        publicacao = request.form.get('publicacao')
        doi = request.form.get('doi')
        
        # Procurar referência existente pelo DOI ou título
        referencia = None
        if doi:
            referencia = Referencia.query.filter_by(doi=doi).first()
        
        if not referencia:
            referencia = Referencia.query.filter_by(titulo=titulo, autores=autores, ano=ano).first()
        
        if not referencia:
            # Criar nova referência
            referencia = Referencia(
                tipo=tipo,
                titulo=titulo,
                autores=autores,
                ano=ano,
                publicacao=publicacao,
                doi=doi,
                url=request.form.get('url'),
                volume=request.form.get('volume'),
                numero=request.form.get('numero'),
                paginas=request.form.get('paginas')
            )
            
            db.session.add(referencia)
            db.session.flush()
        
        # Verificar se já existe esta referência no projeto
        ref_existente = db.session.query(projeto_referencia).filter(
            projeto_referencia.c.projeto_id == projeto_id,
            projeto_referencia.c.referencia_id == referencia.id
        ).first()
        
        if not ref_existente:
            # Adicionar ao projeto
            stmt = projeto_referencia.insert().values(
                projeto_id=projeto_id,
                referencia_id=referencia.id
            )
            db.session.execute(stmt)
        
        db.session.commit()
        
        flash('Referência adicionada com sucesso!', 'success')
        return redirect(url_for('visualizar_projeto', projeto_id=projeto_id))
    
    return render_template('projetos/adicionar_referencia.html', projeto=projeto)


@app.route('/pesquisadores')
@login_required
def lista_pesquisadores():
    termo_busca = request.args.get('q', '')
    instituicao_id = request.args.get('instituicao_id')
    
    query = Pesquisador.query
    
    if termo_busca:
        query = query.filter(Pesquisador.nome.like(f'%{termo_busca}%'))
    
    if instituicao_id:
        query = query.filter(Pesquisador.instituicao_id == instituicao_id)
    
    pesquisadores = query.all()
    instituicoes = Instituicao.query.order_by(Instituicao.nome).all()
    
    return render_template('pesquisadores/pesquisadores.html', 
                          pesquisadores=pesquisadores, 
                          instituicoes=instituicoes,
                          termo_busca=termo_busca)


@app.route('/instituicoes')
@login_required
def lista_instituicoes():
    instituicoes = Instituicao.query.order_by(Instituicao.nome).all()
    return render_template('instituicoes/instituicoes.html', instituicoes=instituicoes)

@app.route('/instituicao/<int:instituicao_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_instituicao(instituicao_id):
    instituicao = Instituicao.query.get_or_404(instituicao_id)
    
    # Verificar se o usuário é admin
    if not current_user.is_admin:
        flash('Você não tem permissão para editar instituições', 'danger')
        return redirect(url_for('lista_instituicoes'))

    if request.method == 'POST':
        instituicao.nome = request.form.get('nome')
        instituicao.sigla = request.form.get('sigla')
        instituicao.tipo = request.form.get('tipo')
        instituicao.endereco = request.form.get('endereco')        
        instituicao.cidade = request.form.get('cidade')        
        instituicao.estado = request.form.get('estado')        
        instituicao.cep = request.form.get('cep')
        
        db.session.commit()
        
        flash('Instituição atualizada com sucesso!', 'success')
        return redirect(url_for('lista_instituicoes'))
    
    return render_template('instituicoes/editar_instituicao.html', instituicao=instituicao)    


@app.route('/instituicao/nova', methods=['GET', 'POST'])
@login_required
def nova_instituicao():
    if request.method == 'POST':
        nome = request.form.get('nome')
        sigla = request.form.get('sigla')
        tipo = request.form.get('tipo')
        endereco = request.form.get('endereco')
        cidade = request.form.get('cidade')
        estado = request.form.get('estado')
        cep = request.form.get('cep')
        
        # Verificar se já existe instituição com a mesma sigla
        if Instituicao.query.filter_by(sigla=sigla).first():
            flash('Já existe uma instituição com esta sigla', 'danger')
            return redirect(url_for('nova_instituicao'))
        
        nova_instituicao = Instituicao(
            nome=nome,
            sigla=sigla,
            tipo=tipo,
            endereco=endereco,
            cidade=cidade,
            estado=estado,
            cep=cep,
            pais="Brasil"
        )
        
        db.session.add(nova_instituicao)
        db.session.commit()
        
        flash('Instituição cadastrada com sucesso!', 'success')
        return redirect(url_for('lista_instituicoes'))
    
    return render_template('instituicoes/nova_instituicao.html')


@app.route('/perfil/<int:usuario_id>')
@login_required
def perfil(usuario_id):
    # Apenas o próprio usuário ou um admin pode ver o perfil
    if usuario_id != current_user.id and not current_user.is_admin:
        flash('Você não tem permissão para acessar este perfil', 'danger')
        return redirect(url_for('dashboard'))
        
    usuario = Usuario.query.get_or_404(usuario_id)
    # Total de projetos
    total_projetos = len(usuario.pesquisador.projetos)
    
    # Projetos em andamento
    projetos_em_andamento = sum(1 for p in usuario.pesquisador.projetos if p.status == 'Em andamento')
    
    # Projetos concluídos
    projetos_concluidos = sum(1 for p in usuario.pesquisador.projetos if p.status == 'Concluído')
    
    return render_template('pesquisadores/perfil.html', 
                         usuario=usuario,
                         total_projetos=total_projetos,
                         projetos_em_andamento=projetos_em_andamento,
                         projetos_concluidos=projetos_concluidos)


@app.route('/perfil/editar/<int:usuario_id>', methods=['GET', 'POST'])
@login_required
def editar_perfil(usuario_id):
    # Apenas o próprio usuário ou um admin pode editar o perfil
    if usuario_id != current_user.id and not current_user.is_admin:
        flash('Você não tem permissão para editar este perfil', 'danger')
        return redirect(url_for('dashboard'))
        
    pesquisador = Usuario.query.get_or_404(usuario_id).pesquisador
    
    if request.method == 'POST':
        pesquisador.nome = request.form.get('nome')
        pesquisador.lattes_id = request.form.get('lattes_id')
        pesquisador.orcid = request.form.get('orcid')
        pesquisador.instituicao_id = request.form.get('instituicao_id')
        pesquisador.departamento = request.form.get('departamento')
        pesquisador.titulacao = request.form.get('titulacao')
        pesquisador.area_atuacao = request.form.get('area_atuacao')
        
        db.session.commit()
        
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('perfil', usuario_id=usuario_id))
    
    instituicoes = Instituicao.query.order_by(Instituicao.nome).all()
    return render_template('pesquisadores/editar_perfil.html', 
                          usuario_id=usuario_id, 
                          pesquisador=pesquisador, 
                          instituicoes=instituicoes)


@app.route('/relatorios')
@login_required
def relatorios():
    return render_template('relatorios.html')

# Adicione esta rota ao seu arquivo app.py

@app.route('/api/buscar_pesquisador')
@login_required
def api_buscar_pesquisador():
    """
    API para buscar pesquisador por e-mail.
    Retorna um JSON com os dados do pesquisador se encontrado,
    ou um erro 404 caso contrário.
    """
    email = request.args.get('email')
    
    if not email:
        return jsonify({'erro': 'E-mail não fornecido'}), 400
    
    # Buscar o usuário pelo e-mail
    usuario = Usuario.query.filter_by(email=email).first()
    
    if not usuario or not usuario.pesquisador:
        return jsonify({'erro': 'Pesquisador não encontrado'}), 404
    
    # Obter dados do pesquisador
    pesquisador = usuario.pesquisador
    
    # Preparar resposta
    resultado = {
        'id': pesquisador.id,
        'nome': pesquisador.nome,
        'titulacao': pesquisador.titulacao,
        'area_atuacao': pesquisador.area_atuacao,
        'instituicao': pesquisador.instituicao.nome if pesquisador.instituicao else None,
        'instituicao_id': pesquisador.instituicao_id,
        'departamento': pesquisador.departamento
    }
    
    return jsonify(resultado)

@app.route('/api/projetos/estatisticas')
@login_required
def api_estatisticas_projetos():
    """
    pesquisador = current_user.pesquisador
    
    # Estatísticas dos projetos do pesquisador
    projetos_ids = db.session.query(projeto_pesquisador.c.projeto_id).filter(
        projeto_pesquisador.c.pesquisador_id == pesquisador.id,
        projeto_pesquisador.c.ativo == True
    ).all()
    
    projetos_ids = Projeto.query() """
    
    projetos_ids = [id[0] for id in Projeto.query.with_entities(Projeto.id).all()]
    
    # Total por status
    status_counts = db.session.query(
        Projeto.status, func.count(Projeto.id)
    ).filter(
        Projeto.id.in_(projetos_ids)
    ).group_by(Projeto.status).all()
    
    # Total por área de conhecimento
    area_counts = db.session.query(
        Projeto.area_conhecimento, func.count(Projeto.id)
    ).filter(
        Projeto.id.in_(projetos_ids)
    ).group_by(Projeto.area_conhecimento).all()
    
    # Projetos por ano
    ano_counts = db.session.query(
        func.strftime('%Y', Projeto.data_inicio), func.count(Projeto.id)
    ).filter(
        Projeto.id.in_(projetos_ids)
    ).group_by(func.strftime('%Y', Projeto.data_inicio)).all()
    
    return {
        'status': dict(status_counts),
        'areas': dict(area_counts),
        'anos': dict(ano_counts)
    }


@app.route('/api/projetos/buscar')
@login_required
def api_buscar_projetos():
    termo = request.args.get('termo', '')
    
    if len(termo) < 3:
        return {'projetos': []}
    
    projetos = Projeto.query.filter(
        Projeto.nome.like(f'%{termo}%')
    ).limit(10).all()
    
    resultado = []
    for p in projetos:
        resultado.append({
            'id': p.id,
            'nome': p.nome,
            'descricao': p.descricao,
            'status': p.status
        })
    
    return {'projetos': resultado}


@app.route('/importar_dados')
@login_required
def importar_dados():
    return render_template('importar_dados.html')


@app.route('/importar_dados', methods=['POST'])
@login_required
def processar_importacao():
    arquivo = request.files.get('arquivo')
    
    if not arquivo:
        flash('Nenhum arquivo enviado', 'danger')
        return redirect(url_for('importar_dados'))
    
    # Processar o arquivo (exemplo para CSV)
    if arquivo.filename.endswith('.csv'):
        try:
            conteudo = arquivo.read().decode('utf-8')
            linhas = conteudo.split('\n')
            cabecalho = linhas[0].split(',')
            
            # Verificar formato do arquivo
            campos_obrigatorios = ['nome', 'descricao', 'area_conhecimento', 'data_inicio']
            
            for campo in campos_obrigatorios:
                if campo not in cabecalho:
                    flash(f'Formato de arquivo inválido. Campo obrigatório ausente: {campo}', 'danger')
                    return redirect(url_for('importar_dados'))
            
            # Processar cada linha
            projetos_importados = 0
            for i in range(1, len(linhas)):
                if not linhas[i].strip():
                    continue
                
                dados = linhas[i].split(',')
                
                if len(dados) != len(cabecalho):
                    continue
                
                # Mapear dados para dicionário
                projeto_dados = {}
                for j, campo in enumerate(cabecalho):
                    projeto_dados[campo] = dados[j].strip()
                
                # Criar projeto
                projeto = Projeto(
                    nome=projeto_dados['nome'],
                    descricao=projeto_dados.get('descricao', ''),
                    area_conhecimento=projeto_dados.get('area_conhecimento', ''),
                    data_inicio=datetime.strptime(projeto_dados['data_inicio'], '%Y-%m-%d').date(),
                    status=projeto_dados.get('status', 'Em andamento'),
                    criador_id=current_user.pesquisador.id,
                    instituicao_id=current_user.pesquisador.instituicao_id
                )
                
                if 'data_fim' in projeto_dados and projeto_dados['data_fim']:
                    projeto.data_fim = datetime.strptime(projeto_dados['data_fim'], '%Y-%m-%d').date()
                
                db.session.add(projeto)
                db.session.flush()
                
                # Adicionar o criador como pesquisador do projeto
                stmt = projeto_pesquisador.insert().values(
                    projeto_id=projeto.id,
                    pesquisador_id=current_user.pesquisador.id,
                    funcao='Coordenador',
                    data_entrada=datetime.now(),
                    ativo=True
                )
                db.session.execute(stmt)
                
                projetos_importados += 1
            
            db.session.commit()
            flash(f'{projetos_importados} projetos importados com sucesso!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao processar arquivo: {str(e)}', 'danger')
    
    else:
        flash('Formato de arquivo não suportado. Use CSV.', 'danger')
    
    return redirect(url_for('importar_dados'))


@app.route('/exportar_dados')
@login_required
def exportar_dados():
    formato = request.args.get('formato', 'csv')
    tipo = request.args.get('tipo', 'projetos')
    
    if tipo == 'projetos':
        # Obter projetos do usuário
        pesquisador = current_user.pesquisador
        projetos_ids = db.session.query(projeto_pesquisador.c.projeto_id).filter(
            projeto_pesquisador.c.pesquisador_id == pesquisador.id,
            projeto_pesquisador.c.ativo == True
        ).all()
        
        projetos_ids = [p[0] for p in projetos_ids]
        projetos = Projeto.query.filter(Projeto.id.in_(projetos_ids)).all()
        
        if formato == 'csv':
            # Gerar CSV
            output = 'id,nome,descricao,area_conhecimento,data_inicio,data_fim,status\n'
            
            for p in projetos:
                data_inicio = p.data_inicio.strftime('%Y-%m-%d') if p.data_inicio else ''
                data_fim = p.data_fim.strftime('%Y-%m-%d') if p.data_fim else ''
                
                # Escapar campos com vírgulas
                nome = f'"{p.nome}"' if ',' in p.nome else p.nome
                descricao = f'"{p.descricao}"' if p.descricao and ',' in p.descricao else (p.descricao or '')
                
                output += f'{p.id},{nome},{descricao},{p.area_conhecimento},{data_inicio},{data_fim},{p.status}\n'
            
            response = app.response_class(
                response=output,
                status=200,
                mimetype='text/csv'
            )
            response.headers['Content-Disposition'] = 'attachment; filename=projetos.csv'
            return response
        
        elif formato == 'json':
            # Gerar JSON
            resultado = []
            for p in projetos:
                resultado.append({
                    'id': p.id,
                    'nome': p.nome,
                    'descricao': p.descricao,
                    'area_conhecimento': p.area_conhecimento,
                    'data_inicio': p.data_inicio.strftime('%Y-%m-%d') if p.data_inicio else None,
                    'data_fim': p.data_fim.strftime('%Y-%m-%d') if p.data_fim else None,
                    'status': p.status,
                    'instituicao': p.instituicao.nome if p.instituicao else None
                })
            
            response = app.response_class(
                response=json.dumps(resultado, ensure_ascii=False),
                status=200,
                mimetype='application/json'
            )
            response.headers['Content-Disposition'] = 'attachment; filename=projetos.json'
            return response
    
    flash('Tipo de exportação não suportado', 'danger')
    return redirect(url_for('dashboard'))


# Inicialização do banco de dados e criação de dados de exemplo
@app.cli.command('inicializar_db')
def inicializar_db():
    """Inicializa o banco de dados com dados de exemplo."""
    db.drop_all()
    db.create_all()
    
    # Criar instituições de exemplo
    instituicoes = [
        Instituicao(nome='Universidade de São Paulo', sigla='USP', tipo='Universidade Pública', 
                  cidade='São Paulo', estado='SP', pais='Brasil'),
        Instituicao(nome='Universidade Estadual de Campinas', sigla='UNICAMP', tipo='Universidade Pública', 
                  cidade='Campinas', estado='SP', pais='Brasil'),
        Instituicao(nome='Universidade Federal do Rio de Janeiro', sigla='UFRJ', tipo='Universidade Pública', 
                  cidade='Rio de Janeiro', estado='RJ', pais='Brasil'),
        Instituicao(nome='Universidade de Brasília', sigla='UnB', tipo='Universidade Pública', 
                  cidade='Brasília', estado='DF', pais='Brasil'),
        Instituicao(nome='Pontifícia Universidade Católica de São Paulo', sigla='PUC-SP', tipo='Universidade Privada', 
                  cidade='São Paulo', estado='SP', pais='Brasil')
    ]
    
    for inst in instituicoes:
        db.session.add(inst)
    
    db.session.commit()
    
    # Criar usuário admin
    admin = Usuario(email='admin@example.com', is_admin=True)  # Marcar como admin
    admin.set_senha('admin123')
    db.session.add(admin)
    db.session.flush()
    
    # Criar perfil de pesquisador para o admin
    pesquisador_admin = Pesquisador(
        usuario_id=admin.id,
        nome='Administrador do Sistema',
        instituicao_id=1,  # USP
        titulacao='Doutor',
        area_atuacao='Ciência da Computação'
    )
    db.session.add(pesquisador_admin)
    
    # Criar outros usuários de exemplo
    usuarios = [
        ('maria.silva@example.com', 'Maria Silva', 'senha123', 1, 'Doutora', 'Biologia Molecular'),
        ('joao.santos@example.com', 'João Santos', 'senha123', 2, 'Mestre', 'Engenharia Elétrica'),
        ('ana.oliveira@example.com', 'Ana Oliveira', 'senha123', 3, 'Doutora', 'Física Teórica'),
        ('carlos.souza@example.com', 'Carlos Souza', 'senha123', 4, 'Doutor', 'Ciências Sociais')
    ]
    
    for email, nome, senha, inst_id, titulacao, area in usuarios:
        u = Usuario(email=email)
        u.set_senha(senha)
        db.session.add(u)
        db.session.flush()
        
        p = Pesquisador(
            usuario_id=u.id,
            nome=nome,
            instituicao_id=inst_id,
            titulacao=titulacao,
            area_atuacao=area
        )
        db.session.add(p)
    
    db.session.commit()
    
    # Criar eventos de exemplo
    eventos = [
        Evento(nome='SBBD 2023 - Simpósio Brasileiro de Banco de Dados', tipo='Conferência',
             cidade='Belo Horizonte', estado='MG', pais='Brasil',
             data_inicio=datetime(2023, 9, 15).date(), data_fim=datetime(2023, 9, 18).date(),
             qualis='B1'),
        Evento(nome='SIBGRAPI 2023 - Conference on Graphics, Patterns and Images', tipo='Conferência',
             cidade='Rio de Janeiro', estado='RJ', pais='Brasil',
             data_inicio=datetime(2023, 8, 28).date(), data_fim=datetime(2023, 9, 1).date(),
             qualis='B1'),
        Evento(nome='SBC 2023 - Congresso da Sociedade Brasileira de Computação', tipo='Congresso',
             cidade='João Pessoa', estado='PB', pais='Brasil',
             data_inicio=datetime(2023, 7, 30).date(), data_fim=datetime(2023, 8, 5).date())
    ]
    
    for evento in eventos:
        db.session.add(evento)
    
    db.session.commit()
    
    # Criar projetos de exemplo
    projetos = [
        Projeto(nome='Análise de Dados Genômicos em Larga Escala',
              descricao='Desenvolvimento de ferramentas computacionais para análise de dados genômicos.',
              area_conhecimento='Bioinformática',
              data_inicio=datetime(2023, 1, 15).date(),
              data_fim=datetime(2025, 1, 14).date(),
              status='Em andamento',
              instituicao_id=1,  # USP
              criador_id=2),  # Maria Silva
        Projeto(nome='Sistemas Inteligentes para Smart Cities',
              descricao='Pesquisa sobre aplicações de IA para cidades inteligentes.',
              area_conhecimento='Inteligência Artificial',
              data_inicio=datetime(2022, 6, 1).date(),
              data_fim=datetime(2024, 5, 31).date(),
              status='Em andamento',
              instituicao_id=2,  # UNICAMP
              criador_id=3),  # João Santos
        Projeto(nome='Modelagem Quântica de Materiais Supercondutores',
              descricao='Estudo teórico e experimental de materiais supercondutores.',
              area_conhecimento='Física Quântica',
              data_inicio=datetime(2022, 3, 10).date(),
              data_fim=datetime(2023, 12, 31).date(),
              status='Concluído',
              instituicao_id=3,  # UFRJ
              criador_id=4)  # Ana Oliveira
    ]
    
    for projeto in projetos:
        db.session.add(projeto)
    
    db.session.flush()
    
    # Adicionar pesquisadores aos projetos
    participacoes = [
        (1, 2, 'Coordenador'),  # Projeto 1, Maria Silva, Coordenador
        (1, 3, 'Pesquisador'),  # Projeto 1, João Santos, Pesquisador
        (2, 3, 'Coordenador'),  # Projeto 2, João Santos, Coordenador
        (2, 4, 'Pesquisador'),  # Projeto 2, Ana Oliveira, Pesquisador
        (2, 5, 'Pesquisador'),  # Projeto 2, Carlos Souza, Pesquisador
        (3, 4, 'Coordenador'),  # Projeto 3, Ana Oliveira, Coordenador
        (3, 5, 'Pesquisador')   # Projeto 3, Carlos Souza, Pesquisador
    ]
    
    for projeto_id, pesquisador_id, funcao in participacoes:
        stmt = projeto_pesquisador.insert().values(
            projeto_id=projeto_id,
            pesquisador_id=pesquisador_id,
            funcao=funcao,
            data_entrada=datetime.now(),
            ativo=True
        )
        db.session.execute(stmt)
    
    # Adicionar eventos aos projetos
    participacoes_eventos = [
        (1, 1, datetime(2023, 9, 16)),  # Projeto 1, Evento 1
        (2, 2, datetime(2023, 8, 30)),  # Projeto 2, Evento 2
        (3, 3, datetime(2023, 8, 1))    # Projeto 3, Evento 3
    ]
    
    for projeto_id, evento_id, data in participacoes_eventos:
        stmt = projeto_evento.insert().values(
            projeto_id=projeto_id,
            evento_id=evento_id,
            data_participacao=data
        )
        db.session.execute(stmt)
    
    db.session.commit()
    
    print('Banco de dados inicializado com sucesso!')


# Comando para criar usuário admin via CLI
@app.cli.command('criar_admin')
@click.argument('email')
@click.argument('senha')
@click.argument('nome')
def criar_admin(email, senha, nome):
    """Cria um usuário administrador."""
    # Verificar se já existe
    usuario = Usuario.query.filter_by(email=email).first()
    
    if usuario:
        print(f'Usuário com e-mail {email} já existe.')
        return
    
    # Criar usuário admin
    usuario = Usuario(email=email, is_admin=True)  # Definir como admin
    usuario.set_senha(senha)
    db.session.add(usuario)
    db.session.flush()
    
    # Criar pesquisador
    pesquisador = Pesquisador(
        usuario_id=usuario.id,
        nome=nome,
        titulacao='Administrador'
    )
    db.session.add(pesquisador)
    db.session.commit()
    
    print(f'Administrador {nome} criado com sucesso!')

@app.cli.command('promover_admin')
@click.argument('email')
def promover_admin(email):
    """Promove um usuário existente a administrador."""
    usuario = Usuario.query.filter_by(email=email).first()
    
    if not usuario:
        print(f'Usuário com e-mail {email} não encontrado.')
        return
    
    usuario.is_admin = True
    db.session.commit()
    print(f'Usuário {email} promovido a administrador com sucesso!')

# Executar o aplicativo
if __name__ == '__main__':
    app.run()
