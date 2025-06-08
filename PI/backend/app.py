from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import jwt
import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import re

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuração
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secreta')
MONGO_URI = os.getenv('MONGO_URI')

# Configurando CORS para permitir o header Authorization na rota /perfil
CORS(app, resources={r"/perfil": {"origins": "*"}}, expose_headers='Authorization')

# Conexão com o MongoDB
client = MongoClient(MONGO_URI)
db = client[os.getenv("DB_NAME")]
usuarios_collection = db['usuarios']
receitas_collection = db['receitas']
tokens_reset_collection = db['tokens_reset']

# Middleware para verificar token JWT
def verificar_token(f):
    def decorator(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'erro': 'Token não fornecido'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            usuario_id = payload['id']
            usuario = usuarios_collection.find_one({'_id': ObjectId(usuario_id)})
            
            if not usuario:
                return jsonify({'erro': 'Usuário não encontrado'}), 401
                
            request.usuario_atual = usuario
            
        except jwt.ExpiredSignatureError:
            return jsonify({'erro': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'erro': 'Token inválido'}), 401
        except Exception as e:
            return jsonify({'erro': 'Erro na validação do token'}), 401
            
        return f(*args, **kwargs)
    
    decorator.__name__ = f.__name__
    return decorator

# Função para validar email
def validar_email(email):
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(padrao, email) is not None

# Função para validar senha
def validar_senha(senha):
    if len(senha) < 6:
        return False, "A senha deve ter pelo menos 6 caracteres"
    return True, ""

# Função para enviar email (configurar com suas credenciais)
def enviar_email_reset(email, token):
    try:
        # Configurar com suas credenciais de email
        smtp_server = "smtp.gmail.com"  # ou seu servidor SMTP
        smtp_port = 587
        remetente_email = "seu_email@gmail.com"  # Configure aqui
        remetente_senha = "sua_senha_app"  # Configure aqui
        
        mensagem = MimeMultipart()
        mensagem['From'] = remetente_email
        mensagem['To'] = email
        mensagem['Subject'] = "Redefinição de Senha - ECOmida"
        
        corpo = f"""
        Olá!
        
        Você solicitou a redefinição de sua senha no ECOmida.
        
        Use o código abaixo para redefinir sua senha:
        {token}
        
        Este código expira em 1 hora.
        
        Se você não solicitou esta redefinição, ignore este email.
        
        Atenciosamente,
        Equipe ECOmida
        """
        
        mensagem.attach(MimeText(corpo, 'plain'))
        
        servidor = smtplib.SMTP(smtp_server, smtp_port)
        servidor.starttls()
        servidor.login(remetente_email, remetente_senha)
        servidor.send_message(mensagem)
        servidor.quit()
        
        return True
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False
# =================== ROTAS DE AUTENTICAÇÃO ===================
# Rota de cadastro
@app.route('/cadastro', methods=['POST'])
def cadastrar():
    try:
        dados = request.get_json()
        nome = dados.get('nome', '').strip()
        email = dados.get('email', '').strip().lower()
        senha = dados.get('senha', '')
        confirmar = dados.get('confirmar', '')

        # Validações
        if not all([nome, email, senha, confirmar]):
            return jsonify({'erro': 'Preencha todos os campos'}), 400

        if len(nome) < 2:
            return jsonify({'erro': 'Nome deve ter pelo menos 2 caracteres'}), 400

        if not validar_email(email):
            return jsonify({'erro': 'Email inválido'}), 400

        valido, erro_senha = validar_senha(senha)
        if not valido:
            return jsonify({'erro': erro_senha}), 400
        
        if senha != confirmar:
            return jsonify({'erro': 'As senhas não coincidem'}), 400
        
        # Verificar se email já existe
        if usuarios_collection.find_one({'email': email}):
            return jsonify({'erro': 'Email já cadastrado'}), 409

        # Criar usuário
        hash_senha = generate_password_hash(senha)
        usuario = {
            'nome': nome,
            'email': email,
            'senha': hash_senha,
            'data_cadastro': datetime.datetime.utcnow(),
            'ativo': True
        }
        
        resultado = usuarios_collection.insert_one(usuario)
        
        return jsonify({
            'mensagem': 'Usuário cadastrado com sucesso!',
            'usuario_id': str(resultado.inserted_id)
        }), 201

    except Exception as e:
        return jsonify({'erro': 'Erro interno do servidor'}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        dados = request.get_json()
        email = dados.get('email', '').strip().lower()
        senha = dados.get('senha', '')

        if not all([email, senha]):
            return jsonify({'erro': 'Email e senha são obrigatórios'}), 400

        if not validar_email(email):
            return jsonify({'erro': 'Email inválido'}), 400

        usuario = usuarios_collection.find_one({'email': email, 'ativo': True})
        if not usuario or not check_password_hash(usuario['senha'], senha):
            return jsonify({'erro': 'Credenciais inválidas'}), 401

        # Gerar token JWT
        token = jwt.encode({
            'id': str(usuario['_id']),
            'email': usuario['email'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({
            'token': token,
            'usuario': {
                'id': str(usuario['_id']),
                'nome': usuario['nome'],
                'email': usuario['email']
            },
            'mensagem': 'Login realizado com sucesso!'
        }), 200

    except Exception as e:
        return jsonify({'erro': 'Erro interno do servidor'}), 500

@app.route('/esqueci-senha', methods=['POST'])
def esqueci_senha():
    try:
        dados = request.get_json()
        email = dados.get('email', '').strip().lower()

        if not email:
            return jsonify({'erro': 'Email é obrigatório'}), 400

        if not validar_email(email):
            return jsonify({'erro': 'Email inválido'}), 400

        usuario = usuarios_collection.find_one({'email': email, 'ativo': True})
        if not usuario:
            # Por segurança, sempre retorna sucesso
            return jsonify({'mensagem': 'Se o email existir, um link será enviado'}), 200

        # Gerar token de reset
        token_reset = secrets.token_urlsafe(32)
        
        # Salvar token no banco
        tokens_reset_collection.delete_many({'email': email})  # Remove tokens antigos
        tokens_reset_collection.insert_one({
            'email': email,
            'token': token_reset,
            'criado_em': datetime.datetime.utcnow(),
            'expirado': False
        })

        # Enviar email (descomente e configure para usar)
        # if enviar_email_reset(email, token_reset):
        #     return jsonify({'mensagem': 'Email de redefinição enviado'}), 200
        # else:
        #     return jsonify({'erro': 'Erro ao enviar email'}), 500

        return jsonify({
            'mensagem': 'Se o email existir, um link será enviado',
            'token_temp': token_reset  # Remover em produção
        }), 200

    except Exception as e:
        return jsonify({'erro': 'Erro interno do servidor'}), 500

@app.route('/redefinir-senha', methods=['POST'])
def redefinir_senha():
    try:
        dados = request.get_json()
        token = dados.get('token', '')
        nova_senha = dados.get('nova_senha', '')
        confirmar_senha = dados.get('confirmar_senha', '')

        if not all([token, nova_senha, confirmar_senha]):
            return jsonify({'erro': 'Todos os campos são obrigatórios'}), 400

        valido, erro_senha = validar_senha(nova_senha)
        if not valido:
            return jsonify({'erro': erro_senha}), 400

        if nova_senha != confirmar_senha:
            return jsonify({'erro': 'As senhas não coincidem'}), 400

        # Verificar token
        token_doc = tokens_reset_collection.find_one({
            'token': token,
            'expirado': False
        })

        if not token_doc:
            return jsonify({'erro': 'Token inválido ou expirado'}), 400

        # Verificar se token não expirou (1 hora)
        if datetime.datetime.utcnow() - token_doc['criado_em'] > datetime.timedelta(hours=1):
            tokens_reset_collection.update_one(
                {'_id': token_doc['_id']},
                {'$set': {'expirado': True}}
            )
            return jsonify({'erro': 'Token expirado'}), 400

        # Atualizar senha
        hash_nova_senha = generate_password_hash(nova_senha)
        usuarios_collection.update_one(
            {'email': token_doc['email']},
            {'$set': {'senha': hash_nova_senha}}
        )

        # Invalidar token
        tokens_reset_collection.update_one(
            {'_id': token_doc['_id']},
            {'$set': {'expirado': True}}
        )

        return jsonify({'mensagem': 'Senha redefinida com sucesso!'}), 200

    except Exception as e:
        return jsonify({'erro': 'Erro interno do servidor'}), 500

# =================== ROTAS DE USUÁRIO ===================

@app.route('/perfil', methods=['GET'])
@verificar_token
def obter_perfil():
    try:
        usuario = request.usuario_atual
        return jsonify({
            'usuario': {
                'id': str(usuario['_id']),
                'nome': usuario['nome'],
                'email': usuario['email'],
                'data_cadastro': usuario.get('data_cadastro')
            }
        }), 200
    except Exception as e:
        return jsonify({'erro': 'Erro interno do servidor'}), 500

@app.route('/perfil', methods=['PUT'])
@verificar_token
def atualizar_perfil():
    try:
        dados = request.get_json()
        nome = dados.get('nome', '').strip()
        
        if not nome:
            return jsonify({'erro': 'Nome é obrigatório'}), 400
            
        if len(nome) < 2:
            return jsonify({'erro': 'Nome deve ter pelo menos 2 caracteres'}), 400

        usuarios_collection.update_one(
            {'_id': request.usuario_atual['_id']},
            {'$set': {'nome': nome}}
        )

        return jsonify({'mensagem': 'Perfil atualizado com sucesso!'}), 200

    except Exception as e:
        return jsonify({'erro': 'Erro interno do servidor'}), 500

@app.route('/alterar-senha', methods=['POST'])
@verificar_token
def alterar_senha():
    try:
        dados = request.get_json()
        senha_atual = dados.get('senha_atual', '')
        nova_senha = dados.get('nova_senha', '')
        confirmar_senha = dados.get('confirmar_senha', '')

        if not all([senha_atual, nova_senha, confirmar_senha]):
            return jsonify({'erro': 'Todos os campos são obrigatórios'}), 400

        # Verificar senha atual
        if not check_password_hash(request.usuario_atual['senha'], senha_atual):
            return jsonify({'erro': 'Senha atual incorreta'}), 401

        valido, erro_senha = validar_senha(nova_senha)
        if not valido:
            return jsonify({'erro': erro_senha}), 400

        if nova_senha != confirmar_senha:
            return jsonify({'erro': 'As senhas não coincidem'}), 400

        # Atualizar senha
        hash_nova_senha = generate_password_hash(nova_senha)
        usuarios_collection.update_one(
            {'_id': request.usuario_atual['_id']},
            {'$set': {'senha': hash_nova_senha}}
        )

        return jsonify({'mensagem': 'Senha alterada com sucesso!'}), 200

    except Exception as e:
        return jsonify({'erro': 'Erro interno do servidor'}), 500

# =================== ROTAS DE RECEITAS ===================

@app.route('/receitas', methods=['GET'])
def listar_receitas():
    try:
        categoria = request.args.get('categoria')
        busca = request.args.get('busca')
        
        filtro = {}
        
        if categoria:
            filtro['categoria'] = categoria
            
        if busca:
            filtro['$or'] = [
                {'titulo': {'$regex': busca, '$options': 'i'}},
                {'ingredientes': {'$regex': busca, '$options': 'i'}},
                {'descricao': {'$regex': busca, '$options': 'i'}}
            ]

        receitas = list(receitas_collection.find(filtro).sort('titulo', 1))
        
        # Converter ObjectId para string
        for receita in receitas:
            receita['_id'] = str(receita['_id'])

        return jsonify({'receitas': receitas}), 200

    except Exception as e:
        return jsonify({'erro': 'Erro interno do servidor'}), 500

@app.route('/receitas/<receita_id>', methods=['GET'])
def obter_receita(receita_id):
    try:
        receita = receitas_collection.find_one({'_id': ObjectId(receita_id)})
        
        if not receita:
            return jsonify({'erro': 'Receita não encontrada'}), 404

        receita['_id'] = str(receita['_id'])
        return jsonify({'receita': receita}), 200

    except Exception as e:
        return jsonify({'erro': 'Erro interno do servidor'}), 500


@app.route('/receitas', methods=['POST'])
@verificar_token
def criar_receita():
    try:
        dados = request.get_json()
        
        campos_obrigatorios = ['titulo', 'ingredientes', 'modo_preparo', 'categoria']
        for campo in campos_obrigatorios:
            if not dados.get(campo):
                return jsonify({'erro': f'Campo {campo} é obrigatório'}), 400

        receita = {
            'titulo': dados['titulo'].strip(),
            'descricao': dados.get('descricao', '').strip(),
            'ingredientes': dados['ingredientes'],
            'modo_preparo': dados['modo_preparo'],
            'categoria': dados['categoria'],
            'tempo_preparo': dados.get('tempo_preparo'),
            'porcoes': dados.get('porcoes'),
            'dificuldade': dados.get('dificuldade', 'média'),
            'autor_id': str(request.usuario_atual['_id']),
            'autor_nome': request.usuario_atual['nome'],
            'data_criacao': datetime.datetime.utcnow(),
            'ativa': True
        }

        resultado = receitas_collection.insert_one(receita)
        
        return jsonify({
            'mensagem': 'Receita criada com sucesso!',
            'receita_id': str(resultado.inserted_id)
        }), 201

    except Exception as e:
        return jsonify({'erro': 'Erro interno do servidor'}), 500

# =================== ROTA DE SAÚDE ===================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200

# =================== TRATAMENTO DE ERROS ===================

@app.errorhandler(404)
def nao_encontrado(error):
    return jsonify({'erro': 'Rota não encontrada'}), 404

@app.errorhandler(405)
def metodo_nao_permitido(error):
    return jsonify({'erro': 'Método não permitido'}), 405

@app.errorhandler(500)
def erro_interno(error):
    return jsonify({'erro': 'Erro interno do servidor'}), 500

# =================== INICIALIZAÇÃO ===================

def inicializar_dados():
    """Inicializa dados básicos se necessário"""
    try:
        # Criar índices para performance
        usuarios_collection.create_index("email", unique=True)
        receitas_collection.create_index("categoria")
        receitas_collection.create_index("titulo")
        tokens_reset_collection.create_index("token")
        
        print("✅ Índices do banco de dados criados/verificados")
        
        # Adicionar receitas de exemplo se não existirem
        if receitas_collection.count_documents({}) == 0:
            receitas_exemplo = [
                {
                    'titulo': 'Panqueca de Banana com Sobras de Pão',
                    'descricao': 'Deliciosa panqueca aproveitando pães que iriam fora',
                    'ingredientes': ['2 bananas maduras', '2 fatias de pão amanhecido', '2 ovos', '1 xícara de leite', 'Canela a gosto'],
                    'modo_preparo': ['Bata todos os ingredientes no liquidificador', 'Despeje na frigideira quente', 'Cozinhe até dourar dos dois lados'],
                    'categoria': 'sobremesas',
                    'tempo_preparo': '15 minutos',
                    'porcoes': 4,
                    'dificuldade': 'fácil',
                    'autor_nome': 'Sistema',
                    'data_criacao': datetime.datetime.utcnow(),
                    'ativa': True
                },
                {
                    'titulo': 'Sopa de Legumes com Sobras',
                    'descricao': 'Sopa nutritiva usando legumes que sobrariam',
                    'ingredientes': ['Sobras de legumes cozidos', '1 litro de água', 'Sal e temperos a gosto', '1 cubo de caldo'],
                    'modo_preparo': ['Refogue os legumes', 'Adicione água e temperos', 'Cozinhe por 20 minutos'],
                    'categoria': 'carnes',
                    'tempo_preparo': '30 minutos',
                    'porcoes': 6,
                    'dificuldade': 'fácil',
                    'autor_nome': 'Sistema',
                    'data_criacao': datetime.datetime.utcnow(),
                    'ativa': True
                }
            ]
            receitas_collection.insert_many(receitas_exemplo)
            print("✅ Receitas de exemplo adicionadas")
            
    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")

if __name__ == '__main__':
    print("🚀 Iniciando servidor ECOmida...")
    inicializar_dados()
    print("✅ Servidor rodando em http://localhost:5000")
    print("📝 Rotas disponíveis:")
    print("   POST /cadastro - Cadastrar usuário")
    print("   POST /login - Fazer login")
    print("   POST /esqueci-senha - Solicitar reset de senha")
    print("   POST /redefinir-senha - Redefinir senha")
    print("   GET /perfil - Obter perfil (auth)")
    print("   PUT /perfil - Atualizar perfil (auth)")
    print("   POST /alterar-senha - Alterar senha (auth)")
    print("   GET /receitas - Listar receitas")
    print("   GET /receitas/<id> - Obter receita específica")
    print("   POST /receitas - Criar receita (auth)")
    print("   GET /health - Health check")
    app.run(debug=True, host='0.0.0.0', port=5000)