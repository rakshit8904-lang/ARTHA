"""
Database models.

Money is always an integer number of paise (amount_minor), never a float.
Dates are calendar dates in Asia/Kolkata. IDs are UUID strings.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, UniqueConstraint

from app.constants import (
    ACCOUNT_STATUSES, ACCOUNT_TYPES, APPROVAL_PENDING, APPROVAL_STATUSES,
    CURRENCY, DIRECTIONS, IMPORT_STATUSES, MEMBERSHIP_ACTIVE,
    MEMBERSHIP_STATUSES, ROLES, TRANSACTION_TYPES, VALIDATION_VALID,
)
from app.extensions import db


def new_id():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


def in_list(column, values):
    return "%s in (%s)" % (column, ", ".join("'" + v + "'" for v in values))


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=new_id)
    email = db.Column(db.String(320), nullable=False, unique=True)
    display_name = db.Column(db.String(120), nullable=False)
    auth_provider = db.Column(db.String(40), nullable=False, default="local")
    auth_ref = db.Column(db.String(255), nullable=False)
    email_verified_at = db.Column(db.DateTime(timezone=True), nullable=True)
    onboarding_answers = db.Column(db.JSON, nullable=False, default=dict)
    onboarding_completed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("auth_provider", "auth_ref", name="uq_users_provider_ref"),
    )


class LocalCredential(db.Model):
    __tablename__ = "local_credentials"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    password_hash = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


class Household(db.Model):
    __tablename__ = "households"

    id = db.Column(db.String(36), primary_key=True, default=new_id)
    name = db.Column(db.String(120), nullable=False)
    owner_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


class MonthlyPlan(db.Model):
    __tablename__ = "monthly_plans"
    household_id = db.Column(db.String(36), db.ForeignKey("households.id", ondelete="CASCADE"), primary_key=True)
    month = db.Column(db.String(7), primary_key=True)
    plan_type = db.Column(db.String(10), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    housing = db.Column(db.String(12))
    maintenance_included = db.Column(db.Boolean)
    income = db.Column(db.BigInteger, nullable=False)
    other_income = db.Column(db.BigInteger, nullable=False)
    limits = db.Column(db.JSON, nullable=False)
    revision = db.Column(db.Integer, nullable=False)
    allocation = db.Column(db.JSON, nullable=True)


class HouseholdMembership(db.Model):
    __tablename__ = "household_memberships"

    id = db.Column(db.String(36), primary_key=True, default=new_id)
    household_id = db.Column(db.String(36), db.ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)
    membership_status = db.Column(db.String(20), nullable=False, default=MEMBERSHIP_ACTIVE)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (
        UniqueConstraint("household_id", "user_id", name="uq_membership_household_user"),
        CheckConstraint(in_list("role", ROLES), name="ck_membership_role"),
        CheckConstraint(in_list("membership_status", MEMBERSHIP_STATUSES), name="ck_membership_status"),
    )


class Account(db.Model):
    __tablename__ = "accounts"

    id = db.Column(db.String(36), primary_key=True, default=new_id)
    household_id = db.Column(db.String(36), db.ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True)
    account_name = db.Column(db.String(120), nullable=False)
    account_type = db.Column(db.String(30), nullable=False)
    institution_name = db.Column(db.String(120), nullable=False, default="")
    currency = db.Column(db.String(3), nullable=False, default=CURRENCY)
    account_status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("id", "household_id", name="uq_accounts_id_household"),
        UniqueConstraint("household_id", "account_name", name="uq_account_household_name"),
        CheckConstraint(in_list("account_type", ACCOUNT_TYPES), name="ck_account_type"),
        CheckConstraint(in_list("account_status", ACCOUNT_STATUSES), name="ck_account_status"),
        CheckConstraint("currency = 'INR'", name="ck_account_currency"),
    )


class Import(db.Model):
    __tablename__ = "imports"

    id = db.Column(db.String(36), primary_key=True, default=new_id)
    household_id = db.Column(db.String(36), db.ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = db.Column(db.String(36), db.ForeignKey("accounts.id"), nullable=False, index=True)
    uploaded_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    file_hash = db.Column(db.String(64), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    parser_version = db.Column(db.String(40), nullable=False)
    import_status = db.Column(db.String(20), nullable=False)
    total_rows = db.Column(db.Integer, nullable=False, default=0)
    valid_rows = db.Column(db.Integer, nullable=False, default=0)
    invalid_rows = db.Column(db.Integer, nullable=False, default=0)
    error_message = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    review_expires_at = db.Column(db.DateTime(timezone=True), index=True)

    __table_args__ = (
        UniqueConstraint("id", "household_id", name="uq_imports_id_household"),
        UniqueConstraint("id", "account_id", name="uq_imports_id_account"),
        ForeignKeyConstraint(
            ["account_id", "household_id"],
            ["accounts.id", "accounts.household_id"],
            name="fk_imports_account_household",
            ondelete="CASCADE",
        ),
        CheckConstraint(in_list("import_status", IMPORT_STATUSES), name="ck_import_status"),
        # Exact re-import protection. Failed attempts do not block a retry.
        Index(
            "uq_import_account_hash_active", "account_id", "file_hash", unique=True,
            postgresql_where=db.text("import_status <> 'failed'"),
            sqlite_where=db.text("import_status <> 'failed'"),
        ),
    )


class StagedTransaction(db.Model):
    __tablename__ = "staged_transactions"

    id = db.Column(db.String(36), primary_key=True, default=new_id)
    import_id = db.Column(db.String(36), db.ForeignKey("imports.id", ondelete="CASCADE"), nullable=False, index=True)
    household_id = db.Column(db.String(36), db.ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = db.Column(db.String(36), db.ForeignKey("accounts.id"), nullable=False)
    source_row_number = db.Column(db.Integer, nullable=False)
    raw_row = db.Column(db.JSON, nullable=False)
    original_description = db.Column(db.Text, nullable=False, default="")
    description = db.Column(db.Text, nullable=False, default="")
    transaction_date = db.Column(db.Date)
    amount_minor = db.Column(db.BigInteger)
    currency = db.Column(db.String(3), nullable=False, default=CURRENCY)
    direction = db.Column(db.String(10))
    transaction_type = db.Column(db.String(30))
    suggested_category = db.Column(db.String(60))
    category = db.Column(db.String(60))
    matched_transaction_id = db.Column(db.String(36))
    validation_status = db.Column(db.String(20), nullable=False, default=VALIDATION_VALID)
    approval_status = db.Column(db.String(20), nullable=False, default=APPROVAL_PENDING)
    validation_errors = db.Column(db.JSON, nullable=False, default=list)
    potential_duplicate = db.Column(db.Boolean, nullable=False, default=False)
    duplicate_candidates = db.Column(db.JSON, nullable=False, default=list)
    edit_history = db.Column(db.JSON, nullable=False, default=list)
    transaction_id = db.Column(db.String(36))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("import_id", "source_row_number", name="uq_staged_import_row"),
        ForeignKeyConstraint(
            ["account_id", "household_id"],
            ["accounts.id", "accounts.household_id"],
            name="fk_staged_account_household",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["import_id", "account_id"],
            ["imports.id", "imports.account_id"],
            name="fk_staged_import_account",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["import_id", "household_id"],
            ["imports.id", "imports.household_id"],
            name="fk_staged_import_household",
            ondelete="CASCADE",
        ),
        CheckConstraint(in_list("approval_status", APPROVAL_STATUSES), name="ck_staged_approval"),
        CheckConstraint("validation_status in ('valid', 'invalid')", name="ck_staged_validation"),
    )


class Transaction(db.Model):
    """Approved ledger record. Only approved rows ever reach this table."""
    __tablename__ = "transactions"

    id = db.Column(db.String(36), primary_key=True, default=new_id)
    household_id = db.Column(db.String(36), db.ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    account_id = db.Column(db.String(36), db.ForeignKey("accounts.id"), nullable=False)
    import_id = db.Column(db.String(36), db.ForeignKey("imports.id"), nullable=False)
    source_row_number = db.Column(db.Integer, nullable=False)
    amount_minor = db.Column(db.BigInteger, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default=CURRENCY)
    direction = db.Column(db.String(10), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False)
    original_description = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    transaction_type = db.Column(db.String(30))  # Explicit "Review later" approval.
    category = db.Column(db.String(60))
    matched_transaction_id = db.Column(db.String(36), db.ForeignKey("transactions.id"))
    approval_status = db.Column(db.String(20), nullable=False, default="approved")
    correction_metadata = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("import_id", "source_row_number", name="uq_transaction_import_row"),
        ForeignKeyConstraint(
            ["account_id", "household_id"],
            ["accounts.id", "accounts.household_id"],
            name="fk_transactions_account_household",
        ),
        ForeignKeyConstraint(
            ["import_id", "account_id"],
            ["imports.id", "imports.account_id"],
            name="fk_transactions_import_account",
        ),
        ForeignKeyConstraint(
            ["import_id", "household_id"],
            ["imports.id", "imports.household_id"],
            name="fk_transactions_import_household",
        ),
        CheckConstraint("amount_minor >= 0", name="ck_transaction_amount_nonneg"),
        CheckConstraint("currency = 'INR'", name="ck_transaction_currency"),
        CheckConstraint(in_list("direction", DIRECTIONS), name="ck_transaction_direction"),
        CheckConstraint(in_list("transaction_type", TRANSACTION_TYPES), name="ck_transaction_type"),
        CheckConstraint("approval_status = 'approved'", name="ck_transaction_approved_only"),
        Index("ix_transactions_household_date", "household_id", "transaction_date"),
        Index("ix_transactions_account_dedupe", "account_id", "transaction_date", "amount_minor", "direction"),
    )


class TransferDecision(db.Model):
    __tablename__ = "transfer_decisions"
    debit_id = db.Column(db.String(36), db.ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True)
    credit_id = db.Column(db.String(36), db.ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True)
    decision = db.Column(db.String(10), nullable=False)
    __table_args__ = (
        CheckConstraint("decision in ('confirmed','dismissed','unsure')", name="ck_transfer_decision"),
        *(Index("uq_confirmed_" + leg, leg, unique=True,
                sqlite_where=db.text("decision = 'confirmed'"), postgresql_where=db.text("decision = 'confirmed'"))
          for leg in ("debit_id", "credit_id")),
    )


class RecurringExpense(db.Model):
    __tablename__ = "recurring_expenses"
    household_id = db.Column(db.String(36), db.ForeignKey("households.id", ondelete="CASCADE"), primary_key=True)
    fingerprint = db.Column(db.String(64), primary_key=True)
    description = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(60))
    typical_amount_minor = db.Column(db.BigInteger, nullable=False)
    status = db.Column(db.String(12), nullable=False)
    confirmed_by = db.Column(db.String(36), db.ForeignKey("users.id"))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    __table_args__ = (
        CheckConstraint("status in ('confirmed','dismissed')", name="ck_recurring_expense_status"),
        CheckConstraint("typical_amount_minor >= 0", name="ck_recurring_expense_amount"),
    )


class RelocationScenario(db.Model):
    __tablename__ = "relocation_scenarios"
    id = db.Column(db.String(36), primary_key=True, default=new_id)
    household_id = db.Column(db.String(36), db.ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    city_key = db.Column(db.String(100), nullable=False)
    inputs = db.Column(db.JSON, nullable=False)
    revision = db.Column(db.Integer, nullable=False, default=1)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


class SavedGoal(db.Model):
    """User-entered savings goal; results are recalculated from inputs and never touch the ledger."""
    __tablename__ = "saved_goals"
    id = db.Column(db.String(36), primary_key=True, default=new_id)
    household_id = db.Column(db.String(36), db.ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    inputs = db.Column(db.JSON, nullable=False)
    created_by = db.Column(db.String(36), db.ForeignKey("users.id", name="fk_saved_goals_created_by"), nullable=True)
    visibility = db.Column(db.String(10), nullable=False, default="household", server_default="household")
    revision = db.Column(db.Integer, nullable=False, default=1)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


class ProfileItem(db.Model):
    """One answer in the ongoing financial profile. state says whether amount is known, zero, n/a or unknown."""
    __tablename__ = "profile_items"
    id = db.Column(db.String(36), primary_key=True, default=new_id)
    household_id = db.Column(db.String(36), db.ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True)
    section = db.Column(db.String(20), nullable=False)
    kind = db.Column(db.String(30), nullable=False)
    label = db.Column(db.String(100), nullable=False, default="")
    state = db.Column(db.String(20), nullable=False)
    amount_minor = db.Column(db.BigInteger, nullable=True)
    frequency = db.Column(db.String(12), nullable=True)
    date = db.Column(db.Date, nullable=True)
    details = db.Column(db.JSON, nullable=False, default=dict)
    created_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    visibility = db.Column(db.String(10), nullable=False, default="household")
    revision = db.Column(db.Integer, nullable=False, default=1)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


class PortfolioHolding(db.Model):
    """User-entered investment position; current value is manually updated, never live-priced."""
    __tablename__ = "portfolio_holdings"
    id = db.Column(db.String(36), primary_key=True, default=new_id)
    household_id = db.Column(db.String(36), db.ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_name = db.Column(db.String(120), nullable=False)
    asset_type = db.Column(db.String(30), nullable=False)
    quantity = db.Column(db.Numeric(24, 8), nullable=False)
    invested_minor = db.Column(db.BigInteger, nullable=False)
    current_value_minor = db.Column(db.BigInteger, nullable=False)
    as_of_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.String(500), nullable=False, default="")
    created_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    __table_args__ = (
        CheckConstraint("invested_minor >= 0", name="ck_portfolio_invested_nonneg"),
        CheckConstraint("current_value_minor >= 0", name="ck_portfolio_value_nonneg"),
        CheckConstraint("quantity > 0", name="ck_portfolio_quantity_positive"),
        CheckConstraint("asset_type in ('mutual_fund','equity','etf','debt','gold','fixed_deposit','other')", name="ck_portfolio_asset_type"),
    )
