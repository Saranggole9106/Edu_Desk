from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Ticket, TicketCategory, Department, TicketResponse
from src.routes.auth import login_required, role_required
from datetime import datetime
import random
import string
import os
from werkzeug.utils import secure_filename

tickets_bp = Blueprint('tickets', __name__)

def generate_ticket_id():
    """Generate a unique ticket ID"""
    while True:
        ticket_id = 'TKT' + ''.join(random.choices(string.digits, k=6))
        if not Ticket.query.filter_by(ticket_id=ticket_id).first():
            return ticket_id

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@tickets_bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    """Get all active ticket categories"""
    try:
        categories = TicketCategory.query.filter_by(is_active=True).all()
        return jsonify({
            'categories': [cat.to_dict() for cat in categories]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/create', methods=['POST'])
@login_required
def create_ticket():
    """Create a new ticket (students only)"""
    try:
        # Check if user is a student
        user = User.query.get(session['user_id'])
        if user.role != 'student':
            return jsonify({'error': 'Only students can create tickets'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'description', 'category_id', 'department_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate category and department exist
        category = TicketCategory.query.get(data['category_id'])
        if not category:
            return jsonify({'error': 'Invalid category'}), 400
        
        department = Department.query.get(data['department_id'])
        if not department:
            return jsonify({'error': 'Invalid department'}), 400
        
        # Create ticket
        ticket = Ticket(
            ticket_id=generate_ticket_id(),
            title=data['title'],
            description=data['description'],
            student_id=user.id,
            category_id=data['category_id'],
            department_id=data['department_id'],
            priority=data.get('priority', 'medium')
        )
        
        db.session.add(ticket)
        db.session.commit()
        
        # Send real-time notification
        try:
            from src.routes.websocket import notify_new_ticket
            notify_new_ticket(ticket)
        except ImportError:
            pass  # WebSocket not available
        
        return jsonify({
            'message': 'Ticket created successfully',
            'ticket': ticket.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/my-tickets', methods=['GET'])
@login_required
def get_my_tickets():
    """Get tickets for current user"""
    try:
        user = User.query.get(session['user_id'])
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status_filter = request.args.get('status')
        
        if user.role == 'student':
            query = Ticket.query.filter_by(student_id=user.id)
        elif user.role == 'staff':
            query = Ticket.query.filter_by(department_id=user.department_id)
        else:  # admin
            query = Ticket.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        tickets = query.order_by(Ticket.created_at.desc()).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'tickets': [ticket.to_dict() for ticket in tickets.items],
            'total': tickets.total,
            'pages': tickets.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/<int:ticket_id>', methods=['GET'])
@login_required
def get_ticket(ticket_id):
    """Get ticket details with responses"""
    try:
        user = User.query.get(session['user_id'])
        ticket = Ticket.query.get(ticket_id)
        
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        # Check permissions
        if user.role == 'student' and ticket.student_id != user.id:
            return jsonify({'error': 'Access denied'}), 403
        elif user.role == 'staff' and ticket.department_id != user.department_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get responses
        responses = TicketResponse.query.filter_by(ticket_id=ticket.id).order_by(TicketResponse.created_at.asc()).all()
        
        # Filter internal responses for students
        if user.role == 'student':
            responses = [r for r in responses if not r.is_internal]
        
        ticket_data = ticket.to_dict()
        ticket_data['responses'] = [response.to_dict() for response in responses]
        
        return jsonify({'ticket': ticket_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/<int:ticket_id>/respond', methods=['POST'])
@login_required
def respond_to_ticket(ticket_id):
    """Add response to ticket"""
    try:
        user = User.query.get(session['user_id'])
        ticket = Ticket.query.get(ticket_id)
        
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        # Check permissions
        if user.role == 'student' and ticket.student_id != user.id:
            return jsonify({'error': 'Access denied'}), 403
        elif user.role == 'staff' and ticket.department_id != user.department_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        if not data.get('message'):
            return jsonify({'error': 'Message is required'}), 400
        
        # Create response
        response = TicketResponse(
            ticket_id=ticket.id,
            user_id=user.id,
            message=data['message'],
            is_internal=data.get('is_internal', False) and user.role in ['staff', 'admin']
        )
        
        db.session.add(response)
        
        # Update ticket timestamp
        ticket.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send real-time notification
        try:
            from src.routes.websocket import notify_new_response
            notify_new_response(ticket, response)
        except ImportError:
            pass  # WebSocket not available
        
        return jsonify({
            'message': 'Response added successfully',
            'response': response.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/<int:ticket_id>/assign', methods=['POST'])
@role_required(['staff', 'admin'])
def assign_ticket(ticket_id):
    """Assign ticket to staff member"""
    try:
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        data = request.get_json()
        staff_id = data.get('staff_id')
        
        assigned_staff = None
        if staff_id:
            staff = User.query.get(staff_id)
            if not staff or staff.role != 'staff':
                return jsonify({'error': 'Invalid staff member'}), 400
            
            # Check if staff belongs to same department
            if staff.department_id != ticket.department_id:
                return jsonify({'error': 'Staff member not in same department'}), 400
            
            ticket.assigned_to = staff_id
            assigned_staff = staff
        else:
            ticket.assigned_to = None
        
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Send real-time notification
        try:
            from src.routes.websocket import notify_ticket_assignment
            notify_ticket_assignment(ticket, assigned_staff)
        except ImportError:
            pass  # WebSocket not available
        
        return jsonify({
            'message': 'Ticket assignment updated successfully',
            'ticket': ticket.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/<int:ticket_id>/status', methods=['POST'])
@role_required(['staff', 'admin'])
def update_ticket_status(ticket_id):
    """Update ticket status"""
    try:
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['open', 'in_progress', 'resolved', 'closed']:
            return jsonify({'error': 'Invalid status'}), 400
        
        old_status = ticket.status
        ticket.status = new_status
        ticket.updated_at = datetime.utcnow()
        
        if new_status == 'resolved':
            ticket.resolved_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send real-time notification
        try:
            from src.routes.websocket import notify_ticket_update
            notify_ticket_update(ticket, 'status', f'Ticket status changed from {old_status} to {new_status}')
        except ImportError:
            pass  # WebSocket not available
        
        return jsonify({
            'message': 'Ticket status updated successfully',
            'ticket': ticket.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/<int:ticket_id>/priority', methods=['POST'])
@role_required(['staff', 'admin'])
def update_ticket_priority(ticket_id):
    """Update ticket priority"""
    try:
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        data = request.get_json()
        new_priority = data.get('priority')
        
        if new_priority not in ['low', 'medium', 'high', 'urgent']:
            return jsonify({'error': 'Invalid priority'}), 400
        
        old_priority = ticket.priority
        ticket.priority = new_priority
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Send real-time notification
        try:
            from src.routes.websocket import notify_ticket_update
            notify_ticket_update(ticket, 'priority', f'Ticket priority changed from {old_priority} to {new_priority}')
        except ImportError:
            pass  # WebSocket not available
        
        return jsonify({
            'message': 'Ticket priority updated successfully',
            'ticket': ticket.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/<int:ticket_id>/rate', methods=['POST'])
@login_required
def rate_ticket(ticket_id):
    """Rate resolved ticket (students only)"""
    try:
        user = User.query.get(session['user_id'])
        if user.role != 'student':
            return jsonify({'error': 'Only students can rate tickets'}), 403
        
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        if ticket.student_id != user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        if ticket.status != 'resolved':
            return jsonify({'error': 'Can only rate resolved tickets'}), 400
        
        data = request.get_json()
        rating = data.get('rating')
        
        if not rating or rating not in [1, 2, 3, 4, 5]:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        ticket.satisfaction_rating = rating
        db.session.commit()
        
        return jsonify({
            'message': 'Rating submitted successfully',
            'ticket': ticket.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/stats', methods=['GET'])
@role_required(['staff', 'admin'])
def get_ticket_stats():
    """Get ticket statistics"""
    try:
        user = User.query.get(session['user_id'])
        
        # Base query
        if user.role == 'staff':
            base_query = Ticket.query.filter_by(department_id=user.department_id)
        else:  # admin
            base_query = Ticket.query
        
        # Get counts by status
        stats = {
            'total': base_query.count(),
            'open': base_query.filter_by(status='open').count(),
            'in_progress': base_query.filter_by(status='in_progress').count(),
            'resolved': base_query.filter_by(status='resolved').count(),
            'closed': base_query.filter_by(status='closed').count()
        }
        
        # Get counts by priority
        stats['priority'] = {
            'low': base_query.filter_by(priority='low').count(),
            'medium': base_query.filter_by(priority='medium').count(),
            'high': base_query.filter_by(priority='high').count(),
            'urgent': base_query.filter_by(priority='urgent').count()
        }
        
        # Get average satisfaction rating
        resolved_tickets = base_query.filter(
            Ticket.status == 'resolved',
            Ticket.satisfaction_rating.isnot(None)
        ).all()
        
        if resolved_tickets:
            avg_rating = sum(t.satisfaction_rating for t in resolved_tickets) / len(resolved_tickets)
            stats['average_rating'] = round(avg_rating, 2)
        else:
            stats['average_rating'] = None
        
        return jsonify({'stats': stats}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

