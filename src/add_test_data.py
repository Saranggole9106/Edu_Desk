from src.models.user import db, Department, TicketCategory
from src.database.init_db import app

with app.app_context():
    # Add Departments
    if not Department.query.filter_by(name="Computer Science").first():
        cs = Department(name="Computer Science", is_active=True)
        db.session.add(cs)
    if not Department.query.filter_by(name="Mathematics").first():
        math = Department(name="Mathematics", is_active=True)
        db.session.add(math)

    # Add Categories
    if not TicketCategory.query.filter_by(name="Exam").first():
        exam = TicketCategory(name="Exam", is_active=True)
        db.session.add(exam)
    if not TicketCategory.query.filter_by(name="Fees").first():
        fees = TicketCategory(name="Fees", is_active=True)
        db.session.add(fees)

    db.session.commit()
    print("Test departments and categories added!") 