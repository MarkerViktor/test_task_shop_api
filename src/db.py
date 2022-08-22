import sqlalchemy as sa

from src import entities


metadata = sa.MetaData()


user = sa.Table(
    'user', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('type', sa.Enum(entities.UserType), nullable=False),
    sa.Column('is_active', sa.Boolean, nullable=False, default=False),
)

product = sa.Table(
    'product', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('title', sa.Text, nullable=False),
    sa.Column('description', sa.Text, nullable=False),
    sa.Column('price_rub', sa.Numeric, nullable=False),
)

payment_account = sa.Table(
    'payment_account', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False),
    sa.Column('balance_rub', sa.Numeric, nullable=False, default=0),
)

transaction = sa.Table(
    'transaction', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('payment_account_id', sa.Integer, sa.ForeignKey('payment_account.id'), nullable=False),
    sa.Column('amount_rum', sa.Numeric, nullable=False),
)

auth_credentials = sa.Table(
    'user_auth_credentials', metadata,
    sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True),
    sa.Column('login', sa.Text, nullable=False),
    sa.Column('password_hash', sa.BINARY, nullable=False),
    sa.Column('password_salt', sa.BINARY, nullable=False),
)
