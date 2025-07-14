from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import session
from src.models.user import User
import json

socketio = SocketIO(cors_allowed_origins="*")

# Store user sessions
user_sessions = {}

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if 'user_id' not in session:
        return False  # Reject connection if not authenticated
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        return False
    
    # Store user session
    user_sessions[user_id] = {
        'sid': session.get('sid'),
        'role': user.role,
        'department_id': user.department_id
    }
    
    # Join user to their personal room
    join_room(f'user_{user_id}')
    
    # Join staff to their department room
    if user.role == 'staff' and user.department_id:
        join_room(f'dept_{user.department_id}')
    
    # Join admin to admin room
    if user.role == 'admin':
        join_room('admin')
    
    emit('connected', {'message': 'Connected successfully'})
    print(f"User {user.username} connected")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    if 'user_id' in session:
        user_id = session['user_id']
        if user_id in user_sessions:
            user = User.query.get(user_id)
            if user:
                # Leave all rooms
                leave_room(f'user_{user_id}')
                if user.role == 'staff' and user.department_id:
                    leave_room(f'dept_{user.department_id}')
                if user.role == 'admin':
                    leave_room('admin')
                
                print(f"User {user.username} disconnected")
            
            del user_sessions[user_id]

@socketio.on('join_ticket_room')
def handle_join_ticket_room(data):
    """Join a specific ticket room for real-time updates"""
    if 'user_id' not in session:
        return
    
    ticket_id = data.get('ticket_id')
    if ticket_id:
        join_room(f'ticket_{ticket_id}')
        emit('joined_ticket_room', {'ticket_id': ticket_id})

@socketio.on('leave_ticket_room')
def handle_leave_ticket_room(data):
    """Leave a specific ticket room"""
    if 'user_id' not in session:
        return
    
    ticket_id = data.get('ticket_id')
    if ticket_id:
        leave_room(f'ticket_{ticket_id}')
        emit('left_ticket_room', {'ticket_id': ticket_id})

def notify_new_ticket(ticket):
    """Notify relevant users about new ticket"""
    # Notify department staff
    socketio.emit('new_ticket', {
        'ticket': ticket.to_dict(),
        'message': f'New ticket created: {ticket.title}'
    }, room=f'dept_{ticket.department_id}')
    
    # Notify admin
    socketio.emit('new_ticket', {
        'ticket': ticket.to_dict(),
        'message': f'New ticket created: {ticket.title}'
    }, room='admin')

def notify_ticket_update(ticket, update_type, message):
    """Notify relevant users about ticket updates"""
    # Notify the student who created the ticket
    socketio.emit('ticket_update', {
        'ticket': ticket.to_dict(),
        'update_type': update_type,
        'message': message
    }, room=f'user_{ticket.student_id}')
    
    # Notify department staff
    socketio.emit('ticket_update', {
        'ticket': ticket.to_dict(),
        'update_type': update_type,
        'message': message
    }, room=f'dept_{ticket.department_id}')
    
    # Notify admin
    socketio.emit('ticket_update', {
        'ticket': ticket.to_dict(),
        'update_type': update_type,
        'message': message
    }, room='admin')
    
    # Notify users in the specific ticket room
    socketio.emit('ticket_update', {
        'ticket': ticket.to_dict(),
        'update_type': update_type,
        'message': message
    }, room=f'ticket_{ticket.id}')

def notify_new_response(ticket, response):
    """Notify relevant users about new response"""
    # Notify the student who created the ticket (if response is not internal)
    if not response.is_internal:
        socketio.emit('new_response', {
            'ticket': ticket.to_dict(),
            'response': response.to_dict(),
            'message': f'New response on ticket {ticket.ticket_id}'
        }, room=f'user_{ticket.student_id}')
    
    # Notify department staff
    socketio.emit('new_response', {
        'ticket': ticket.to_dict(),
        'response': response.to_dict(),
        'message': f'New response on ticket {ticket.ticket_id}'
    }, room=f'dept_{ticket.department_id}')
    
    # Notify admin
    socketio.emit('new_response', {
        'ticket': ticket.to_dict(),
        'response': response.to_dict(),
        'message': f'New response on ticket {ticket.ticket_id}'
    }, room='admin')
    
    # Notify users in the specific ticket room
    socketio.emit('new_response', {
        'ticket': ticket.to_dict(),
        'response': response.to_dict(),
        'message': f'New response on ticket {ticket.ticket_id}'
    }, room=f'ticket_{ticket.id}')

def notify_ticket_assignment(ticket, assigned_staff):
    """Notify about ticket assignment"""
    if assigned_staff:
        # Notify the assigned staff member
        socketio.emit('ticket_assigned', {
            'ticket': ticket.to_dict(),
            'message': f'Ticket {ticket.ticket_id} has been assigned to you'
        }, room=f'user_{assigned_staff.id}')
        
        # Notify the student
        socketio.emit('ticket_update', {
            'ticket': ticket.to_dict(),
            'update_type': 'assignment',
            'message': f'Your ticket has been assigned to {assigned_staff.full_name}'
        }, room=f'user_{ticket.student_id}')

def get_online_users():
    """Get list of currently online users"""
    online_users = []
    for user_id, session_data in user_sessions.items():
        user = User.query.get(user_id)
        if user:
            online_users.append({
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role
            })
    return online_users

@socketio.on('get_online_users')
def handle_get_online_users():
    """Send list of online users to requesting client"""
    if 'user_id' not in session:
        return
    
    online_users = get_online_users()
    emit('online_users', {'users': online_users})

# Periodic tasks (if needed)
def send_periodic_updates():
    """Send periodic updates to connected clients"""
    # This could be used for sending system status updates, etc.
    pass

