"""Payment and Escrow Marshmallow schemas."""

from marshmallow import Schema, fields


class STKPushInitiateSchema(Schema):
    booking_id = fields.String(required=True)
    phone_number = fields.String(required=True)


class SimulatePaymentCallbackSchema(Schema):
    checkout_request_id = fields.String(required=True)
    result_code = fields.Integer(required=False, load_default=0)  # 0 is success
    mpesa_receipt_number = fields.String(required=False, allow_none=True)
    amount_cents = fields.Integer(required=False, allow_none=True)
