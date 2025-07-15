import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.tickets import tickets_bp
from src.routes.faq import faq_bp
from src.routes.websocket import socketio

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Set session cookie settings for cross-site authentication
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

# Enable CORS for all routes
CORS(app, supports_credentials=True)

# Initialize SocketIO
socketio.init_app(app, cors_allowed_origins="*")

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(tickets_bp, url_prefix='/api/tickets')
app.register_blueprint(faq_bp, url_prefix='/api/faq')

# uncomment if you need to use database
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    raise RuntimeError("DATABASE_URL environment variable not set!")
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

# Add this near the top of src/main.py
def insert_test_data():
    from src.models.user import db, Department, TicketCategory

    # Departments to add
    departments = ["Computer Science", "Mathematics", "Physics", "Chemistry"]
    for dept_name in departments:
        if not Department.query.filter_by(name=dept_name).first():
            db.session.add(Department(name=dept_name, is_active=True))

    # Categories to add
    categories = ["Exam", "Fees", "Hostel", "Library"]
    for cat_name in categories:
        if not TicketCategory.query.filter_by(name=cat_name).first():
            db.session.add(TicketCategory(name=cat_name, is_active=True))

    db.session.commit()
    print("Test departments and categories added!")

# Call this inside your app context at startup
with app.app_context():
    insert_test_data()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=False)
