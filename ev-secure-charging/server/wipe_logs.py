from app import app
from models import db, AttackLog, CryptoSecureLog

with app.app_context():
    AttackLog.query.delete()
    CryptoSecureLog.query.filter_by(event_type='attack_detected').delete()
    db.session.commit()
    print("Logs wiped successfully!")
