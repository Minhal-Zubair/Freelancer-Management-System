from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, DateTimeField, BooleanField
from wtforms import FloatField, IntegerField, MultipleFileField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from models import Freelancer, Client, ProjectStatus, Priority, TaskStatus, ClientType, InvoiceStatus
from datetime import datetime
from models import Client, Task, Project


class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', 
                                    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_email(self, email):
        user = Freelancer.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please login instead.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class FreelancerProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    profile_image = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    current_password = PasswordField('Current Password', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    confirm_new_password = PasswordField('Confirm New Password', 
                                       validators=[Optional(), EqualTo('new_password')])
    submit = SubmitField('Update Profile')


class ClientForm(FlaskForm):
    name = StringField('Client Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=15)])
    organization = StringField('Organization/Company', validators=[Optional(), Length(max=100)])
    classification = SelectField('Type', choices=[(type.value, type.value) for type in ClientType])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Client')


class ProjectForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    status = SelectField('Status', choices=[(status.value, status.value) for status in ProjectStatus])
    start_date = DateTimeField('Start Date', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    deadline = DateTimeField('Deadline', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    price = FloatField('Price', validators=[Optional()])
    priority = SelectField('Priority', choices=[(priority.value, priority.value) for priority in Priority])
    files = MultipleFileField('Attach Files', validators=[
        Optional(), 
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'png'])
    ])
    submit = SubmitField('Save Project')
    
    def __init__(self, freelancer=None, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        if freelancer:
            self.client_id.choices = [
                (c.id, c.name) for c in Client.query.filter_by(freelancer_id=freelancer.id).all()
            ]

class TaskForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    status = SelectField('Status', choices=[(status.value, status.value) for status in TaskStatus])
    priority = SelectField('Priority', choices=[(priority.value, priority.value) for priority in Priority])
    start_date = DateTimeField('Start Date', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    due_date = DateTimeField('Due Date', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    parent_id = SelectField('Depends On Task', coerce=int, validators=[Optional()])
    submit = SubmitField('Save Task')
    
    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop('project_id', None)
        task_id = kwargs.pop('task_id', None)
        super(TaskForm, self).__init__(*args, **kwargs)
        
        if project_id:
            # Exclude current task from dependency options
            if task_id:
                self.parent_id.choices = [(0, 'None')] + [(task.id, task.title) 
                                        for task in Task.query.filter_by(project_id=project_id)
                                        .filter(Task.id != task_id).all()]
            else:
                self.parent_id.choices = [(0, 'None')] + [(task.id, task.title) 
                                        for task in Task.query.filter_by(project_id=project_id).all()]


class TimeLogForm(FlaskForm):
    project_id = SelectField('Project', coerce=int, validators=[DataRequired()])
    task_id = SelectField('Task', coerce=int, validators=[Optional()])
    start_time = DateTimeField('Start Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    end_time = DateTimeField('End Time', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    notes = TextAreaField('Notes', validators=[Optional()])
    is_billable = BooleanField('Billable', default=True)
    submit = SubmitField('Save Time Log')
    
    def __init__(self, *args, **kwargs):
        freelancer = kwargs.pop('freelancer', None)
        project_id = kwargs.pop('project_id', None)
        super(TimeLogForm, self).__init__(*args, **kwargs)
        
        if freelancer:
            self.project_id.choices = [(project.id, project.title) 
                                     for project in Freelancer.query.filter_by(id=freelancer.id)
                                     .first().projects]
        
        if project_id:
            self.task_id.choices = [(0, 'No Specific Task')] + [(task.id, task.title) 
                                  for task in Task.query.filter_by(project_id=project_id).all()]


class InvoiceForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    project_id = SelectField('Project', coerce=int, validators=[Optional()])
    title = StringField('Invoice Title', validators=[DataRequired(), Length(min=2, max=100)])
    issue_date = DateTimeField('Issue Date', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    due_date = DateTimeField('Due Date', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    amount = FloatField('Amount', validators=[DataRequired()])
    tax_rate = FloatField('Tax Rate (%)', validators=[Optional()], default=0)
    notes = TextAreaField('Notes', validators=[Optional()])
    status = SelectField('Status', choices=[(status.value, status.value) for status in InvoiceStatus])
    payment_method = StringField('Payment Method', validators=[Optional()])
    transaction_id = StringField('Transaction ID', validators=[Optional()])
    payment_date = DateTimeField('Payment Date', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    submit = SubmitField('Save Invoice')
    
    def __init__(self, *args, **kwargs):
        freelancer = kwargs.pop('freelancer', None)
        client_id = kwargs.pop('client_id', None)
        super(InvoiceForm, self).__init__(*args, **kwargs)
        
        if freelancer:
            self.client_id.choices = [(client.id, client.name) 
                                    for client in Client.query.filter_by(freelancer_id=freelancer.id).all()]
        
        if client_id:
            self.project_id.choices = [(0, 'No Specific Project')] + [(project.id, project.title) 
                                     for project in Project.query.filter_by(client_id=client_id).all()]
        else:
            self.project_id.choices = [(0, 'No Specific Project')]  # 👈 add this to prevent None     


class TagForm(FlaskForm):
    name = StringField('Tag Name', validators=[DataRequired(), Length(min=2, max=50)])
    color = StringField('Color', validators=[DataRequired()], default="#6c757d")
    submit = SubmitField('Save Tag')


class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')


class TimerForm(FlaskForm):
    project_id = HiddenField('Project ID', validators=[DataRequired()])
    task_id = HiddenField('Task ID', validators=[Optional()])
    start_time = HiddenField('Start Time')
    is_running = HiddenField('Is Running', default='false')
    submit = SubmitField('Start Timer')
    
class SettingsForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Length(min=10, max=15)])
    profile_image = FileField('Profile Image')
    
    current_password = PasswordField('Current Password')
    new_password = PasswordField('New Password', validators=[Length(min=6, max=32)])
    confirm_new_password = PasswordField('Confirm New Password', validators=[
        EqualTo('new_password', message='Passwords must match')
    ])
    
    change_password = SubmitField('Change Password')  # Button for changing password
    
    submit = SubmitField('Update Settings')
