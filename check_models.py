# check_models.py
from portfolio_dashboard import create_app, db

app = create_app()

with app.app_context():
    print(db.metadata.tables.keys())