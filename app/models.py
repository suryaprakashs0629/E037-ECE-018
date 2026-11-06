from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import UniqueConstraint, CheckConstraint
from .extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='GROUP_USER')
    group_id = db.Column(db.String(20), db.ForeignKey('groups.group_id'), nullable=True, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    can_submit_emergency = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    group = db.relationship('Group', back_populates='users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='scrypt')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'ADMIN'

class Group(db.Model):
    __tablename__ = 'groups'
    group_id = db.Column(db.String(20), primary_key=True)
    group_name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(30), nullable=False, index=True)
    priority_rank = db.Column(db.Integer, nullable=False)
    contact_name = db.Column(db.String(120), default='')
    contact_mobile = db.Column(db.String(20), default='')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    users = db.relationship('User', back_populates='group')

class Channel(db.Model):
    __tablename__ = 'channels'
    channel_no = db.Column(db.Integer, primary_key=True)
    frequency_mhz = db.Column(db.Numeric(10,5), nullable=False)
    spacing_khz = db.Column(db.Numeric(5,2), nullable=False, default=12.5)
    is_emergency = db.Column(db.Boolean, default=False, nullable=False)

class RadioRequest(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer, primary_key=True)
    request_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.String(20), db.ForeignKey('groups.group_id'), nullable=False, index=True)
    request_date = db.Column(db.Date, nullable=False, index=True)
    start_slot = db.Column(db.Integer, nullable=False)
    end_slot = db.Column(db.Integer, nullable=False)
    channel_count = db.Column(db.Integer, nullable=False)
    fixed_channels = db.Column(db.String(80), nullable=False, default='ANY')
    purpose = db.Column(db.String(500), nullable=False)
    is_emergency = db.Column(db.Boolean, default=False, nullable=False)
    emergency_justification = db.Column(db.String(500), default='')
    status = db.Column(db.String(24), default='PENDING_REVIEW', nullable=False, index=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    submission_sequence = db.Column(db.Integer, nullable=False, default=0)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_comment = db.Column(db.String(500), default='')
    group = db.relationship('Group')
    submitter = db.relationship('User', foreign_keys=[user_id])
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])

class AllocationRun(db.Model):
    __tablename__ = 'allocation_runs'
    id = db.Column(db.Integer, primary_key=True)
    allocation_date = db.Column(db.Date, nullable=False, index=True)
    started_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    run_type = db.Column(db.String(30), nullable=False, default='WEB')
    status = db.Column(db.String(20), nullable=False, default='RUNNING')
    summary = db.Column(db.Text, default='')
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    actor = db.relationship('User')

class Allocation(db.Model):
    __tablename__ = 'allocations'
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('allocation_runs.id'), nullable=False, index=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=False, index=True)
    allocation_date = db.Column(db.Date, nullable=False, index=True)
    slot = db.Column(db.Integer, nullable=False)
    channel_no = db.Column(db.Integer, db.ForeignKey('channels.channel_no'), nullable=False)
    group_id = db.Column(db.String(20), db.ForeignKey('groups.group_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    request = db.relationship('RadioRequest')
    channel = db.relationship('Channel')
    group = db.relationship('Group')
    __table_args__ = (
        UniqueConstraint('allocation_date','slot','channel_no', name='uq_allocation_date_slot_channel'),
        CheckConstraint('channel_no BETWEEN 1 AND 15', name='ck_allocatable_channel_only'),
        CheckConstraint('slot BETWEEN 1 AND 48', name='ck_allocation_slot_range'),
    )

class ConflictLog(db.Model):
    __tablename__ = 'conflict_logs'
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('allocation_runs.id'), nullable=True, index=True)
    allocation_date = db.Column(db.Date, nullable=False, index=True)
    request_code = db.Column(db.String(32), nullable=False, index=True)
    group_id = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.String(40), nullable=False)
    detail = db.Column(db.String(80), nullable=False, default='NONE')
    sequence_no = db.Column(db.Integer, nullable=False, default=0)
    message = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class RequestEvent(db.Model):
    __tablename__ = 'request_events'
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=False, index=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    event_type = db.Column(db.String(40), nullable=False)
    note = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    request = db.relationship('RadioRequest')
    actor = db.relationship('User')

class AllocationHistory(db.Model):
    __tablename__ = 'allocation_history'
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('allocation_runs.id'), nullable=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=False, index=True)
    event_type = db.Column(db.String(40), nullable=False)
    snapshot = db.Column(db.Text, nullable=False, default='{}')
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=True)
    title = db.Column(db.String(140), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship('User')

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(80), nullable=False)
    target_type = db.Column(db.String(60), nullable=False)
    target_id = db.Column(db.String(80), default='')
    details = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    actor = db.relationship('User')

class ImportBatch(db.Model):
    __tablename__ = 'import_batches'
    id = db.Column(db.Integer, primary_key=True)
    batch_code = db.Column(db.String(40), unique=True, nullable=False, index=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), nullable=False, default='COMPLETED')
    summary = db.Column(db.Text, default='')
    output_dir = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    uploader = db.relationship('User')

class ScheduleLock(db.Model):
    __tablename__ = 'schedule_locks'
    schedule_date = db.Column(db.Date, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
