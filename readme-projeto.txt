# Sistema de Gerenciamento de Projetos de Pesquisa (SisPesq)

Sistema web para controle de projetos de pesquisa acadêmica, desenvolvido em Python usando Flask, SQLAlchemy e Bootstrap.

## Características

- Cadastro e gerenciamento de projetos de pesquisa
- Cadastro de pesquisadores e instituições
- Gerenciamento de colaboradores em projetos
- Registro de eventos e participações
- Controle de referências bibliográficas
- Geração de relatórios e estatísticas
- Importação e exportação de dados

## Tecnologias Utilizadas

- **Backend**: Python 3.8+, Flask 2.0+
- **ORM**: SQLAlchemy
- **Autenticação**: Flask-Login
- **Migração de BD**: Flask-Migrate
- **Frontend**: Bootstrap 5, Chart.js
- **Banco de Dados**: SQLite (desenvolvimento), PostgreSQL (produção)

## Normalização do Modelo de Dados

O sistema original possuía uma tabela única `projects` que foi normalizada em várias tabelas relacionais:

- `usuario`: Autenticação e acesso ao sistema
- `pesquisador`: Dados dos pesquisadores
- `instituicao`: Dados das instituições de pesquisa/ensino
- `projeto`: Informações dos projetos de pesquisa
- `evento`: Eventos acadêmicos
- `referencia`: Referências bibliográficas

Além de tabelas de relacionamento:
- `projeto_pesquisador`: Relação entre projetos e pesquisadores
- `projeto_evento`: Participações em eventos
- `projeto_referencia`: Referências utilizadas nos projetos

Esta normalização evita redundância e garante a integridade dos dados.

## Adaptações para o Contexto Brasileiro

Para adequar o sistema à cultura acadêmica brasileira, foram feitas as seguintes adaptações:

1. **Instituições**:
   - Inclusão de campo para sigla (ex: USP, UFRJ, UNICAMP)
   - Campo para UF (estados brasileiros)
   - Tipos específicos (Universidade Pública, Universidade Privada, Instituto de Pesquisa, etc.)

2. **Pesquisadores**:
   - Campo para ID Lattes (plataforma brasileira de currículos acadêmicos)
   - Campo para ORCID (identificador internacional)
   - Titulações adaptadas ao sistema brasileiro (Graduado, Especialista, Mestre, Doutor, Pós-Doutor)

3. **Eventos**:
   - Suporte à classificação Qualis (sistema brasileiro de avaliação de periódicos e eventos)

4. **Projetos**:
   - Campos adaptados para financiamentos por agências brasileiras (CAPES, CNPq, FAPESP, etc.)

## Instalação e Configuração

### Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Ambiente virtual (recomendado)

### Passos para Instalação

1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/sispesq.git
cd sispesq
```

2. Crie e ative um ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
export SECRET_KEY=chave-secreta-aqui
```

5. Inicialize o banco de dados
```bash
flask db init
flask db migrate -m "Criação inicial do banco de dados"
flask db upgrade
```

6. (Opcional) Popule o banco com dados de exemplo
```bash
flask inicializar_db
```

7. Crie um usuário administrador
```bash
flask criar_admin admin@example.com senha123 "Nome do Administrador"
```

8. Execute a aplicação
```bash
flask run
```

A aplicação estará disponível em `http://localhost:5000`

## Uso do Sistema

### Autenticação

Acesse o sistema usando o e-mail e senha registrados. Novos usuários podem se cadastrar na página inicial.

### Dashboard

O dashboard apresenta uma visão geral dos seus projetos, eventos próximos e estatísticas.

### Projetos

- **Listar Projetos**: Visualize todos os seus projetos
- **Novo Projeto**: Crie um novo projeto de pesquisa
- **Detalhes do Projeto**: Visualize e edite informações, adicione pesquisadores, eventos e referências

### Pesquisadores

- **Listar Pesquisadores**: Busque pesquisadores cadastrados no sistema
- **Perfil**: Visualize e edite seu perfil acadêmico

### Instituições

- **Listar Instituições**: Veja todas as instituições cadastradas
- **Nova Instituição**: Cadastre uma nova instituição

### Relatórios

- Visualize estatísticas sobre seus projetos
- Exporte dados em diferentes formatos

### Importação/Exportação

- Importe projetos a partir de arquivos CSV
- Exporte seus dados em formatos CSV ou JSON

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para mais detalhes.

## Contato

Para dúvidas ou sugestões, entre em contato pelo e-mail: seuemail@exemplo.com
