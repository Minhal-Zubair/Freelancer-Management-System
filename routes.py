import os
import secrets
from datetime import datetime, timedelta
from flask import render_template, url_for, flash, redirect, request, abort, jsonify, send_from_directory
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from app import app, db, bcrypt
from models import Freelancer, Client, Project, Task, TimeLog, Invoice, LoginSession, ProjectFile, Tag, ProjectTag
from models import ProjectStatus, TaskStatus, Priority, ClientType, InvoiceStatus
from forms import (RegistrationForm, LoginForm, FreelancerProfileForm, ClientForm, ProjectForm, 
                 TaskForm, TimeLogForm, InvoiceForm, TagForm, SearchForm, TimerForm)
from sqlalchemy import func, desc, and_, or_
import utils


# Home Route
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html', title='Freelancer Project Management System')


# User Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        freelancer = Freelancer(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            password_hash=hashed_password
        )
        db.session.add(freelancer)
        db.session.commit()
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        freelancer = Freelancer.query.filter_by(email=form.email.data).first()
        if freelancer and bcrypt.check_password_hash(freelancer.password_hash, form.password.data):
            # Create login session
            login_session = LoginSession(
                freelancer_id=freelancer.id,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(login_session)
            db.session.commit()
            
            login_user(freelancer, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    # Update login session
    if current_user.is_authenticated:
        login_session = LoginSession.query.filter_by(
            freelancer_id=current_user.id, 
            is_active=True
        ).order_by(LoginSession.login_time.desc()).first()
        
        if login_session:
            login_session.is_active = False
            login_session.logout_time = datetime.utcnow()
            db.session.commit()
    
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Recent projects (last 5)
    recent_projects = Project.query.filter_by(freelancer_id=current_user.id) \
                            .order_by(Project.last_updated.desc()).limit(5).all()
    
    # Projects by status
    project_stats = db.session.query(
        Project.status, 
        func.count(Project.id).label('count')
    ).filter_by(freelancer_id=current_user.id).group_by(Project.status).all()
    
    # Projects by priority
    priority_stats = db.session.query(
        Project.priority, 
        func.count(Project.id).label('count')
    ).filter_by(freelancer_id=current_user.id).group_by(Project.priority).all()
    
    # Upcoming deadlines (next 7 days)
    upcoming_deadlines = Project.query.filter(
        Project.freelancer_id == current_user.id,
        Project.deadline >= datetime.utcnow(),
        Project.deadline <= datetime.utcnow() + timedelta(days=7),
        Project.status != ProjectStatus.COMPLETED
    ).order_by(Project.deadline).all()
    
    # Recent time logs
    recent_time_logs = TimeLog.query.filter_by(freelancer_id=current_user.id) \
                             .order_by(TimeLog.start_time.desc()).limit(5).all()
    
    # Calculate earnings
    total_earnings = db.session.query(func.sum(Invoice.total_amount)) \
                           .filter_by(freelancer_id=current_user.id, 
                                     status=InvoiceStatus.PAID).scalar() or 0
    
    # Outstanding invoices
    outstanding_invoices = Invoice.query.filter(
        Invoice.freelancer_id == current_user.id,
        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.OVERDUE])
    ).all()
    outstanding_amount = sum(invoice.total_amount for invoice in outstanding_invoices)
    
    # Client distribution
    client_stats = db.session.query(
        Client.id, 
        Client.name,
        func.count(Project.id).label('project_count')
    ).join(Project, Client.id == Project.client_id) \
     .filter(Client.freelancer_id == current_user.id) \
     .group_by(Client.id, Client.name) \
     .order_by(desc('project_count')) \
     .limit(5).all()
    
    return render_template('dashboard.html', 
                         title='Dashboard',
                         recent_projects=recent_projects,
                         project_stats=project_stats,
                         priority_stats=priority_stats,
                         upcoming_deadlines=upcoming_deadlines,
                         recent_time_logs=recent_time_logs,
                         total_earnings=total_earnings,
                         outstanding_amount=outstanding_amount,
                         outstanding_invoices=len(outstanding_invoices),
                         client_stats=client_stats)


# Profile Management
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = FreelancerProfileForm()
    
    if form.validate_on_submit():
        # Check if current password is provided and correct
        if form.current_password.data:
            if not bcrypt.check_password_hash(current_user.password_hash, form.current_password.data):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('profile'))
            
            # Update password if new one provided
            if form.new_password.data:
                current_user.password_hash = bcrypt.generate_password_hash(
                    form.new_password.data).decode('utf-8')
        
        # Update profile image if provided
        if form.profile_image.data:
            picture_file = utils.save_picture(form.profile_image.data)
            current_user.profile_image = picture_file
        
        # Update other fields
        current_user.name = form.name.data
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile'))
    
    # Pre-populate form with current data
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.email.data = current_user.email
        form.phone.data = current_user.phone
    
    # Get stats for profile page
    total_projects = Project.query.filter_by(freelancer_id=current_user.id).count()
    completed_projects = Project.query.filter_by(
        freelancer_id=current_user.id, 
        status=ProjectStatus.COMPLETED
    ).count()
    total_clients = Client.query.filter_by(freelancer_id=current_user.id).count()
    
    # Calculate total hours logged
    total_hours = db.session.query(func.sum(TimeLog.duration)) \
                      .filter_by(freelancer_id=current_user.id).scalar() or 0
    total_hours = total_hours / 3600  # Convert seconds to hours
    
    # Recent login sessions
    login_sessions = LoginSession.query.filter_by(freelancer_id=current_user.id) \
                              .order_by(LoginSession.login_time.desc()).limit(5).all()
    
    return render_template('profile.html', 
                         title='Profile',
                         form=form,
                         profile_image=url_for('static', filename=f'uploads/{current_user.profile_image}'),
                         total_projects=total_projects,
                         completed_projects=completed_projects,
                         total_clients=total_clients,
                         total_hours=total_hours,
                         login_sessions=login_sessions)


# Client Management
@app.route('/clients')
@login_required
def clients():
    page = request.args.get('page', 1, type=int)
    clients = Client.query.filter_by(freelancer_id=current_user.id) \
                   .order_by(Client.name).paginate(page=page, per_page=10)
    
    # Get stats for each client
    client_stats = {}
    for client in clients.items:
        projects_count = Project.query.filter_by(client_id=client.id).count()
        completed_projects = Project.query.filter_by(
            client_id=client.id, 
            status=ProjectStatus.COMPLETED
        ).count()
        
        total_earnings = db.session.query(func.sum(Invoice.total_amount)) \
                             .filter_by(client_id=client.id, 
                                      status=InvoiceStatus.PAID).scalar() or 0
        
        client_stats[client.id] = {
            'projects_count': projects_count,
            'completed_projects': completed_projects,
            'total_earnings': total_earnings
        }
    
    return render_template('clients.html',
                         title='Clients',
                         clients=clients,
                         client_stats=client_stats)


@app.route('/clients/new', methods=['GET', 'POST'])
@login_required
def new_client():
    form = ClientForm()
    
    if form.validate_on_submit():
        client = Client(
            freelancer_id=current_user.id,
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            organization=form.organization.data,
            classification=ClientType(form.classification.data),
            notes=form.notes.data
        )
        db.session.add(client)
        db.session.commit()
        
        flash('Client has been created!', 'success')
        return redirect(url_for('clients'))
    
    return render_template('client_detail.html',
                         title='New Client',
                         form=form,
                         legend='New Client')


@app.route('/clients/<int:client_id>')
@login_required
def client(client_id):
    client = Client.query.get_or_404(client_id)
    
    # Make sure the client belongs to the current user
    if client.freelancer_id != current_user.id:
        abort(403)
    
    # Get all projects for this client
    projects = Project.query.filter_by(client_id=client.id).all()
    
    # Get all invoices for this client
    invoices = Invoice.query.filter_by(client_id=client.id).all()
    
    # Calculate total earnings from this client
    total_earnings = db.session.query(func.sum(Invoice.total_amount)) \
                         .filter_by(client_id=client.id, 
                                  status=InvoiceStatus.PAID).scalar() or 0
    
    # Calculate outstanding amount
    outstanding_amount = db.session.query(func.sum(Invoice.total_amount)) \
                             .filter(Invoice.client_id == client.id,
                                    Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.OVERDUE])) \
                             .scalar() or 0
    
    return render_template('client_detail.html',
                         title=client.name,
                         client=client,
                         projects=projects,
                         invoices=invoices,
                         total_earnings=total_earnings,
                         outstanding_amount=outstanding_amount)


@app.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    
    # Make sure the client belongs to the current user
    if client.freelancer_id != current_user.id:
        abort(403)
    
    form = ClientForm()
    
    if form.validate_on_submit():
        client.name = form.name.data
        client.email = form.email.data
        client.phone = form.phone.data
        client.organization = form.organization.data
        client.classification = ClientType(form.classification.data)
        client.notes = form.notes.data
        
        db.session.commit()
        
        flash('Client has been updated!', 'success')
        return redirect(url_for('client', client_id=client.id))
    
    elif request.method == 'GET':
        # Pre-populate form with current data
        form.name.data = client.name
        form.email.data = client.email
        form.phone.data = client.phone
        form.organization.data = client.organization
        form.classification.data = client.classification.value
        form.notes.data = client.notes
    
    return render_template('client_detail.html',
                         title=f'Edit {client.name}',
                         form=form,
                         legend='Edit Client',
                         client=client)


@app.route('/clients/<int:client_id>/delete', methods=['POST'])
@login_required
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    
    # Make sure the client belongs to the current user
    if client.freelancer_id != current_user.id:
        abort(403)
    
    # Check if client has projects
    projects = Project.query.filter_by(client_id=client.id).all()
    if projects:
        flash('Cannot delete client with associated projects.', 'danger')
        return redirect(url_for('client', client_id=client.id))
    
    db.session.delete(client)
    db.session.commit()
    
    flash('Client has been deleted!', 'success')
    return redirect(url_for('clients'))


# Project Management
@app.route('/projects')
@login_required
def projects():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', None)
    
    # Base query
    query = Project.query.filter_by(freelancer_id=current_user.id)
    
    # Apply status filter if provided
    if status_filter and status_filter != 'all':
        query = query.filter_by(status=ProjectStatus(status_filter))
    
    # Order projects by deadline (upcoming first) and then by creation date
    projects = query.order_by(
        Project.status,
        Project.deadline.asc().nullslast(),
        Project.date_created.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('projects.html',
                         title='Projects',
                         projects=projects,
                         status_filter=status_filter,
                         project_statuses=[status.value for status in ProjectStatus])


@app.route('/projects/new', methods=['GET', 'POST'])
@login_required
def new_project():
    form = ProjectForm(freelancer=current_user)
    
    if form.validate_on_submit():
        project = Project(
            freelancer_id=current_user.id,
            client_id=form.client_id.data,
            title=form.title.data,
            description=form.description.data,
            status=ProjectStatus(form.status.data),
            start_date=form.start_date.data,
            deadline=form.deadline.data,
            price=form.price.data,
            priority=Priority(form.priority.data)
        )
        db.session.add(project)
        db.session.commit()
        
        # Handle file uploads
        if form.files.data:
            for file in form.files.data:
                if file.filename:
                    file_saved = utils.save_project_file(file, project.id)
                    
                    if file_saved:
                        project_file = ProjectFile(
                            project_id=project.id,
                            filename=file_saved['filename'],
                            original_filename=file_saved['original_filename'],
                            file_type=file_saved['file_type'],
                            file_size=file_saved['file_size']
                        )
                        db.session.add(project_file)
            
            db.session.commit()
        
        flash('Project has been created!', 'success')
        return redirect(url_for('project', project_id=project.id))
    
    return render_template('project_detail.html',
                         title='New Project',
                         form=form,
                         legend='New Project')


@app.route('/projects/<int:project_id>')
@login_required
def project(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Make sure the project belongs to the current user
    if project.freelancer_id != current_user.id:
        abort(403)
    
    # Get all tasks for this project
    tasks = Task.query.filter_by(project_id=project.id).all()
    
    # Get all time logs for this project
    time_logs = TimeLog.query.filter_by(project_id=project.id) \
                     .order_by(TimeLog.start_time.desc()).all()
    
    # Calculate total time spent on the project
    total_time = db.session.query(func.sum(TimeLog.duration)) \
                     .filter_by(project_id=project.id).scalar() or 0
    total_hours = total_time / 3600  # Convert seconds to hours
    
    # Get all attachments for the project
    files = ProjectFile.query.filter_by(project_id=project.id).all()
    
    # Get all tags for this project
    project_tags = ProjectTag.query.filter_by(project_id=project.id).all()
    tags = [pt.tag for pt in project_tags]
    
    # Get all invoices for this project
    invoices = Invoice.query.filter_by(project_id=project.id).all()
    
    # Timer form for time tracking
    timer_form = TimerForm()
    timer_form.project_id.data = project.id
    
    return render_template('project_detail.html',
                         title=project.title,
                         project=project,
                         tasks=tasks,
                         time_logs=time_logs,
                         total_hours=total_hours,
                         files=files,
                         tags=tags,
                         invoices=invoices,
                         timer_form=timer_form)


@app.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Make sure the project belongs to the current user
    if project.freelancer_id != current_user.id:
        abort(403)
    
    form = ProjectForm(freelancer=current_user)
    
    if form.validate_on_submit():
        project.title = form.title.data
        project.description = form.description.data
        project.client_id = form.client_id.data
        project.status = ProjectStatus(form.status.data)
        project.start_date = form.start_date.data
        project.deadline = form.deadline.data
        project.price = form.price.data
        project.priority = Priority(form.priority.data)
        
        # Handle file uploads
        if form.files.data:
            for file in form.files.data:
                if file.filename:
                    file_saved = utils.save_project_file(file, project.id)
                    
                    if file_saved:
                        project_file = ProjectFile(
                            project_id=project.id,
                            filename=file_saved['filename'],
                            original_filename=file_saved['original_filename'],
                            file_type=file_saved['file_type'],
                            file_size=file_saved['file_size']
                        )
                        db.session.add(project_file)
        
        db.session.commit()
        
        flash('Project has been updated!', 'success')
        return redirect(url_for('project', project_id=project.id))
    
    elif request.method == 'GET':
        # Pre-populate form with current data
        form.title.data = project.title
        form.description.data = project.description
        form.client_id.data = project.client_id
        form.status.data = project.status.value
        form.start_date.data = project.start_date
        form.deadline.data = project.deadline
        form.price.data = project.price
        form.priority.data = project.priority.value
    
    return render_template('project_detail.html',
                         title=f'Edit {project.title}',
                         form=form,
                         legend='Edit Project',
                         project=project)


@app.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Make sure the project belongs to the current user
    if project.freelancer_id != current_user.id:
        abort(403)
    
    # Delete associated records
    ProjectFile.query.filter_by(project_id=project.id).delete()
    TimeLog.query.filter_by(project_id=project.id).delete()
    Task.query.filter_by(project_id=project.id).delete()
    ProjectTag.query.filter_by(project_id=project.id).delete()
    
    # Update associated invoices to remove project reference
    invoices = Invoice.query.filter_by(project_id=project.id).all()
    for invoice in invoices:
        invoice.project_id = None
    
    db.session.delete(project)
    db.session.commit()
    
    flash('Project has been deleted!', 'success')
    return redirect(url_for('projects'))


@app.route('/projects/<int:project_id>/files/<filename>')
@login_required
def download_file(project_id, filename):
    project = Project.query.get_or_404(project_id)
    
    # Make sure the project belongs to the current user
    if project.freelancer_id != current_user.id:
        abort(403)
    
    # Verify that file exists for this project
    project_file = ProjectFile.query.filter_by(
        project_id=project.id, 
        filename=filename
    ).first_or_404()
    
    # Send the file
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], f'project_{project.id}'),
                              filename, 
                              as_attachment=True, 
                              download_name=project_file.original_filename)


@app.route('/projects/<int:project_id>/files/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_file(project_id, file_id):
    project = Project.query.get_or_404(project_id)
    
    # Make sure the project belongs to the current user
    if project.freelancer_id != current_user.id:
        abort(403)
    
    # Get the file
    project_file = ProjectFile.query.filter_by(
        id=file_id, 
        project_id=project.id
    ).first_or_404()
    
    # Delete file from filesystem
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f'project_{project.id}', project_file.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete record from database
    db.session.delete(project_file)
    db.session.commit()
    
    flash('File has been deleted!', 'success')
    return redirect(url_for('project', project_id=project.id))


# Task Management
@app.route('/projects/<int:project_id>/tasks/new', methods=['GET', 'POST'])
@login_required
def new_task(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Make sure the project belongs to the current user
    if project.freelancer_id != current_user.id:
        abort(403)
    
    form = TaskForm(project_id=project.id)
    
    if form.validate_on_submit():
        task = Task(
            project_id=project.id,
            title=form.title.data,
            description=form.description.data,
            status=TaskStatus(form.status.data),
            priority=Priority(form.priority.data),
            start_date=form.start_date.data,
            due_date=form.due_date.data
        )
        
        # Set parent task if provided
        if form.parent_id.data and form.parent_id.data > 0:
            task.parent_id = form.parent_id.data
        
        db.session.add(task)
        db.session.commit()
        
        flash('Task has been created!', 'success')
        return redirect(url_for('project', project_id=project.id))
    
    return render_template('tasks.html',
                         title='New Task',
                         form=form,
                         legend='New Task',
                         project=project)


@app.route('/projects/<int:project_id>/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(project_id, task_id):
    project = Project.query.get_or_404(project_id)
    
    # Make sure the project belongs to the current user
    if project.freelancer_id != current_user.id:
        abort(403)
    
    task = Task.query.get_or_404(task_id)
    
    # Make sure the task belongs to the project
    if task.project_id != project.id:
        abort(403)
    
    form = TaskForm(project_id=project.id, task_id=task.id)
    
    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.status = TaskStatus(form.status.data)
        task.priority = Priority(form.priority.data)
        task.start_date = form.start_date.data
        task.due_date = form.due_date.data
        
        # Set parent task if provided
        if form.parent_id.data and form.parent_id.data > 0:
            task.parent_id = form.parent_id.data
        else:
            task.parent_id = None
        
        db.session.commit()
        
        flash('Task has been updated!', 'success')
        return redirect(url_for('project', project_id=project.id))
    
    elif request.method == 'GET':
        # Pre-populate form with current data
        form.title.data = task.title
        form.description.data = task.description
        form.status.data = task.status.value
        form.priority.data = task.priority.value
        form.start_date.data = task.start_date
        form.due_date.data = task.due_date
        form.parent_id.data = task.parent_id if task.parent_id else 0
    
    return render_template('tasks.html',
                         title=f'Edit {task.title}',
                         form=form,
                         legend='Edit Task',
                         project=project,
                         task=task)


@app.route('/projects/<int:project_id>/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(project_id, task_id):
    project = Project.query.get_or_404(project_id)
    
    # Make sure the project belongs to the current user
    if project.freelancer_id != current_user.id:
        abort(403)
    
    task = Task.query.get_or_404(task_id)
    
    # Make sure the task belongs to the project
    if task.project_id != project.id:
        abort(403)
    
    # Check for dependent tasks and update them
    dependent_tasks = Task.query.filter_by(parent_id=task.id).all()
    for dependent_task in dependent_tasks:
        dependent_task.parent_id = None
    
    # Delete time logs associated with this task
    TimeLog.query.filter_by(task_id=task.id).delete()
    
    db.session.delete(task)
    db.session.commit()
    
    flash('Task has been deleted!', 'success')
    return redirect(url_for('project', project_id=project.id))


# Time Tracking
@app.route('/timetracking')
@login_required
def timetracking():
    page = request.args.get('page', 1, type=int)
    date_filter = request.args.get('date', None)
    project_filter = request.args.get('project', None, type=int)
    
    # Base query
    query = TimeLog.query.filter_by(freelancer_id=current_user.id)
    
    # Apply date filter if provided
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(
                func.date(TimeLog.start_time) == filter_date
            )
        except ValueError:
            pass
    
    # Apply project filter if provided
    if project_filter:
        query = query.filter_by(project_id=project_filter)
    
    # Get time logs
    time_logs = query.order_by(TimeLog.start_time.desc()).paginate(page=page, per_page=15)
    
    # Get all projects for filter dropdown
    projects = Project.query.filter_by(freelancer_id=current_user.id).all()
    
    # Calculate total hours for the filtered time logs
    total_time = db.session.query(func.sum(TimeLog.duration)) \
                     .filter_by(freelancer_id=current_user.id)
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            total_time = total_time.filter(
                func.date(TimeLog.start_time) == filter_date
            )
        except ValueError:
            pass
    
    if project_filter:
        total_time = total_time.filter_by(project_id=project_filter)
    
    total_time = total_time.scalar() or 0
    total_hours = total_time / 3600  # Convert seconds to hours
    
    return render_template('timetracking.html',
                         title='Time Tracking',
                         time_logs=time_logs,
                         projects=projects,
                         project_filter=project_filter,
                         date_filter=date_filter,
                         total_hours=total_hours)


@app.route('/timetracking/new', methods=['GET', 'POST'])
@login_required
def new_time_log():
    form = TimeLogForm(freelancer=current_user)
    
    # Handle dynamic task dropdown
    if request.args.get('project_id'):
        project_id = int(request.args.get('project_id'))
        form.project_id.data = project_id
        form.task_id.choices = [(0, 'No Specific Task')] + [(task.id, task.title) 
                              for task in Task.query.filter_by(project_id=project_id).all()]
    
    if form.validate_on_submit():
        # Calculate duration
        duration = None
        if form.end_time.data:
            delta = form.end_time.data - form.start_time.data
            duration = delta.total_seconds()
        
        time_log = TimeLog(
            freelancer_id=current_user.id,
            project_id=form.project_id.data,
            task_id=form.task_id.data if form.task_id.data else None,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            duration=duration,
            notes=form.notes.data,
            is_billable=form.is_billable.data
        )
        db.session.add(time_log)
        db.session.commit()
        
        flash('Time log has been created!', 'success')
        return redirect(url_for('timetracking'))
    
    return render_template('timetracking.html',
                         title='New Time Log',
                         form=form,
                         legend='New Time Log')


@app.route('/timetracking/<int:time_log_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_time_log(time_log_id):
    time_log = TimeLog.query.get_or_404(time_log_id)
    
    # Make sure the time log belongs to the current user
    if time_log.freelancer_id != current_user.id:
        abort(403)
    
    form = TimeLogForm(freelancer=current_user)
    
    # Set task choices based on project
    if time_log.project_id:
        form.task_id.choices = [(0, 'No Specific Task')] + [(task.id, task.title) 
                              for task in Task.query.filter_by(project_id=time_log.project_id).all()]
    
    if form.validate_on_submit():
        # Calculate duration
        duration = None
        if form.end_time.data:
            delta = form.end_time.data - form.start_time.data
            duration = delta.total_seconds()
        
        time_log.project_id = form.project_id.data
        time_log.task_id = form.task_id.data if form.task_id.data else None
        time_log.start_time = form.start_time.data
        time_log.end_time = form.end_time.data
        time_log.duration = duration
        time_log.notes = form.notes.data
        time_log.is_billable = form.is_billable.data
        
        db.session.commit()
        
        flash('Time log has been updated!', 'success')
        return redirect(url_for('timetracking'))
    
    elif request.method == 'GET':
        # Pre-populate form with current data
        form.project_id.data = time_log.project_id
        form.task_id.data = time_log.task_id if time_log.task_id else 0
        form.start_time.data = time_log.start_time
        form.end_time.data = time_log.end_time
        form.notes.data = time_log.notes
        form.is_billable.data = time_log.is_billable
    
    return render_template('timetracking.html',
                         title='Edit Time Log',
                         form=form,
                         legend='Edit Time Log',
                         time_log=time_log)


@app.route('/timetracking/<int:time_log_id>/delete', methods=['POST'])
@login_required
def delete_time_log(time_log_id):
    time_log = TimeLog.query.get_or_404(time_log_id)
    
    # Make sure the time log belongs to the current user
    if time_log.freelancer_id != current_user.id:
        abort(403)
    
    db.session.delete(time_log)
    db.session.commit()
    
    flash('Time log has been deleted!', 'success')
    return redirect(url_for('timetracking'))


@app.route('/timer/start', methods=['POST'])
@login_required
def start_timer():
    project_id = request.form.get('project_id')
    task_id = request.form.get('task_id')
    
    if not project_id:
        return jsonify({"error": "Project ID is required"}), 400
    
    # Check if there's an active timer
    active_timer = TimeLog.query.filter_by(
        freelancer_id=current_user.id,
        end_time=None
    ).first()
    
    if active_timer:
        return jsonify({"error": "You already have an active timer"}), 400
    
    # Create a new time log
    time_log = TimeLog(
        freelancer_id=current_user.id,
        project_id=project_id,
        task_id=task_id if task_id else None,
        start_time=datetime.utcnow(),
        is_billable=True
    )
    db.session.add(time_log)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "time_log_id": time_log.id,
        "message": "Timer started"
    })


@app.route('/timer/stop', methods=['POST'])
@login_required
def stop_timer():
    time_log_id = request.form.get('time_log_id')
    
    if not time_log_id:
        # Find active timer if time_log_id not provided
        time_log = TimeLog.query.filter_by(
            freelancer_id=current_user.id,
            end_time=None
        ).first()
        
        if not time_log:
            return jsonify({"error": "No active timer found"}), 400
    else:
        time_log = TimeLog.query.get_or_404(time_log_id)
    
    # Make sure the time log belongs to the current user
    if time_log.freelancer_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Stop the timer
    end_time = datetime.utcnow()
    time_log.end_time = end_time
    
    # Calculate duration
    delta = end_time - time_log.start_time
    time_log.duration = delta.total_seconds()
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "time_log_id": time_log.id,
        "duration": time_log.duration,
        "message": "Timer stopped"
    })


# Invoice Management
@app.route('/invoices')
@login_required
def invoices():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', None)
    client_filter = request.args.get('client', None, type=int)
    
    # Base query
    query = Invoice.query.filter_by(freelancer_id=current_user.id)
    
    # Apply status filter if provided
    if status_filter and status_filter != 'all':
        query = query.filter_by(status=InvoiceStatus(status_filter))
    
    # Apply client filter if provided
    if client_filter:
        query = query.filter_by(client_id=client_filter)
    
    # Get invoices
    invoices = query.order_by(Invoice.issue_date.desc()).paginate(page=page, per_page=10)
    
    # Get all clients for filter dropdown
    clients = Client.query.filter_by(freelancer_id=current_user.id).all()
    
    # Calculate total amount for all invoices
    total_amount = db.session.query(func.sum(Invoice.total_amount)) \
                       .filter_by(freelancer_id=current_user.id).scalar() or 0
    
    # Calculate total paid amount
    paid_amount = db.session.query(func.sum(Invoice.total_amount)) \
                      .filter_by(freelancer_id=current_user.id, 
                               status=InvoiceStatus.PAID).scalar() or 0
    
    # Calculate outstanding amount
    outstanding_amount = db.session.query(func.sum(Invoice.total_amount)) \
                             .filter(Invoice.freelancer_id == current_user.id,
                                    Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.OVERDUE])) \
                             .scalar() or 0
    
    return render_template('invoices.html',
                         title='Invoices',
                         invoices=invoices,
                         clients=clients,
                         status_filter=status_filter,
                         client_filter=client_filter,
                         invoice_statuses=[status.value for status in InvoiceStatus],
                         total_amount=total_amount,
                         paid_amount=paid_amount,
                         outstanding_amount=outstanding_amount)


@app.route('/invoices/new', methods=['GET', 'POST'])
@login_required
def new_invoice():
    form = InvoiceForm(freelancer=current_user)
    
    # Handle dynamic project dropdown based on selected client
    if request.args.get('client_id'):
        client_id = int(request.args.get('client_id'))
        form.client_id.data = client_id
        form.project_id.choices = [(0, 'No Specific Project')] + [(project.id, project.title) 
                                  for project in Project.query.filter_by(client_id=client_id).all()]
    
    if form.validate_on_submit():
        # Calculate tax amount and total
        amount = form.amount.data
        tax_rate = form.tax_rate.data / 100 if form.tax_rate.data else 0
        tax_amount = amount * tax_rate
        total_amount = amount + tax_amount
        
        invoice = Invoice(
            freelancer_id=current_user.id,
            client_id=form.client_id.data,
            project_id=form.project_id.data if form.project_id.data and form.project_id.data > 0 else None,
            title=form.title.data,
            issue_date=form.issue_date.data,
            due_date=form.due_date.data,
            amount=amount,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_amount=total_amount,
            status=InvoiceStatus(form.status.data),
            notes=form.notes.data,
            payment_method=form.payment_method.data,
            transaction_id=form.transaction_id.data,
            payment_date=form.payment_date.data
        )
        db.session.add(invoice)
        db.session.commit()
        
        flash('Invoice has been created!', 'success')
        return redirect(url_for('invoice', invoice_id=invoice.id))
    
    # Set default dates
    if request.method == 'GET':
        form.issue_date.data = datetime.utcnow()
        form.due_date.data = datetime.utcnow() + timedelta(days=15)
    
    return render_template('invoice_detail.html',
                         title='New Invoice',
                         form=form,
                         legend='New Invoice')


@app.route('/invoices/<int:invoice_id>')
@login_required
def invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Make sure the invoice belongs to the current user
    if invoice.freelancer_id != current_user.id:
        abort(403)
    
    return render_template('invoice_detail.html',
                         title=f'Invoice #{invoice.invoice_number}',
                         invoice=invoice)


@app.route('/invoices/<int:invoice_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Make sure the invoice belongs to the current user
    if invoice.freelancer_id != current_user.id:
        abort(403)
    
    form = InvoiceForm(freelancer=current_user)
    
    # Set project choices based on selected client
    form.project_id.choices = [(0, 'No Specific Project')] + [(project.id, project.title) 
                              for project in Project.query.filter_by(client_id=invoice.client_id).all()]
    
    if form.validate_on_submit():
        # Calculate tax amount and total
        amount = form.amount.data
        tax_rate = form.tax_rate.data / 100 if form.tax_rate.data else 0
        tax_amount = amount * tax_rate
        total_amount = amount + tax_amount
        
        invoice.client_id = form.client_id.data
        invoice.project_id = form.project_id.data if form.project_id.data and form.project_id.data > 0 else None
        invoice.title = form.title.data
        invoice.issue_date = form.issue_date.data
        invoice.due_date = form.due_date.data
        invoice.amount = amount
        invoice.tax_rate = tax_rate
        invoice.tax_amount = tax_amount
        invoice.total_amount = total_amount
        invoice.status = InvoiceStatus(form.status.data)
        invoice.notes = form.notes.data
        invoice.payment_method = form.payment_method.data
        invoice.transaction_id = form.transaction_id.data
        invoice.payment_date = form.payment_date.data
        
        db.session.commit()
        
        flash('Invoice has been updated!', 'success')
        return redirect(url_for('invoice', invoice_id=invoice.id))
    
    elif request.method == 'GET':
        # Pre-populate form with current data
        form.client_id.data = invoice.client_id
        form.project_id.data = invoice.project_id if invoice.project_id else 0
        form.title.data = invoice.title
        form.issue_date.data = invoice.issue_date
        form.due_date.data = invoice.due_date
        form.amount.data = invoice.amount
        form.tax_rate.data = invoice.tax_rate * 100 if invoice.tax_rate else 0
        form.status.data = invoice.status.value
        form.notes.data = invoice.notes
        form.payment_method.data = invoice.payment_method
        form.transaction_id.data = invoice.transaction_id
        form.payment_date.data = invoice.payment_date
    
    return render_template('invoice_detail.html',
                         title=f'Edit Invoice #{invoice.invoice_number}',
                         form=form,
                         legend='Edit Invoice',
                         invoice=invoice)


@app.route('/invoices/<int:invoice_id>/delete', methods=['POST'])
@login_required
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Make sure the invoice belongs to the current user
    if invoice.freelancer_id != current_user.id:
        abort(403)
    
    db.session.delete(invoice)
    db.session.commit()
    
    flash('Invoice has been deleted!', 'success')
    return redirect(url_for('invoices'))


# Calendar & Reports
@app.route('/calendar')
@login_required
def calendar():
    # Get all projects with deadlines
    projects = Project.query.filter(
        Project.freelancer_id == current_user.id,
        Project.deadline.isnot(None)
    ).all()
    
    # Get all tasks with due dates
    tasks = Task.query.join(Project).filter(
        Project.freelancer_id == current_user.id,
        Task.due_date.isnot(None)
    ).all()
    
    # Get all invoices with due dates
    invoices = Invoice.query.filter(
        Invoice.freelancer_id == current_user.id,
        Invoice.due_date.isnot(None)
    ).all()
    
    # Build JSON data for calendar
    events = []
    
    for project in projects:
        events.append({
            'id': f'project_{project.id}',
            'title': f'Project: {project.title}',
            'start': project.deadline.strftime('%Y-%m-%d'),
            'color': '#3788d8',
            'extendedProps': {
                'type': 'project',
                'id': project.id,
                'status': project.status.value
            }
        })
    
    for task in tasks:
        events.append({
            'id': f'task_{task.id}',
            'title': f'Task: {task.title}',
            'start': task.due_date.strftime('%Y-%m-%d'),
            'color': '#f56954',
            'extendedProps': {
                'type': 'task',
                'id': task.id,
                'project_id': task.project_id,
                'status': task.status.value
            }
        })
    
    for invoice in invoices:
        events.append({
            'id': f'invoice_{invoice.id}',
            'title': f'Invoice: {invoice.invoice_number}',
            'start': invoice.due_date.strftime('%Y-%m-%d'),
            'color': '#00a65a',
            'extendedProps': {
                'type': 'invoice',
                'id': invoice.id,
                'status': invoice.status.value
            }
        })
    
    return render_template('calendar.html',
                         title='Calendar',
                         events=events)


@app.route('/reports')
@login_required
def reports():
    report_type = request.args.get('type', 'earnings')
    period = request.args.get('period', 'monthly')
    
    data = {}
    labels = []
    
    # Earnings Report
    if report_type == 'earnings':
        if period == 'monthly':
            # Monthly earnings for the current year
            current_year = datetime.utcnow().year
            for month in range(1, 13):
                month_name = datetime(current_year, month, 1).strftime('%B')
                
                # Get total paid invoices for the month
                earnings = db.session.query(func.sum(Invoice.total_amount)) \
                               .filter(Invoice.freelancer_id == current_user.id,
                                      Invoice.status == InvoiceStatus.PAID,
                                      func.extract('year', Invoice.payment_date) == current_year,
                                      func.extract('month', Invoice.payment_date) == month) \
                               .scalar() or 0
                
                labels.append(month_name)
                data[month_name] = earnings
        
        elif period == 'yearly':
            # Yearly earnings for the last 5 years
            current_year = datetime.utcnow().year
            for year in range(current_year - 4, current_year + 1):
                # Get total paid invoices for the year
                earnings = db.session.query(func.sum(Invoice.total_amount)) \
                               .filter(Invoice.freelancer_id == current_user.id,
                                      Invoice.status == InvoiceStatus.PAID,
                                      func.extract('year', Invoice.payment_date) == year) \
                               .scalar() or 0
                
                labels.append(str(year))
                data[str(year)] = earnings
    
    # Projects Report
    elif report_type == 'projects':
        # Count projects by status
        projects_by_status = db.session.query(
            Project.status, 
            func.count(Project.id).label('count')
        ).filter_by(freelancer_id=current_user.id).group_by(Project.status).all()
        
        for status, count in projects_by_status:
            labels.append(status.value)
            data[status.value] = count
    
    # Clients Report
    elif report_type == 'clients':
        # Get top clients by revenue
        top_clients = db.session.query(
            Client.id,
            Client.name,
            func.sum(Invoice.total_amount).label('total_paid')
        ).join(Invoice, Client.id == Invoice.client_id) \
         .filter(Invoice.freelancer_id == current_user.id,
                Invoice.status == InvoiceStatus.PAID) \
         .group_by(Client.id, Client.name) \
         .order_by(desc('total_paid')) \
         .limit(5).all()
        
        for client_id, client_name, total_paid in top_clients:
            labels.append(client_name)
            data[client_name] = total_paid
    
    # Time Report
    elif report_type == 'time':
        if period == 'monthly':
            # Monthly time logged for the current year
            current_year = datetime.utcnow().year
            for month in range(1, 13):
                month_name = datetime(current_year, month, 1).strftime('%B')
                
                # Get total time logged for the month (in hours)
                time_logged = db.session.query(func.sum(TimeLog.duration)) \
                                  .filter(TimeLog.freelancer_id == current_user.id,
                                         func.extract('year', TimeLog.start_time) == current_year,
                                         func.extract('month', TimeLog.start_time) == month) \
                                  .scalar() or 0
                time_logged = time_logged / 3600  # Convert seconds to hours
                
                labels.append(month_name)
                data[month_name] = time_logged
        
        elif period == 'projects':
            # Time logged per project
            top_projects = db.session.query(
                Project.id,
                Project.title,
                func.sum(TimeLog.duration).label('total_time')
            ).join(TimeLog, Project.id == TimeLog.project_id) \
             .filter(TimeLog.freelancer_id == current_user.id) \
             .group_by(Project.id, Project.title) \
             .order_by(desc('total_time')) \
             .limit(5).all()
            
            for project_id, project_title, total_time in top_projects:
                total_hours = total_time / 3600  # Convert seconds to hours
                labels.append(project_title)
                data[project_title] = total_hours
    
    return render_template('reports.html',
                         title='Reports',
                         report_type=report_type,
                         period=period,
                         labels=labels,
                         data=data)


# Search and Utility Routes
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()
    results = {'projects': [], 'clients': [], 'tasks': [], 'invoices': []}
    query = None
    
    if form.validate_on_submit() or request.args.get('query'):
        query = form.query.data or request.args.get('query')
        
        if query:
            # Search projects
            projects = Project.query.filter(
                Project.freelancer_id == current_user.id,
                or_(
                    Project.title.ilike(f'%{query}%'),
                    Project.description.ilike(f'%{query}%')
                )
            ).all()
            results['projects'] = projects
            
            # Search clients
            clients = Client.query.filter(
                Client.freelancer_id == current_user.id,
                or_(
                    Client.name.ilike(f'%{query}%'),
                    Client.email.ilike(f'%{query}%'),
                    Client.organization.ilike(f'%{query}%')
                )
            ).all()
            results['clients'] = clients
            
            # Search tasks
            tasks = Task.query.join(Project).filter(
                Project.freelancer_id == current_user.id,
                or_(
                    Task.title.ilike(f'%{query}%'),
                    Task.description.ilike(f'%{query}%')
                )
            ).all()
            results['tasks'] = tasks
            
            # Search invoices
            invoices = Invoice.query.filter(
                Invoice.freelancer_id == current_user.id,
                or_(
                    Invoice.title.ilike(f'%{query}%'),
                    Invoice.invoice_number.ilike(f'%{query}%')
                )
            ).all()
            results['invoices'] = invoices
    
    return render_template('search.html',
                         title='Search Results',
                         form=form,
                         query=query,
                         results=results)


@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html', title='Settings')


@app.route('/api/check-duplicate-email', methods=['POST'])
def check_duplicate_email():
    email = request.json.get('email')
    user_id = request.json.get('user_id')
    
    if not email:
        return jsonify({"valid": False, "message": "Email is required"}), 400
    
    query = Freelancer.query.filter_by(email=email)
    
    # If checking for an existing user (edit profile), exclude current user
    if user_id:
        query = query.filter(Freelancer.id != int(user_id))
    
    user = query.first()
    
    if user:
        return jsonify({"valid": False, "message": "Email is already in use"})
    
    return jsonify({"valid": True})


@app.route('/api/projects/<int:project_id>/tasks')
@login_required
def get_project_tasks(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Make sure the project belongs to the current user
    if project.freelancer_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    tasks = Task.query.filter_by(project_id=project.id).all()
    tasks_list = [{"id": task.id, "title": task.title} for task in tasks]
    
    return jsonify({"tasks": [{"id": 0, "title": "No Specific Task"}] + tasks_list})


@app.route('/api/clients/<int:client_id>/projects')
@login_required
def get_client_projects(client_id):
    client = Client.query.get_or_404(client_id)
    
    # Make sure the client belongs to the current user
    if client.freelancer_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    projects = Project.query.filter_by(client_id=client.id).all()
    projects_list = [{"id": project.id, "title": project.title} for project in projects]
    
    return jsonify({"projects": [{"id": 0, "title": "No Specific Project"}] + projects_list})


@app.route('/api/freelancer/stats')
@login_required
def get_freelancer_stats():
    # Total projects
    total_projects = Project.query.filter_by(freelancer_id=current_user.id).count()
    
    # Projects by status
    projects_by_status = db.session.query(
        Project.status, 
        func.count(Project.id).label('count')
    ).filter_by(freelancer_id=current_user.id).group_by(Project.status).all()
    
    status_counts = {status.value: 0 for status in ProjectStatus}
    for status, count in projects_by_status:
        status_counts[status.value] = count
    
    # Total earnings
    total_earnings = db.session.query(func.sum(Invoice.total_amount)) \
                         .filter_by(freelancer_id=current_user.id, 
                                  status=InvoiceStatus.PAID).scalar() or 0
    
    # Outstanding amount
    outstanding_amount = db.session.query(func.sum(Invoice.total_amount)) \
                             .filter(Invoice.freelancer_id == current_user.id,
                                    Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.OVERDUE])) \
                             .scalar() or 0
    
    # Total time logged (in hours)
    total_time = db.session.query(func.sum(TimeLog.duration)) \
                     .filter_by(freelancer_id=current_user.id).scalar() or 0
    total_hours = total_time / 3600
    
    # Recent activity
    recent_activity = []
    
    # Recent projects
    recent_projects = Project.query.filter_by(freelancer_id=current_user.id) \
                            .order_by(Project.date_created.desc()).limit(3).all()
    for project in recent_projects:
        recent_activity.append({
            'type': 'project',
            'id': project.id,
            'title': project.title,
            'date': project.date_created,
            'message': f'Project created: {project.title}'
        })
    
    # Recent time logs
    recent_time_logs = TimeLog.query.filter_by(freelancer_id=current_user.id) \
                             .order_by(TimeLog.start_time.desc()).limit(3).all()
    for time_log in recent_time_logs:
        project = Project.query.get(time_log.project_id)
        recent_activity.append({
            'type': 'time_log',
            'id': time_log.id,
            'title': project.title if project else 'Unknown Project',
            'date': time_log.start_time,
            'message': f'Time logged for: {project.title if project else "Unknown Project"}'
        })
    
    # Recent invoices
    recent_invoices = Invoice.query.filter_by(freelancer_id=current_user.id) \
                            .order_by(Invoice.issue_date.desc()).limit(3).all()
    for invoice in recent_invoices:
        recent_activity.append({
            'type': 'invoice',
            'id': invoice.id,
            'title': invoice.invoice_number,
            'date': invoice.issue_date,
            'message': f'Invoice created: {invoice.invoice_number}'
        })
    
    # Sort by date descending
    recent_activity.sort(key=lambda x: x['date'], reverse=True)
    recent_activity = recent_activity[:5]  # Get top 5
    
    # Format dates for JSON
    for activity in recent_activity:
        activity['date'] = activity['date'].strftime('%Y-%m-%d %H:%M')
    
    return jsonify({
        'total_projects': total_projects,
        'projects_by_status': status_counts,
        'total_earnings': total_earnings,
        'outstanding_amount': outstanding_amount,
        'total_hours': total_hours,
        'recent_activity': recent_activity
    })


# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', title='Page Not Found', error_code=404, 
                         message='The page you are looking for does not exist.'), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', title='Forbidden', error_code=403, 
                         message='You do not have permission to access this resource.'), 403


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', title='Server Error', error_code=500, 
                         message='An internal server error occurred.'), 500
