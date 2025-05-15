# check_records.py
from portfolio_dashboard import create_app, db
from portfolio_dashboard.models.account_balances import AccountBalances, MonthlyWithdrawal
from portfolio_dashboard.models.expenses import Expenses
from portfolio_dashboard.models.portfolio_position import PortfolioPosition
from portfolio_dashboard.models.portfolio_metadata import PortfolioMetadata
from portfolio_dashboard.models.user import User

app = create_app()

with app.app_context():
    print(f"Users: {User.query.count()}")
    print(f"Account Balances: {AccountBalances.query.count()}")
    print(f"Monthly Withdrawals: {MonthlyWithdrawal.query.count()}")
    print(f"Expenses: {Expenses.query.count()}")
    print(f"Portfolio Positions: {PortfolioPosition.query.count()}")
    print(f"Portfolio Metadata: {PortfolioMetadata.query.count()}")

