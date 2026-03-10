from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import enum
db = SQLAlchemy()

class Status(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class StatusProcess(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class StatusParticipant(enum.Enum):
    EVALUATOR = "evaluator"
    DECIDER = "decider"

class StatusStep(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    
class RolesModel(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    companymembers = db.relationship('CompanyMembersModel', back_populates='role')

class UserModel(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(255), nullable=False)
    lastname = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    is_Global_Admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.datetime.now(datetime.UTC))
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.now(datetime.UTC), onupdate=datetime.datetime.now(datetime.UTC), nullable=False)
    companies = db.relationship('CompanyModel', back_populates='creator')
    company_members = db.relationship('CompanyMembersModel', back_populates='member')    
    processes = db.relationship('ProcessesModel', back_populates='process_creator')
    process_participants = db.relationship('ProcessParticiModel', back_populates='participant')
    evaluations = db.relationship('EvaluationsModel', back_populates='evaluator')
    step_decisions = db.relationship('StepDecisionsModel', back_populates='decider') 
    

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class SubscriptionModel(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    max_processes = db.Column(db.Integer, nullable=False)
    max_users_per_process = db.Column(db.Integer, nullable=False)
    max_steps_per_process = db.Column(db.Integer, nullable=False)
    max_criteria_per_step = db.Column(db.Integer, nullable=False)
    max_choices_per_step = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    companies = db.relationship('CompanyModel', back_populates='subscription')
    company_subscription_history  = db.relationship('SubHistoryModel', back_populates='subscription')

class CompanyModel(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    sector = db.Column(db.String(255), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)#clés étrangère users
    creator = db.relationship('UserModel', back_populates='companies')
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)#clés étrangère subscription
    subscription = db.relationship('SubscriptionModel', back_populates='companies')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.datetime.now(datetime.UTC))
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.now(datetime.UTC), onupdate=datetime.datetime.now(datetime.UTC))
    company_subscription_history = db.relationship('SubHistoryModel', back_populates='company', cascade='all, delete-orphan')
    company_members = db.relationship('CompanyMembersModel', back_populates='company', cascade='all, delete-orphan')
    processes = db.relationship('ProcessesModel', back_populates='company', cascade='all, delete-orphan')


class SubHistoryModel(db.Model):
    __tablename__ = "company_subscription_history"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    company = db.relationship("CompanyModel", back_populates="company_subscription_history")
    subscription_id = db.Column(db.Integer, db.ForeignKey("subscriptions.id"), nullable=False)
    subscription  = db.relationship('SubscriptionModel', back_populates='company_subscription_history')
    start_date = db.Column(db.DateTime, default=datetime.datetime.now(datetime.UTC), nullable=False)
    end_date = db.Column(db.DateTime)
    price_at_time = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(Status), default=Status.ACTIVE, nullable=False)

class CompanyMembersModel(db.Model):
    __tablename__ = "company_members"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    company = db.relationship('CompanyModel', back_populates='company_members')
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    member = db.relationship('UserModel', back_populates='company_members')
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    role = db.relationship('RolesModel', back_populates='companymembers')
    is_active = db.Column(db.Boolean, default=True)
    joined_at = db.Column(db.DateTime, default=datetime.datetime.now(datetime.UTC), nullable=False)
    __table_args__ = (db.UniqueConstraint('company_id', 'user_id', name='uq_company_user'),)

class ProcessesModel(db.Model):
    __tablename__ = 'processes'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    company = db.relationship('CompanyModel', back_populates='processes')
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    objective = db.Column(db.Text)
    status = db.Column(db.Enum(StatusProcess), default=StatusProcess.DRAFT, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    process_creator = db.relationship('UserModel', back_populates='processes')
    start_date = db.Column(db.DateTime, default=datetime.datetime.now(datetime.UTC), nullable=False)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.TIMESTAMP, default=datetime.datetime.now(datetime.UTC), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.now(datetime.UTC), onupdate=datetime.datetime.now(datetime.UTC), nullable=False)
    process_participants = db.relationship('ProcessParticiModel', back_populates='process', cascade='all, delete-orphan')
    process_steps = db.relationship('ProcessStepsModel', back_populates='process', cascade='all, delete-orphan')
    process_progress = db.relationship('ProcessProgressModel', back_populates='process', cascade='all, delete-orphan', uselist=False, single_parent=True)
    
class ProcessParticiModel(db.Model):
    __tablename__ = "process_participants"
    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey("processes.id"), nullable=False)
    process = db.relationship('ProcessesModel', back_populates='process_participants')
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    participant = db.relationship('UserModel', back_populates='process_participants')
    participant_role = db.Column(db.Enum(StatusParticipant), default=StatusParticipant.EVALUATOR, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.datetime.now(datetime.UTC), nullable=False)
    __table_args__ = (db.UniqueConstraint('process_id', 'user_id', 'participant_role', name='uq_process_participant_user'),)

class ProcessStepsModel(db.Model):
    __tablename__ = "process_steps"
    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey("processes.id"), nullable=False)
    process = db.relationship('ProcessesModel', back_populates='process_steps')
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    order_index = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(StatusStep), default=StatusStep.PENDING, nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.datetime.now(datetime.UTC), nullable=False)
    end_date = db.Column(db.DateTime)
    __table_args__ = (db.UniqueConstraint('process_id', 'order_index', name='uq_process_order'),)
    process_progress = db.relationship('ProcessProgressModel', back_populates='step')
    step_criteria = db.relationship('StepCriteriaModel', back_populates='step', cascade='all, delete-orphan')
    step_decisions = db.relationship('StepDecisionsModel', back_populates='step', cascade='all, delete-orphan')
    step_choices = db.relationship('StepChoiceModel', back_populates='step', cascade='all, delete-orphan')

class ProcessProgressModel(db.Model):
    __tablename__ = "process_progress"
    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey("processes.id"), nullable=False, unique=True)
    process = db.relationship('ProcessesModel', back_populates='process_progress')
    current_step_id = db.Column(db.Integer, db.ForeignKey("process_steps.id"), nullable=False)
    step = db.relationship('ProcessStepsModel', back_populates='process_progress')

class StepCriteriaModel(db.Model):
    __tablename__ = "step_criteria"
    id = db.Column(db.Integer, primary_key=True)
    step_id = db.Column(db.Integer, db.ForeignKey("process_steps.id"), nullable=False)
    step = db.relationship('ProcessStepsModel', back_populates='step_criteria')
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    max_score = db.Column(db.Numeric(10,2), default=10, nullable=False)
    evaluations = db.relationship('EvaluationsModel', back_populates='criteria', cascade='all, delete-orphan')

class StepChoiceModel(db.Model):
    __tablename__ = "step_choices"
    id = db.Column(db.Integer, primary_key=True)
    step_id = db.Column(db.Integer, db.ForeignKey("process_steps.id"), nullable=False)
    step = db.relationship('ProcessStepsModel', back_populates='step_choices')
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    file_url = db.Column(db.Text)
    evaluations = db.relationship('EvaluationsModel', back_populates='choice', cascade='all, delete-orphan')
    step_decisions = db.relationship('StepDecisionsModel', back_populates='choice', cascade='all, delete-orphan')
    

class EvaluationsModel(db.Model):
    __tablename__ = "evaluations"
    id = db.Column(db.Integer, primary_key=True)
    evaluator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    evaluator = db.relationship('UserModel', back_populates='evaluations')
    criteria_id = db.Column(db.Integer, db.ForeignKey("step_criteria.id"), nullable=False)
    criteria = db.relationship('StepCriteriaModel', back_populates='evaluations')
    choice_id = db.Column(db.Integer, db.ForeignKey("step_choices.id"), nullable=False)
    choice = db.relationship('StepChoiceModel', back_populates='evaluations')
    score = db.Column(db.Numeric(10,2), nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=datetime.datetime.now(datetime.UTC), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.now(datetime.UTC), onupdate=datetime.datetime.now(datetime.UTC), nullable=False)
    __table_args__ = (db.UniqueConstraint('evaluator_id', 'criteria_id', 'choice_id', name='uq_eval'),)

class StepDecisionsModel(db.Model):
    __tablename__ = "step_decisions"
    id = db.Column(db.Integer, primary_key=True)
    step_id = db.Column(db.Integer, db.ForeignKey("process_steps.id"), nullable=False)
    step = db.relationship('ProcessStepsModel', back_populates='step_decisions')
    decided_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    decider = db.relationship('UserModel', back_populates='step_decisions')
    choice_id = db.Column(db.Integer, db.ForeignKey("step_choices.id"), nullable=False)
    choice = db.relationship('StepChoiceModel', back_populates='step_decisions')
    name = db.Column(db.String(255), nullable=False)
    comment = db.Column(db.Text)
    decided_at = db.Column(db.DateTime, default=datetime.datetime.now(datetime.UTC), nullable=False)
    __table_args__ = (db.UniqueConstraint('step_id', name='uq_decision_per_step'),)


