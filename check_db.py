# check_db.py
from portfolio_dashboard import create_app, db
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    inspector = inspect(db.engine)
    
    for table_name in inspector.get_table_names():
        print(f"Table: {table_name}")
        for column in inspector.get_columns(table_name):
            print(f"  Column: {column['name']}, Type: {column['type']}")
        print()
