import os
import secrets
from PIL import Image
from flask import current_app
from datetime import datetime


def save_picture(form_picture):
    """Save profile picture with a random name and resize it"""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    
    # Ensure upload folder exists
    upload_folder = os.path.join(current_app.root_path, 'static/uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    picture_path = os.path.join(upload_folder, picture_fn)
    
    # Resize image to save space
    output_size = (250, 250)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    return picture_fn


def save_project_file(form_file, project_id):
    """Save project file with a unique name"""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_file.filename)
    file_fn = random_hex + f_ext
    
    # Create project-specific upload folder
    project_folder = os.path.join(current_app.root_path, f'static/uploads/project_{project_id}')
    if not os.path.exists(project_folder):
        os.makedirs(project_folder)
    
    file_path = os.path.join(project_folder, file_fn)
    
    # Save the file
    form_file.save(file_path)
    
    # Get file size in bytes
    file_size = os.path.getsize(file_path)
    
    # Get file type (extension without the dot)
    file_type = f_ext.lstrip('.') if f_ext else ''
    
    return {
        'filename': file_fn,
        'original_filename': form_file.filename,
        'file_path': file_path,
        'file_type': file_type,
        'file_size': file_size
    }


def get_active_timer(freelancer_id):
    """Check if there's an active timer for the freelancer"""
    from models import TimeLog
    
    active_timer = TimeLog.query.filter_by(
        freelancer_id=freelancer_id,
        end_time=None
    ).first()
    
    return active_timer


def format_duration(seconds):
    """Format duration in seconds to hours, minutes, seconds format"""
    if not seconds:
        return "0h 0m 0s"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    return f"{int(hours)}h {int(minutes)}m {int(secs)}s"


def format_datetime(dt, format_str='%Y-%m-%d %H:%M'):
    """Format datetime object to string"""
    if not dt:
        return ""
    
    return dt.strftime(format_str)


def generate_invoice_number():
    """Generate a unique invoice number"""
    date_str = datetime.utcnow().strftime("%Y%m%d")
    random_str = secrets.token_hex(4).upper()
    return f"INV-{date_str}-{random_str}"


def calculate_project_progress(project):
    """Calculate project progress based on completed tasks"""
    from models import Task, TaskStatus
    
    # Get total tasks and completed tasks
    total_tasks = Task.query.filter_by(project_id=project.id).count()
    completed_tasks = Task.query.filter_by(
        project_id=project.id,
        status=TaskStatus.COMPLETED
    ).count()
    
    # Calculate progress percentage
    if total_tasks > 0:
        progress = (completed_tasks / total_tasks) * 100
    else:
        progress = 0
    
    return int(progress)


def get_project_status_class(status):
    """Return Bootstrap badge class based on project status"""
    status_classes = {
        'New': 'badge bg-info',
        'In Progress': 'badge bg-primary',
        'On Hold': 'badge bg-warning text-dark',
        'Completed': 'badge bg-success'
    }
    
    return status_classes.get(status, 'badge bg-secondary')


def get_priority_class(priority):
    """Return Bootstrap badge class based on priority"""
    priority_classes = {
        'Low': 'badge bg-success',
        'Medium': 'badge bg-info',
        'High': 'badge bg-warning text-dark',
        'Urgent': 'badge bg-danger'
    }
    
    return priority_classes.get(priority, 'badge bg-secondary')


def get_invoice_status_class(status):
    """Return Bootstrap badge class based on invoice status"""
    status_classes = {
        'Draft': 'badge bg-secondary',
        'Sent': 'badge bg-primary',
        'Paid': 'badge bg-success',
        'Overdue': 'badge bg-danger',
        'Cancelled': 'badge bg-dark'
    }
    
    return status_classes.get(status, 'badge bg-secondary')
