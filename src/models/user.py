from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # student, staff, admin
    full_name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=True)  # Only for students
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)  # For staff
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    tickets_created = db.relationship('Ticket', foreign_keys='Ticket.student_id', backref='student', lazy='dynamic')
    tickets_assigned = db.relationship('Ticket', foreign_keys='Ticket.assigned_to', backref='assigned_staff', lazy='dynamic')
    ticket_responses = db.relationship('TicketResponse', backref='responder', lazy='dynamic')
    department = db.relationship('Department', backref='staff_members')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'full_name': self.full_name,
            'student_id': self.student_id,
            'department_id': self.department_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    tickets = db.relationship('Ticket', backref='department', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class TicketCategory(db.Model):
    __tablename__ = 'ticket_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    icon = db.Column(db.String(50), default='📋')  # Emoji or icon class
    color = db.Column(db.String(7), default='#007bff')  # Hex color code
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    tickets = db.relationship('Ticket', backref='category', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'color': self.color,
            'description': self.description,
            'is_active': self.is_active
        }

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), unique=True, nullable=False)  # Generated ticket ID
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='open')  # open, in_progress, resolved, closed
    priority = db.Column(db.String(20), nullable=False, default='medium')  # low, medium, high, urgent
    
    # Foreign Keys
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('ticket_categories.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Additional fields
    attachment_path = db.Column(db.String(255), nullable=True)
    satisfaction_rating = db.Column(db.Integer, nullable=True)  # 1-5 rating after resolution
    
    # Relationships
    responses = db.relationship('TicketResponse', backref='ticket', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'student_id': self.student_id,
            'category_id': self.category_id,
            'department_id': self.department_id,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'attachment_path': self.attachment_path,
            'satisfaction_rating': self.satisfaction_rating,
            'student_name': self.student.full_name if self.student else None,
            'category_name': self.category.name if self.category else None,
            'department_name': self.department.name if self.department else None,
            'assigned_staff_name': self.assigned_staff.full_name if self.assigned_staff else None
        }

class TicketResponse(db.Model):
    __tablename__ = 'ticket_responses'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_internal = db.Column(db.Boolean, default=False)  # Internal staff notes vs public responses
    attachment_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'user_id': self.user_id,
            'message': self.message,
            'is_internal': self.is_internal,
            'attachment_path': self.attachment_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'responder_name': self.responder.full_name if self.responder else None,
            'responder_role': self.responder.role if self.responder else None
        }

class FAQ(db.Model):
    __tablename__ = 'faqs'
    
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('ticket_categories.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = db.relationship('TicketCategory', backref='faqs')

    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'is_active': self.is_active,
            'view_count': self.view_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

