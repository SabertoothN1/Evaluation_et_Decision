import os
import flask
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import pymysql
from models import db, UserModel, RolesModel, SubscriptionModel, CompanyModel, SubHistoryModel, CompanyMembersModel, ProcessesModel, ProcessParticiModel, ProcessStepsModel, ProcessProgressModel, StepCriteriaModel, StepChoiceModel, EvaluationsModel, StepDecisionsModel

load_dotenv()
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")
MYSQL_PORT = int(os.getenv("MYSQL_PORT"))
app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:8080"}})

conn = pymysql.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    port=MYSQL_PORT
)
conn.autocommit(True)
cursor = conn.cursor()
cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
cursor.close()
conn.close()

app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['FLASK_DEBUG'] = True
app.config['SECRET_KEY'] = "987654321ArovanaProjetWebPODC123456789"

jwt = JWTManager(app)

db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)

def insertroles():
    roles = ["ADMIN_COMPANY", "MANAGER", "MEMBER"]
    for r in roles:
        exists = RolesModel.query.filter_by(name=r).first()
        if not exists:
            db.session.add(RolesModel(name=r))
    db.session.commit()
    print("roles ajoutés")

def CreateGlobaladmin():
    email = "admin@processflow.com"
    password = "Admin12345"
    admin = UserModel.query.filter_by(email=email).first()
    if not admin:
        admin = UserModel(
            firstname="Global",
            lastname="Admin",
            phone="000000000",
            email=email,
            is_Global_Admin=True
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print("Global Admin créé :", email, password)
    else:
        print("Global Admin existe déjà")

@login_manager.user_loader
def load_user(user_id):
    return UserModel.query.get(int(user_id))


@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user = UserModel.query.filter_by(email=email).first()

    if user and user.check_password(password):
        login_user(user)
        accessToken = create_access_token(identity=email)
        data = {
            "id": user.id,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "email": user.email,
            "phone": user.phone,
            "is_Global_Admin": user.is_Global_Admin
        }
        return jsonify({'accessToken': accessToken, 'message':'Connecté', 'user': data}), 200
    else:
        return jsonify({'message': 'Email ou mot de passe invalide'}), 401
    
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    print(data)
    firstname = data.get('firstname')
    lastname = data.get('lastname')
    phone = data.get('phone')
    email = data.get('email')
    password = data.get('password')

    if not firstname or not lastname or not phone or not email or not password:
        return jsonify({'message': 'Données absentes'}), 400

    if UserModel.query.filter_by(email=email).first():
        return jsonify({'message': 'Cet email existe déjà'}), 409

    new_user = UserModel(firstname=firstname, lastname=lastname, phone=phone, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    login_user(new_user)
    accessToken = create_access_token(identity=email)
    data = {
        "id": new_user.id,
        "firstname": new_user.firstname,
        "lastname": new_user.lastname,
        "email": new_user.email,
        "phone": new_user.phone,
        "is_Global_Admin": new_user.is_Global_Admin
    }
    return jsonify({'accessToken': accessToken, 'message': 'Inscription réussie', 'user': data})


@app.route('/auth/logout')
def logout():
    logout_user()
    return jsonify({'message': 'deconnecté'}), 200

def get_current_user():
    email = get_jwt_identity()
    return UserModel.query.filter_by(email=email).first()

def is_company_creator(company_id, user_id):
    company = CompanyModel.query.filter_by(id=company_id).first()
    return company and company.created_by == user_id

def is_company_member(company_id, user_id):
    return CompanyMembersModel.query.filter_by(company_id=company_id, user_id=user_id).first() is not None

def can_access_company(company_id, user_id):
    return is_company_creator(company_id, user_id) or is_company_member(company_id, user_id)

@app.route('/dash/profile')
@jwt_required()
def profile():
    current_user = get_current_user()
    data = {
        'id': current_user.id,
        'firstname': current_user.firstname,
        'lastname': current_user.lastname,
        'email': current_user.email,
        'phone': current_user.phone,
        'is_Global_Admin': current_user.is_Global_Admin
    }
    print(data)
    return jsonify({'current_user': data}), 200

@app.route("/dash/users", methods=["GET"])
@jwt_required()
def get_all_users():
    users = UserModel.query.all()
    result = []
    for u in users:
        result.append({
            "id": u.id,
            "firstname": u.firstname,
            "lastname": u.lastname,
            "phone": u.phone,
            "email": u.email,
            "created_at": str(u.created_at),
            "updated_at": str(u.updated_at)
        })
    return jsonify(result), 200

@app.route("/dash/users/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_user(id):
    current = get_current_user()
    if not current:
        return jsonify({"message": "Utilisateurs non trouvé"})
    user = UserModel.query.filter_by(id=id).first()
    if not user:
        return jsonify({"message": "Utilisatuers non trouve"}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"}), 200


@app.route("/dash/companies", methods=["GET"])
@jwt_required()
def get_my_companies():
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur non trouvé"}), 404
    companies = CompanyModel.query.filter_by(created_by=user.id).all()
    result = []
    for c in companies:
        sub = SubscriptionModel.query.filter_by(id=c.subscription_id).first()
        result.append({
            "id": c.id,
            "name": c.name,
            "sector": c.sector,
            "created_by": c.created_by,
            "subscription_id": c.subscription_id,
            "subscription_name": sub.name,
            "is_active": c.is_active,
            "created_at": str(c.created_at),
            "updated_at": str(c.updated_at)
        })
    return jsonify(result)

@app.route("/dash/companies/<int:id>", methods=["GET"])
@jwt_required()
def get_one_company(id):
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur non trouvé"}), 404
    company = CompanyModel.query.filter_by(id=id, created_by=user.id).first()
    if not company:
        return jsonify({"message": "Company non trouvé"}), 404
    data = {
        "id": company.id,
        "name": company.name,
        "sector": company.sector,
        "created_by": company.created_by,
        "subscription_id": company.subscription_id,
        "is_active": company.is_active,
        "created_at": str(company.created_at),
        "updated_at": str(company.updated_at)
    }
    return jsonify(data)

@app.route("/dash/companies/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_company(id):
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur non trouvé"}), 404
    company = CompanyModel.query.filter_by(id=id, created_by=user.id).first()
    if not company:
        return jsonify({"message": "Company non trouvé"}), 404
    db.session.delete(company)
    db.session.commit()
    return jsonify({"message": "Company Supprimé"}), 200


@app.route("/dash/companies", methods=["DELETE"])
@jwt_required()
def delete_all_my_companies():
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur non trouvé"}), 404
    CompanyModel.query.filter_by(created_by=user.id).delete()
    db.session.commit()
    return jsonify({"message": "Companies supprimées"}), 200

@app.route("/dash/companies", methods=["POST"])
@jwt_required()
def create_company():
    user = get_current_user()
    if not user:
        return jsonify({"message": "User not found"}), 404
    data = request.get_json()
    name = data.get("name")
    sector = data.get("sector")
    subscription_id = data.get("subscription_id")
    if not name or not sector or not subscription_id:
        return jsonify({"message": "Des champs sont vides!"})
    new_company = CompanyModel(
        name=name,
        sector=sector,
        subscription_id=subscription_id,
        created_by=user.id
    )
    db.session.add(new_company)
    db.session.commit()
    return jsonify({"message": "Companie créé avec succès"})

@app.route("/dash/subscriptions", methods=["GET"])
@jwt_required()
def get_all_subscriptions():
    subs = SubscriptionModel.query.all()
    result = []
    for s in subs:
        result.append({
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "price": s.price,
            "max_processes": s.max_processes,
            "max_users_per_process": s.max_users_per_process,
            "max_steps_per_process": s.max_steps_per_process,
            "max_criteria_per_step": s.max_criteria_per_step,
            "max_choices_per_step": s.max_choices_per_step
        })
    return jsonify(result), 200

@app.route("/dash/subscriptions", methods=["POST"])
@jwt_required()
def create_subscription():
    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    price = data.get("price")
    max_processes = data.get("max_processes")
    max_users_per_process = data.get("max_users_per_process")
    max_steps_per_process = data.get("max_steps_per_process")
    max_criteria_per_step = data.get("max_criteria_per_step")
    max_choices_per_step = data.get("max_choices_per_step")

    if not name or price is None:
        return jsonify({"message": "Champs vides"}), 400
    required_ints = [
        max_processes,
        max_users_per_process,
        max_steps_per_process,
        max_criteria_per_step,
        max_choices_per_step
    ]
    if any(v is None for v in required_ints):
        return jsonify({
            "message": "Champs Vides"
        }), 400
    new_sub = SubscriptionModel(
        name=name,
        description=description,
        price=float(price),
        max_processes=int(max_processes),
        max_users_per_process=int(max_users_per_process),
        max_steps_per_process=int(max_steps_per_process),
        max_criteria_per_step=int(max_criteria_per_step),
        max_choices_per_step=int(max_choices_per_step)
    )
    db.session.add(new_sub)
    db.session.commit()
    return jsonify({"message": "Abonnement créé"}), 201

@app.route("/dash/roles", methods=["GET"])
@jwt_required()
def get_all_roles():
    roles = RolesModel.query.all()
    roles_list = []
    for role in roles:
        roles_list.append({
            "id": role.id,
            "name": role.name,
            "description": role.description
        })
    return jsonify(roles_list), 200

@app.route("/dash/membre/<int:company_id>", methods=["GET"])
@jwt_required()
def get_company_members(company_id):
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur non trouve"}), 404
    company = CompanyModel.query.filter_by(id=company_id).first()
    if not company:
        return jsonify({"message": "Companie non trouvé"}), 404

    is_creator = (company.created_by == user.id)
    is_member = CompanyMembersModel.query.filter_by(company_id=company_id, user_id=user.id).first()
    if not is_creator and not is_member:
        return jsonify({"message": "Access denié"}), 403
    members = CompanyMembersModel.query.filter_by(company_id=company_id).all()
    result = []
    for m in members:
        result.append({
            "id": m.id,
            "company_id": m.company_id,
            "user_id": m.user_id,
            "role_id": m.role_id,
            "role_name": m.role.name if m.role else None,
            "is_active": m.is_active,
            "joined_at": str(m.joined_at),
            "firstname": m.member.firstname if m.member else None,
            "lastname": m.member.lastname if m.member else None,
            "email": m.member.email if m.member else None,
            "phone": m.member.phone if m.member else None
        })

    return jsonify(result), 200

@app.route("/dash/membre", methods=["POST"])
@jwt_required()
def create_membre():
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur introuvable."}), 404
    data = request.get_json()
    company_id = data.get("company_id")
    email = data.get("email")
    role_id = data.get("role_id")

    if not company_id or not email or not role_id:
        return jsonify({"message": "company_id, email et role_id sont obligatoires."}), 400

    company = CompanyModel.query.filter_by(id=company_id).first()
    if not company:
        return jsonify({"message": "Entreprise introuvable."}), 404

    if not can_access_company(company_id, user.id):
        return jsonify({"message": "Accès refusé."}), 403

    member_user = UserModel.query.filter_by(email=email).first()
    if not member_user:
        return jsonify({"message": "Aucun utilisateur avec cet email."}), 404
    
    role = RolesModel.query.filter_by(id=role_id).first()
    if not role:
        return jsonify({"message": "Rôle introuvable."}), 404
    
    existing = CompanyMembersModel.query.filter_by(company_id=company_id, user_id=member_user.id).first()
    if existing:
        return jsonify({"message": "Cet utilisateur est déjà membre de cette entreprise."}), 409
    new_member = CompanyMembersModel(
        company_id=company_id,
        user_id=member_user.id,
        role_id=role_id,
        is_active=True
    )
    db.session.add(new_member)
    db.session.commit()
    return jsonify({"message": "Membre ajouté avec succès."}), 201


@app.route("/dash/membre/<int:member_id>", methods=["DELETE"])
@jwt_required()
def delete_member(member_id):
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur non trouvé"}), 404

    member_row = CompanyMembersModel.query.filter_by(id=member_id).first()
    if not member_row:
        return jsonify({"message": "Membre non trouvé"}), 404

    company = CompanyModel.query.filter_by(id=member_row.company_id).first()
    if not company:
        return jsonify({"message": "Companie non trouvé"}), 404
    if company.created_by != user.id:
        return jsonify({"message": "Access denié"}), 403

    db.session.delete(member_row)
    db.session.commit()

    return jsonify({"message": "Membre supprimé"}), 200

@app.route("/dash/companies/<int:company_id>/processes", methods=["POST"])
@jwt_required()
def create_process(company_id):
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur introuvable."}), 404
    company = CompanyModel.query.filter_by(id=company_id).first()
    if not company:
        return jsonify({"message": "Entreprise introuvable."}), 404

    if not can_access_company(company_id, user.id):
        return jsonify({"message": "Accès refusé : vous n'appartenez pas à cette entreprise."}), 403
    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    objective = data.get("objective")
    if not name:
        return jsonify({"message": "Le champ 'name' est obligatoire."}), 400
    new_process = ProcessesModel(
        company_id=company_id,
        name=name,
        description=description,
        objective=objective,
        created_by=user.id
    )
    db.session.add(new_process)
    db.session.commit()
    return jsonify({"message": "Processus créé avec succès."}), 201

@app.route("/dash/processes/<int:process_id>", methods=["DELETE"])
@jwt_required()
def delete_process(process_id):
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur non trouvé"}), 404

    processus = ProcessesModel.query.filter_by(id=process_id).first()
    if not processus:
        return jsonify({"message": "Processus non trouvé"}), 404
    if processus.created_by != user.id:
        return jsonify({"message": "Access denié"}), 403
    db.session.delete(processus)
    db.session.commit()

    return jsonify({"message": "Processus supprimé"}), 200

@app.route("/dash/my-processes", methods=["GET"])
@jwt_required()
def get_my_processes():
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur introuvable."}), 404
    processes = ProcessesModel.query.filter_by(created_by=user.id).order_by(ProcessesModel.created_at.desc()).all()
    result = []
    for p in processes:
        result.append({
            "id": p.id,
            "company_id": p.company_id,
            "name": p.name,
            "description": p.description,
            "objective": p.objective,
            "status": p.status.value,
            "start_date": str(p.start_date),
            "end_date": str(p.end_date) if p.end_date else None,
            "created_at": str(p.created_at),
            "updated_at": str(p.updated_at)
        })
    return jsonify(result), 200

@app.route("/dash/companies/<int:company_id>/processes", methods=["GET"])
@jwt_required()
def get_company_processes(company_id):
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur introuvable."}), 404

    company = CompanyModel.query.filter_by(id=company_id).first()
    if not company:
        return jsonify({"message": "Entreprise introuvable."}), 404

    if not can_access_company(company_id, user.id):
        return jsonify({"message": "Accès refusé : vous n'appartenez pas à cette entreprise."}), 403

    processes = ProcessesModel.query.filter_by(company_id=company_id).order_by(ProcessesModel.created_at.desc()).all()
    result = []
    for p in processes:
        creator = UserModel.query.get(p.created_by)
        result.append({
            "id": p.id,
            "company_id": p.company_id,
            "name": p.name,
            "description": p.description,
            "objective": p.objective,
            "status": p.status.value,
            "created_by": p.created_by,
            "creator_email": creator.email if creator else None,
            "created_at": str(p.created_at),
            "updated_at": str(p.updated_at)
        })
    return jsonify(result), 200

@app.route("/dash/companies/<int:company_id>/members", methods=["POST"])
@jwt_required()
def add_company_member(company_id):
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur introuvable."}), 404
    company = CompanyModel.query.filter_by(id=company_id).first()
    if not company:
        return jsonify({"message": "Entreprise introuvable."}), 404
    if company.created_by != user.id:
        return jsonify({"message": "Accès refusé : seul le créateur de l'entreprise peut ajouter des membres."}), 403
    data = request.get_json()
    email = data.get("email")
    role_id = data.get("role_id")
    if not email or not role_id:
        return jsonify({"message": "Les champs 'email' et 'role_id' sont obligatoires."}), 400

    member_user = UserModel.query.filter_by(email=email).first()
    if not member_user:
        return jsonify({"message": "Aucun utilisateur trouvé avec cet email."}), 404

    role = RolesModel.query.filter_by(id=role_id).first()
    if not role:
        return jsonify({"message": "Rôle introuvable."}), 404
    if member_user.id == company.created_by:
        return jsonify({"message": "Le créateur de l'entreprise est déjà l'administrateur."}), 409
    new_member = CompanyMembersModel(
        company_id=company_id,
        user_id=member_user.id,
        role_id=role_id,
        is_active=True
    )
    try:
        db.session.add(new_member)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Cet utilisateur est déjà membre de cette entreprise."}), 409

    return jsonify({"message": "Membre ajouté avec succès."}), 201

@app.route("/dash/processes/<int:process_id>/steps", methods=["POST"])
@jwt_required()
def create_step(process_id):
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur introuvable."}), 404
    process = ProcessesModel.query.filter_by(id=process_id).first()
    if not process:
        return jsonify({"message": "Processus introuvable."}), 404
    if not can_access_company(process.company_id, user.id):
        return jsonify({"message": "Accès refusé : vous n'avez pas accès à ce processus."}), 403
    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    order_index = data.get("order_index")
    if not name or order_index is None:
        return jsonify({"message": "Les champs 'name' et 'order_index' sont obligatoires."}), 400
    existing = ProcessStepsModel.query.filter_by(process_id=process_id, order_index=order_index).first()
    if existing:
        return jsonify({"message": "Une étape avec ce numéro existe déjà dans ce processus."}), 409
    new_step = ProcessStepsModel(
        process_id=process_id,
        name=name,
        description=description,
        order_index=int(order_index)
    )
    db.session.add(new_step)
    db.session.commit()
    return jsonify({"message": "Étape créée avec succès."}), 201

@app.route("/dash/processes/<int:process_id>/steps", methods=["GET"])
@jwt_required()
def get_process_steps(process_id):
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur introuvable."}), 404
    process = ProcessesModel.query.filter_by(id=process_id).first()
    if not process:
        return jsonify({"message": "Processus introuvable."}), 404
    if not can_access_company(process.company_id, user.id):
        return jsonify({"message": "Accès refusé : vous n'avez pas accès à ce processus."}), 403
    steps = ProcessStepsModel.query.filter_by(process_id=process_id).order_by(ProcessStepsModel.order_index.asc()).all()
    result = []
    for s in steps:
        result.append({
            "id": s.id,
            "process_id": s.process_id,
            "name": s.name,
            "description": s.description,
            "order_index": s.order_index,
            "status": s.status.value,
            "start_date": str(s.start_date),
            "end_date": str(s.end_date) if s.end_date else None
        })

    return jsonify(result), 200

@app.route("/dash/steps/<int:step_id>/criteria", methods=["POST"])
@jwt_required()
def create_criteria(step_id):
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur introuvable."}), 404
    step = ProcessStepsModel.query.filter_by(id=step_id).first()
    if not step:
        return jsonify({"message": "Étape introuvable."}), 404
    process = ProcessesModel.query.filter_by(id=step.process_id).first()
    if not process:
        return jsonify({"message": "Processus introuvable."}), 404
    if not can_access_company(process.company_id, user.id):
        return jsonify({"message": "Accès refusé : vous n'avez pas accès à cette entreprise."}), 403
    
    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    max_score = data.get("max_score", 10)
    if not name:
        return jsonify({"message": "Le champ 'Nom' est obligatoire."}), 400

    new_criteria = StepCriteriaModel(
        step_id=step_id,
        name=name,
        description=description,
        max_score=max_score
    )
    db.session.add(new_criteria)
    db.session.commit()
    return jsonify({"message": "Critère ajouté avec succès."}), 201

@app.route("/dash/steps/<int:step_id>/criteria", methods=["GET"])
@jwt_required()
def get_step_criteria(step_id):
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur introuvable."}), 404
    step = ProcessStepsModel.query.filter_by(id=step_id).first()
    if not step:
        return jsonify({"message": "Étape introuvable."}), 404
    process = ProcessesModel.query.filter_by(id=step.process_id).first()
    if not process:
        return jsonify({"message": "Processus introuvable."}), 404
    if not can_access_company(process.company_id, user.id):
        return jsonify({"message": "Accès refusé."}), 403
    
    criteria = StepCriteriaModel.query.filter_by(step_id=step_id).all()
    result = []
    for c in criteria:
        result.append({
            "id": c.id,
            "step_id": c.step_id,
            "name": c.name,
            "description": c.description,
            "max_score": float(c.max_score)
        })
    return jsonify(result), 200

@app.route("/dash/steps/<int:step_id>/choices", methods=["POST"])
@jwt_required()
def create_choice(step_id):
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur introuvable."}), 404
    step = ProcessStepsModel.query.filter_by(id=step_id).first()
    if not step:
        return jsonify({"message": "Étape introuvable."}), 404
    process = ProcessesModel.query.filter_by(id=step.process_id).first()
    if not process:
        return jsonify({"message": "Processus introuvable."}), 404
    if not can_access_company(process.company_id, user.id):
        return jsonify({"message": "Accès refusé."}), 403
    
    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    file_url = data.get("file_url")
    if not name:
        return jsonify({"message": "Le champ 'name' est obligatoire."}), 400
    new_choice = StepChoiceModel(
        step_id=step_id,
        name=name,
        description=description,
        file_url=file_url
    )
    db.session.add(new_choice)
    db.session.commit()
    return jsonify({"message": "Choix ajouté avec succès."}), 201

@app.route("/dash/steps/<int:step_id>/choices", methods=["GET"])
@jwt_required()
def get_step_choices(step_id):
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur introuvable."}), 404
    step = ProcessStepsModel.query.filter_by(id=step_id).first()
    if not step:
        return jsonify({"message": "Étape introuvable."}), 404
    process = ProcessesModel.query.filter_by(id=step.process_id).first()
    if not process:
        return jsonify({"message": "Processus introuvable."}), 404
    if not can_access_company(process.company_id, user.id):
        return jsonify({"message": "Accès refusé."}), 403

    choices = StepChoiceModel.query.filter_by(step_id=step_id).all()
    result = []
    for ch in choices:
        result.append({
            "id": ch.id,
            "step_id": ch.step_id,
            "name": ch.name,
            "description": ch.description,
            "file_url": ch.file_url
        })
    return jsonify(result), 200

@app.route("/dash/evaluations", methods=["POST"])
@jwt_required()
def create_evaluation():
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur introuvable."}), 404
    data = request.get_json()
    criteria_id = data.get("criteria_id")
    choice_id = data.get("choice_id")
    score = data.get("score")
    comment = data.get("comment")
    if criteria_id is None or choice_id is None or score is None:
        return jsonify({
            "message": "Les champs 'criteria_id', 'choice_id' et 'score' sont obligatoires."
        }), 400
    criteria = StepCriteriaModel.query.filter_by(id=criteria_id).first()
    if not criteria:
        return jsonify({"message": "Critère introuvable."}), 404
    choice = StepChoiceModel.query.filter_by(id=choice_id).first()
    if not choice:
        return jsonify({"message": "Choix introuvable."}), 404
    if criteria.step_id != choice.step_id:
        return jsonify({"message": "Erreur : ce critère ne correspond pas à ce choix."}), 409
    step = ProcessStepsModel.query.filter_by(id=criteria.step_id).first()
    process = ProcessesModel.query.filter_by(id=step.process_id).first()
    if not can_access_company(process.company_id, user.id):
        return jsonify({"message": "Accès refusé : vous n'avez pas accès à ce processus."}), 403

    max_score = float(criteria.max_score)
    score_value = float(score)
    if score_value < 0 or score_value > max_score:
        return jsonify({
            "message": f"Le score doit être entre 0 et {max_score}."
        }), 400
    
    new_eval = EvaluationsModel(
        evaluator_id=user.id,
        criteria_id=criteria_id,
        choice_id=choice_id,
        score=score_value,
        comment=comment
    )
    try:
        db.session.add(new_eval)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "Vous avez déjà évalué ce critère pour ce choix."
        }), 409
    return jsonify({"message": "Évaluation enregistrée avec succès."}), 201

@app.route("/dash/steps/<int:step_id>/evaluations", methods=["GET"])
@jwt_required()
def get_step_evaluations(step_id):
    user = get_current_user()
    if not user:
        return jsonify({"message": "Utilisateur introuvable."}), 404
    step = ProcessStepsModel.query.filter_by(id=step_id).first()
    if not step:
        return jsonify({"message": "Étape introuvable."}), 404
    process = ProcessesModel.query.filter_by(id=step.process_id).first()
    if not process:
        return jsonify({"message": "Processus introuvable."}), 404
    if not can_access_company(process.company_id, user.id):
        return jsonify({"message": "Accès refusé."}), 403

    criteria_ids = [c.id for c in StepCriteriaModel.query.filter_by(step_id=step_id).all()]
    choice_ids = [ch.id for ch in StepChoiceModel.query.filter_by(step_id=step_id).all()]

    if not criteria_ids or not choice_ids:
        return jsonify([]), 200
    
    evals = EvaluationsModel.query.filter(EvaluationsModel.criteria_id.in_(criteria_ids),EvaluationsModel.choice_id.in_(choice_ids)).all()
    result = []
    for e in evals:
        result.append({
            "id": e.id,
            "evaluator_id": e.evaluator_id,
            "evaluator_email": e.evaluator.email if e.evaluator else None,
            "criteria_id": e.criteria_id,
            "criteria_name": e.criteria.name if e.criteria else None,
            "choice_id": e.choice_id,
            "choice_name": e.choice.name if e.choice else None,
            "score": float(e.score),
            "comment": e.comment,
            "created_at": str(e.created_at),
            "updated_at": str(e.updated_at)
        })
    return jsonify(result), 200


with app.app_context():
    db.create_all()
    CreateGlobaladmin()
    insertroles()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)