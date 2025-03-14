# Guia Completo para Configurar e Executar o SisPesq no Windows

## 1. Preparação do Ambiente

### 1.1 Instalar o Python
1. Baixe o Python 3.11 (recomendado) do [site oficial](https://www.python.org/downloads/windows/)
2. Durante a instalação, marque a opção "Add Python to PATH"
3. Conclua a instalação

### 1.2 Verificar a Instalação
Abra o Prompt de Comando (CMD) e digite:
```
python --version
pip --version
```

## 2. Configurar o Projeto

### 2.1 Criar a Estrutura de Diretórios
Crie a seguinte estrutura de pastas:
```
C:\projetos\pesquisa-app\
  ├── app.py                 (Arquivo principal)
  ├── templates\             (Pasta para os templates HTML)
  │    ├── base.html
  │    ├── index.html
  │    ├── login.html
  │    ├── cadastro.html
  │    └── ... (outros templates)
  └── static\                (Pasta para arquivos estáticos)
       ├── css\
       ├── js\
       └── img\
```

### 2.2 Corrigir o Código do app.py
Abra o arquivo app.py e adicione as seguintes linhas no início (se não existirem):
```python
import json
import click
```

### 2.3 Configurar o Ambiente Virtual
1. Abra o CMD como administrador
2. Navegue até a pasta do projeto:
```
cd C:\projetos\pesquisa-app
```

3. Crie um ambiente virtual com Python 3.11:
```
python -m venv venv
```

4. Ative o ambiente virtual:
```
venv\Scripts\activate
```

### 2.4 Instalar as Dependências
Com o ambiente virtual ativado, instale as dependências:
```
pip install Flask==2.2.3
pip install Flask-SQLAlchemy==3.0.3
pip install SQLAlchemy==2.0.4
pip install Flask-Login==0.6.2
pip install Flask-Migrate==4.0.4
pip install Werkzeug==2.2.3
pip install click==8.1.3
pip install Jinja2==3.1.2
```

Alternativamente, você pode criar um arquivo `requirements.txt` com o conteúdo acima e instalar com:
```
pip install -r requirements.txt
```

## 3. Configuração do Banco de Dados

### 3.1 Configurar Variáveis de Ambiente
```
set FLASK_APP=app.py
set FLASK_ENV=development
set SECRET_KEY=chave-secreta-para-desenvolvimento
```

### 3.2 Inicializar o Banco de Dados
```
flask db init
flask db migrate -m "Criação inicial do banco de dados"
flask db upgrade
```

### 3.3 Carregar Dados de Exemplo (Opcional)
```
flask inicializar_db
```

### 3.4 Criar um Usuário Administrador
```
flask criar_admin admin@example.com senha123 "Administrador"
```

## 4. Executar a Aplicação

### 4.1 Usando Portas Alternativas
Para evitar conflitos com outros serviços:
```
flask run --port=8080
```

Ou diretamente usando Python:
```
python app.py
```

### 4.2 Em Caso de Erro de Permissão de Socket
Se encontrar o erro "Foi feita uma tentativa de acesso a um soquete de uma maneira que é proibida pelas permissões de acesso":

1. Tente outra porta:
```
flask run --port=8088
```

2. Execute como administrador:
   - Abra o CMD como administrador
   - Navegue até a pasta do projeto e ative o ambiente virtual
   - Execute o comando acima

3. Modifique o arquivo app.py para usar uma porta específica:
```python
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
```

## 5. Solução de Problemas Comuns

### 5.1 Problemas com Templates
Se os templates não carregarem corretamente:
1. Verifique se todos os arquivos estão na pasta `templates`
2. Certifique-se de que o arquivo `base.html` existe e está completo
3. Verifique se os templates estão estendendo `base.html` corretamente

### 5.2 Problemas com o Banco de Dados
Se houver erros relacionados ao banco de dados:
```
# Remova o banco de dados e crie novamente
del instance\projetos_pesquisa.db
flask db upgrade
flask inicializar_db
```

### 5.3 Problemas com Bibliotecas
Se houver conflitos ou erros com versões de bibliotecas:
```
# Desative o ambiente atual
deactivate
# Crie um novo ambiente
python -m venv venv_novo
# Ative o novo ambiente
venv_novo\Scripts\activate
# Instale as dependências específicas
pip install -r requirements.txt
```

### 5.4 Verificando Processos em Execução nas Portas
```
netstat -ano | findstr :5000
netstat -ano | findstr :8080
```

## 6. Criando um Atalho para Execução Rápida

Crie um arquivo `iniciar.bat` na pasta do projeto com o seguinte conteúdo:

```batch
@echo off
cd C:\projetos\pesquisa-app
call venv\Scripts\activate
set FLASK_APP=app.py
set FLASK_ENV=development
python -m flask run --port=8080
pause
```

Você pode criar um atalho para este arquivo no desktop para iniciar rapidamente a aplicação.

## 7. Acesso à Aplicação

Após iniciar o servidor, acesse a aplicação no navegador usando:
```
http://localhost:8080
```

Faça login com o usuário administrador criado anteriormente:
- E-mail: admin@example.com
- Senha: senha123

Ou crie um novo usuário pelo formulário de cadastro.
