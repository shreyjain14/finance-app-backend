from datetime import datetime
from flask import Blueprint, request, jsonify, make_response
from flask_cors import cross_origin
from .extentions import db
from .models import Payments
from flask_jwt_extended import jwt_required, current_user

api_payment = Blueprint('api_payment', __name__)


@api_payment.route('/create', methods=['POST'])
@jwt_required()
def create():
    data = request.get_json()
    payment = Payments(
        amount=data.get('amount'),
        payed_from=data.get('payed_from'),
        payed_to=data.get('payed_to'),
        user_id=current_user.id
    )
    db.session.add(payment)
    db.session.commit()
    return jsonify({'message': 'Payment created successfully'}), 201


@api_payment.get('/get')
@jwt_required()
def get_payments():

    payments = Payments.query.filter_by(user_id=current_user.id).all()

    payment_list = []
    for payment in payments:
        payment_data = {
            'id': payment.id,
            'amount': payment.amount,
            'payed_from': payment.payed_from,
            'payed_to': payment.payed_to,
            'date': payment.date.isoformat()  # Convert datetime to ISO format string
        }
        payment_list.append(payment_data)

    return jsonify(payment_list), 200


@api_payment.route('/delete', methods=['DELETE'])
@jwt_required()
def delete_payment():
    data = request.get_json()

    payment = Payments.query.get(data.get('id'))
    if payment:
        db.session.delete(payment)
        db.session.commit()
        return jsonify({'message': 'Payment deleted successfully'}), 200
    return jsonify({'message': 'Payment not found'}), 404
