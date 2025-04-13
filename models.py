from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
import uuid
import enum


@login_manager.user_loader
def load_user(user_id):
    return Freelancer.query.get(int(user_id))


class ProjectStatus(enum.Enum):
    NEW = "New"
    IN_PROGRESS = "In Progress"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"


class TaskStatus(enum.Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    BLOCKED = "Blocked"


class Priority(enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class ClientType(enum.Enum):
    INDIVIDUAL = "Individual"
    AGENCY = "Agency"
    RECURRING = "Recurring"


class InvoiceStatus(enum.Enum):
    DRAFT = "Draft"
    SENT = "Sent"
    PAID = "Paid"
    OVERDUE = "Overdue"
    CANCELLED = "Cancelled"


class Freelancer(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(256), nullable=False)
    profile_image = db.Column(db.String(255), default="default.jpg")
    freelancer_id = db.Column(db.String(15), unique=True, nullable=False)
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    clients = db.relationship('Client', backref='freelancer', lazy=True)
    projects = db.relationship('Project', backref='freelancer', lazy=True)
    time_logs = db.relationship('TimeLog', backref='freelancer', lazy=True)
    invoices = db.relationship('Invoice', backref='freelancer', lazy=True)
    login_sessions = db.relationship('LoginSession', backref='freelancer', lazy=True)
    
    def __init__(self, *args, **kwargs):
        super(Freelancer, self).__init__(*args, **kwargs)
        if not self.freelancer_id:
            self.freelancer_id = f"FL-{uuid.uuid4().hex[:10].upper()}"


class LoginSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    freelancer_id = db.Column(db.Integer, db.ForeignKey('freelancer.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # IPv6 can be up to 45 chars
    user_agent = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    logout_time = db.Column(db.DateTime)


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    freelancer_id = db.Column(db.Integer, db.ForeignKey('freelancer.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    organization = db.Column(db.String(100))
    classification = db.Column(db.Enum(ClientType), default=ClientType.INDIVIDUAL)
    notes = db.Column(db.Text)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('Project', backref='client', lazy=True)
    invoices = db.relationship('Invoice', backref='client', lazy=True)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    freelancer_id = db.Column(db.Integer, db.ForeignKey('freelancer.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Enum(ProjectStatus), default=ProjectStatus.NEW)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime)
    price = db.Column(db.Float)
    priority = db.Column(db.Enum(Priority), default=Priority.MEDIUM)
    progress = db.Column(db.Integer, default=0)  # 0-100%
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = db.relationship('Task', backref='project', lazy=True)
    time_logs = db.relationship('TimeLog', backref='project', lazy=True)
    files = db.relationship('ProjectFile', backref='project', lazy=True)
    invoices = db.relationship('Invoice', backref='project', lazy=True)
    project_tags = db.relationship('ProjectTag', backref='project', lazy=True)


class ProjectFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)  # Size in bytes
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Enum(TaskStatus), default=TaskStatus.NOT_STARTED)
    priority = db.Column(db.Enum(Priority), default=Priority.MEDIUM)
    start_date = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Self-referential relationship for task dependencies
    parent_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    dependencies = db.relationship(
        'Task',
        backref=db.backref('parent', remote_side=[id]),
        lazy=True
    )
    
    # Relationship with time logs
    time_logs = db.relationship('TimeLog', backref='task', lazy=True)


class TimeLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    freelancer_id = db.Column(db.Integer, db.ForeignKey('freelancer.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # Duration in seconds
    notes = db.Column(db.Text)
    is_billable = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    freelancer_id = db.Column(db.Integer, db.ForeignKey('freelancer.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    invoice_number = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    amount = db.Column(db.Float, nullable=False)
    tax_rate = db.Column(db.Float, default=0)
    tax_amount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    notes = db.Column(db.Text)
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    payment_date = db.Column(db.DateTime)
    
    def __init__(self, *args, **kwargs):
        super(Invoice, self).__init__(*args, **kwargs)
        if not self.invoice_number:
            # Generate a unique invoice number: INV-YYYYMMDD-XXXX
            date_str = datetime.utcnow().strftime("%Y%m%d")
            random_str = uuid.uuid4().hex[:4].upper()
            self.invoice_number = f"INV-{date_str}-{random_str}"


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    freelancer_id = db.Column(db.Integer, db.ForeignKey('freelancer.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), default="#6c757d")  # Hex color code
    
    # Relationship with ProjectTag
    project_tags = db.relationship('ProjectTag', backref='tag', lazy=True)


class ProjectTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add a unique constraint to prevent duplicate tags on a project
    __table_args__ = (db.UniqueConstraint('project_id', 'tag_id', name='unique_project_tag'),)
