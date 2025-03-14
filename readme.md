# Sistema de Gerenciamento de Projetos de Pesquisa (SisPesq)

O SisPesq é uma aplicação web desenvolvida para facilitar o gerenciamento de projetos de pesquisa acadêmica, permitindo colaboração entre pesquisadores, documentação de eventos científicos, e gestão de referências bibliográficas.

![SisPesq Logo](https://via.placeholder.com/400x100?text=SisPesq)

## 📋 Funcionalidades

- **Gestão de Projetos**
  - Cadastro e acompanhamento de projetos de pesquisa
  - Definição de datas e prazos
  - Categorização por área de conhecimento
  - Controle de status (Em andamento, Concluído, etc.)

- **Colaboração**
  - Adicione múltiplos pesquisadores aos projetos
  - Defina funções (Coordenador, Pesquisador, Bolsista, etc.)
  - Acompanhe as contribuições de cada membro

- **Produção Acadêmica**
  - Registro de participações em eventos científicos
  - Gerenciamento de referências bibliográficas
  - Vinculação de publicações aos projetos

- **Relatórios e Estatísticas**
  - Painéis visuais com gráficos e estatísticas
  - Acompanhamento de prazos e alertas
  - Exportação de dados em formatos CSV e JSON

- **Integração com Plataformas Acadêmicas**
  - Suporte a ID Lattes e ORCID
  - Adaptado ao contexto acadêmico brasileiro

## 💻 Requisitos do Sistema

- Windows 8/10/11
- Python 3.11 ou superior
- Navegador web moderno (Chrome, Firefox, Edge)
- 100MB de espaço em disco
- Conexão com internet (para bibliotecas CDN)

## 🚀 Instalação e Execução

### Instalação

1. **Instale o Python 3.11**
   - Baixe do [site oficial](https://www.python.org/downloads/windows/)
   - Selecione "Add Python to PATH" durante a instalação

2. **Clone ou baixe este repositório**
   - Extraia os arquivos para uma pasta, por exemplo `C:\projetos\pesquisa-app`

3. **Configure o ambiente virtual**
   ```
   cd C:\projetos\pesquisa-app
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

### Execução

1. **Inicialize o banco de dados**
   ```
   set FLASK_APP=app.py
   flask db init
   flask db migrate -m "Inicialização do banco de dados"
   flask db upgrade
   flask inicializar_db
   ```

2. **Execute a aplicação**
   ```
   python app.py
   ```
   Ou use o arquivo `iniciar.bat` incluído no projeto.

3. **Acesse a aplicação**
   - Abra seu navegador e acesse `http://localhost:8080`
   - Login padrão:
     - E-mail: admin@example.com
     - Senha: admin123

## 🔧 Resolução de Problemas

- **Erro de porta em uso**: Use uma porta alternativa modificando a linha no arquivo app.py:
  ```python
  app.run(host='127.0.0.1', port=8088, debug=True)
  ```

- **Erros no banco de dados**: Remova o arquivo de banco de dados e reinicialize:
  ```
  del instance\projetos_pesquisa.db
  flask db upgrade
  flask inicializar_db
  ```

- **Problemas de permissão**: Execute o cmd como administrador ao iniciar a aplicação

## 📚 Tecnologias Utilizadas

- **Backend**: Python + Flask
- **ORM**: SQLAlchemy
- **Frontend**: Bootstrap 5 + JavaScript
- **Gráficos**: Chart.js
- **Banco de Dados**: SQLite (em desenvolvimento), PostgreSQL (em produção)

## 🤝 Contribuição

Sinta-se à vontade para contribuir com este projeto criando issues ou enviando pull requests.

## 📄 Licença

Este projeto está licenciado sob a licença MIT - consulte o arquivo LICENSE para obter detalhes.
