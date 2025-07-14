from flask import Blueprint, request, jsonify, session
from src.models.user import db, FAQ, TicketCategory
from src.routes.auth import login_required, role_required

faq_bp = Blueprint('faq', __name__)

@faq_bp.route('/', methods=['GET'])
def get_faqs():
    """Get all active FAQs"""
    try:
        category_id = request.args.get('category_id', type=int)
        search_query = request.args.get('search', '')
        
        query = FAQ.query.filter_by(is_active=True)
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if search_query:
            query = query.filter(
                FAQ.question.contains(search_query) | 
                FAQ.answer.contains(search_query)
            )
        
        faqs = query.order_by(FAQ.view_count.desc()).all()
        
        return jsonify({
            'faqs': [faq.to_dict() for faq in faqs]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@faq_bp.route('/<int:faq_id>', methods=['GET'])
def get_faq(faq_id):
    """Get specific FAQ and increment view count"""
    try:
        faq = FAQ.query.get(faq_id)
        if not faq or not faq.is_active:
            return jsonify({'error': 'FAQ not found'}), 404
        
        # Increment view count
        faq.view_count += 1
        db.session.commit()
        
        return jsonify({'faq': faq.to_dict()}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@faq_bp.route('/create', methods=['POST'])
@role_required(['staff', 'admin'])
def create_faq():
    """Create new FAQ"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('question') or not data.get('answer'):
            return jsonify({'error': 'Question and answer are required'}), 400
        
        # Validate category if provided
        if data.get('category_id'):
            category = TicketCategory.query.get(data['category_id'])
            if not category:
                return jsonify({'error': 'Invalid category'}), 400
        
        faq = FAQ(
            question=data['question'],
            answer=data['answer'],
            category_id=data.get('category_id')
        )
        
        db.session.add(faq)
        db.session.commit()
        
        return jsonify({
            'message': 'FAQ created successfully',
            'faq': faq.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@faq_bp.route('/<int:faq_id>/update', methods=['PUT'])
@role_required(['staff', 'admin'])
def update_faq(faq_id):
    """Update FAQ"""
    try:
        faq = FAQ.query.get(faq_id)
        if not faq:
            return jsonify({'error': 'FAQ not found'}), 404
        
        data = request.get_json()
        
        if data.get('question'):
            faq.question = data['question']
        
        if data.get('answer'):
            faq.answer = data['answer']
        
        if 'category_id' in data:
            if data['category_id']:
                category = TicketCategory.query.get(data['category_id'])
                if not category:
                    return jsonify({'error': 'Invalid category'}), 400
            faq.category_id = data['category_id']
        
        db.session.commit()
        
        return jsonify({
            'message': 'FAQ updated successfully',
            'faq': faq.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@faq_bp.route('/<int:faq_id>/toggle-status', methods=['POST'])
@role_required(['staff', 'admin'])
def toggle_faq_status(faq_id):
    """Toggle FAQ active status"""
    try:
        faq = FAQ.query.get(faq_id)
        if not faq:
            return jsonify({'error': 'FAQ not found'}), 404
        
        faq.is_active = not faq.is_active
        db.session.commit()
        
        return jsonify({
            'message': f'FAQ {"activated" if faq.is_active else "deactivated"} successfully',
            'faq': faq.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@faq_bp.route('/<int:faq_id>/delete', methods=['DELETE'])
@role_required(['admin'])
def delete_faq(faq_id):
    """Delete FAQ (admin only)"""
    try:
        faq = FAQ.query.get(faq_id)
        if not faq:
            return jsonify({'error': 'FAQ not found'}), 404
        
        db.session.delete(faq)
        db.session.commit()
        
        return jsonify({'message': 'FAQ deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@faq_bp.route('/search', methods=['GET'])
def search_faqs():
    """Search FAQs with suggestions"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'faqs': []}), 200
        
        # Search in questions and answers
        faqs = FAQ.query.filter(
            FAQ.is_active == True,
            (FAQ.question.contains(query) | FAQ.answer.contains(query))
        ).order_by(FAQ.view_count.desc()).limit(10).all()
        
        return jsonify({
            'faqs': [faq.to_dict() for faq in faqs],
            'query': query
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

