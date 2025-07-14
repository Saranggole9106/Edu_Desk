import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.user import db, User, Department, TicketCategory, FAQ
from datetime import datetime
import random
import string

def generate_ticket_id():
    """Generate a unique ticket ID"""
    return 'TKT' + ''.join(random.choices(string.digits, k=6))

def init_database():
    """Initialize database with sample data"""
    
    # Create departments
    departments = [
        {'name': 'Admissions', 'description': 'Handle admission-related queries and document verification'},
        {'name': 'Examinations', 'description': 'Manage exam schedules, hall tickets, and result queries'},
        {'name': 'Fees & Accounts', 'description': 'Process fee payments, receipts, and financial queries'},
        {'name': 'Academic Affairs', 'description': 'Handle academic records, transcripts, and course-related issues'},
        {'name': 'IT Support', 'description': 'Technical support for online portals and system issues'},
        {'name': 'Student Services', 'description': 'General student welfare and support services'}
    ]
    
    for dept_data in departments:
        existing_dept = Department.query.filter_by(name=dept_data['name']).first()
        if not existing_dept:
            dept = Department(**dept_data)
            db.session.add(dept)
    
    db.session.commit()
    
    # Create ticket categories
    categories = [
        {'name': 'Admissions', 'icon': '🎓', 'color': '#28a745', 'description': 'Admission process, document submission, merit lists'},
        {'name': 'Documents', 'icon': '📄', 'color': '#17a2b8', 'description': 'Certificates, transcripts, ID cards, bonafide'},
        {'name': 'Fees', 'icon': '💰', 'color': '#ffc107', 'description': 'Fee payment, receipts, refunds, scholarships'},
        {'name': 'Examinations', 'icon': '📝', 'color': '#dc3545', 'description': 'Exam schedules, hall tickets, results, re-evaluation'},
        {'name': 'Technical Support', 'icon': '💻', 'color': '#6f42c1', 'description': 'Portal issues, login problems, system errors'},
        {'name': 'General Inquiry', 'icon': '❓', 'color': '#6c757d', 'description': 'General questions and other queries'}
    ]
    
    for cat_data in categories:
        existing_cat = TicketCategory.query.filter_by(name=cat_data['name']).first()
        if not existing_cat:
            category = TicketCategory(**cat_data)
            db.session.add(category)
    
    db.session.commit()
    
    # Create admin user
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin = User(
            username='admin',
            email='admin@college.edu',
            full_name='System Administrator',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
    
    # Create sample staff users
    staff_users = [
        {'username': 'staff_admissions', 'email': 'admissions@college.edu', 'full_name': 'Admissions Officer', 'department': 'Admissions'},
        {'username': 'staff_exams', 'email': 'exams@college.edu', 'full_name': 'Exam Controller', 'department': 'Examinations'},
        {'username': 'staff_fees', 'email': 'fees@college.edu', 'full_name': 'Accounts Officer', 'department': 'Fees & Accounts'},
        {'username': 'staff_it', 'email': 'it@college.edu', 'full_name': 'IT Support', 'department': 'IT Support'}
    ]
    
    for staff_data in staff_users:
        existing_staff = User.query.filter_by(username=staff_data['username']).first()
        if not existing_staff:
            dept = Department.query.filter_by(name=staff_data['department']).first()
            staff = User(
                username=staff_data['username'],
                email=staff_data['email'],
                full_name=staff_data['full_name'],
                role='staff',
                department_id=dept.id if dept else None
            )
            staff.set_password('staff123')
            db.session.add(staff)
    
    # Create sample student users
    student_users = [
        {'username': 'student1', 'email': 'student1@college.edu', 'full_name': 'John Doe', 'student_id': 'STU001'},
        {'username': 'student2', 'email': 'student2@college.edu', 'full_name': 'Jane Smith', 'student_id': 'STU002'},
        {'username': 'student3', 'email': 'student3@college.edu', 'full_name': 'Mike Johnson', 'student_id': 'STU003'}
    ]
    
    for student_data in student_users:
        existing_student = User.query.filter_by(username=student_data['username']).first()
        if not existing_student:
            student = User(
                username=student_data['username'],
                email=student_data['email'],
                full_name=student_data['full_name'],
                role='student',
                student_id=student_data['student_id']
            )
            student.set_password('student123')
            db.session.add(student)
    
    db.session.commit()
    
    # Create sample FAQs
    faqs = [
        {
            'question': 'How do I download my hall ticket?',
            'answer': 'You can download your hall ticket from the student portal under the "Examinations" section. Login with your credentials and click on "Download Hall Ticket". If you face any issues, please create a support ticket.',
            'category': 'Examinations'
        },
        {
            'question': 'What documents are required for admission?',
            'answer': 'Required documents include: 1) 10th and 12th mark sheets, 2) Transfer certificate, 3) Conduct certificate, 4) Passport size photographs, 5) Caste certificate (if applicable), 6) Income certificate (for scholarships).',
            'category': 'Admissions'
        },
        {
            'question': 'How can I pay my fees online?',
            'answer': 'Visit the college website and go to the "Fee Payment" section. Select your course and semester, enter your student ID, and proceed with online payment using credit/debit card or net banking.',
            'category': 'Fees'
        },
        {
            'question': 'How do I get a bonafide certificate?',
            'answer': 'Submit an application to the Student Services office with your ID card copy and fee receipt. Processing time is 3-5 working days. You can also apply online through the student portal.',
            'category': 'Documents'
        },
        {
            'question': 'I forgot my portal password. How do I reset it?',
            'answer': 'Click on "Forgot Password" on the login page, enter your registered email ID or student ID. You will receive a password reset link via email. Follow the instructions to create a new password.',
            'category': 'Technical Support'
        }
    ]
    
    for faq_data in faqs:
        existing_faq = FAQ.query.filter_by(question=faq_data['question']).first()
        if not existing_faq:
            category = TicketCategory.query.filter_by(name=faq_data['category']).first()
            faq = FAQ(
                question=faq_data['question'],
                answer=faq_data['answer'],
                category_id=category.id if category else None
            )
            db.session.add(faq)
    
    db.session.commit()
    print("Database initialized successfully with sample data!")

if __name__ == '__main__':
    from flask import Flask
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        init_database()

