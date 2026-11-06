from __future__ import annotations
import csv, json, os, secrets, shutil
from datetime import datetime, date, timedelta
from functools import wraps
from pathlib import Path
from uuid import uuid4
from urllib.parse import urljoin, urlsplit
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from werkzeug.utils import secure_filename
from .extensions import db
from .models import (User, Group, Channel, RadioRequest, AllocationRun, Allocation, ConflictLog,
                     RequestEvent, AllocationHistory, Notification, AuditLog, ImportBatch, ScheduleLock)
from .services.allocation_engine import AllocationEngine, Channel as EngineChannel, Group as EngineGroup, Request as EngineRequest, Assignment, slot_start, utilisation
from .services.command_runner import run_commands, load_channels, load_groups

main = Blueprint('main', __name__)


def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


def audit(action, target_type, target_id='', details=''):
    db.session.add(AuditLog(actor_id=current_user.id if current_user.is_authenticated else None,
                            action=action, target_type=target_type, target_id=str(target_id), details=details))


def notify(user_id, title, message, request_id=None):
    if user_id:
        db.session.add(Notification(user_id=user_id, title=title, message=message, request_id=request_id))


def notify_group(group_id, title, message, request_id=None):
    for user in User.query.filter_by(group_id=group_id, is_active=True).all():
        db.session.add(Notification(user_id=user.id, title=title, message=message, request_id=request_id))


def master_engine():
    channels=[EngineChannel(c.channel_no, str(c.frequency_mhz), str(c.spacing_khz), c.is_emergency)
              for c in Channel.query.order_by(Channel.channel_no).all()]
    # Keep inactive groups in master lookup so existing historical/approved requests remain interpretable;
    # the request form separately prevents inactive groups from submitting new work.
    groups=[EngineGroup(g.group_id,g.group_name,g.category,g.priority_rank,g.contact_name or '',g.contact_mobile or '')
            for g in Group.query.all()]
    return AllocationEngine(channels, groups)


def request_to_engine(r):
    fixed=None if (r.fixed_channels or 'ANY').upper()=='ANY' else tuple(int(x) for x in r.fixed_channels.split(';') if x)
    return EngineRequest(r.request_code,r.group_id,r.request_date.isoformat(),r.start_slot,r.end_slot,
                         r.channel_count,fixed,r.submission_sequence,r.group.category,r.group.priority_rank,
                         r.purpose,'web',[],r.is_emergency)


def create_event(req, event_type, note=''):
    db.session.add(RequestEvent(request_id=req.id, actor_id=current_user.id if current_user.is_authenticated else None,
                                event_type=event_type, note=note))


def safe_date(value, default=None):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return default or date.today()

def safe_next_url(target):
    if not target:
        return None
    ref = urlsplit(request.host_url)
    test = urlsplit(urljoin(request.host_url, target))
    if test.scheme in {'http', 'https'} and test.netloc == ref.netloc:
        return target
    return None


def current_group_scope(query):
    if not current_user.is_admin:
        query=query.filter(RadioRequest.group_id==current_user.group_id)
    return query

@main.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method=='POST':
        username=request.form.get('username','').strip()
        password=request.form.get('password','')
        user=User.query.filter(func.lower(User.username)==username.lower()).first()
        if user and user.locked_until and user.locked_until > datetime.utcnow():
            flash('Sign-in is temporarily locked after repeated failed attempts. Try again later.', 'error')
        elif user and user.is_active and user.check_password(password):
            user.failed_login_attempts=0; user.locked_until=None
            login_user(user, remember=request.form.get('remember')=='on')
            audit('LOGIN','USER',user.id,'Successful login')
            db.session.commit()
            return redirect(safe_next_url(request.args.get('next')) or url_for('main.dashboard'))
        else:
            if user and user.is_active:
                user.failed_login_attempts=(user.failed_login_attempts or 0)+1
                if user.failed_login_attempts>=5:
                    user.failed_login_attempts=0; user.locked_until=datetime.utcnow()+timedelta(minutes=10)
            db.session.commit()
            flash('The username or password was not recognised.', 'error')
    return render_template('login.html')

@main.post('/logout')
@login_required
def logout():
    audit('LOGOUT','USER',current_user.id,'User signed out')
    db.session.commit(); logout_user()
    flash('You have been signed out.', 'success')
    return redirect(url_for('main.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    today=date.today()
    if current_user.is_admin:
        total_groups=Group.query.filter_by(is_active=True).count()
        total_users=User.query.filter_by(is_active=True).count()
        active_channels=Channel.query.filter_by(is_emergency=False).count()
        pending=RadioRequest.query.filter_by(status='PENDING_REVIEW').count()
        approved_waiting=RadioRequest.query.filter_by(status='APPROVED').count()
        allocated=RadioRequest.query.filter_by(status='ALLOCATED').count()
        failed=RadioRequest.query.filter(RadioRequest.status.in_(['ALLOCATION_FAILED','REJECTED'])).count()
        today_conflicts=ConflictLog.query.filter_by(allocation_date=today).count()
        used=Allocation.query.filter_by(allocation_date=today).count()
        pct=used/720*100
        recent=AuditLog.query.order_by(AuditLog.created_at.desc()).limit(8).all()
        category_counts=[]
        for cat in ['SECURITY','MEDICAL','EVENTS','MAINTENANCE']:
            category_counts.append((cat,Group.query.filter_by(category=cat,is_active=True).count()))
        return render_template('dashboard_admin.html',total_groups=total_groups,total_users=total_users,pending=pending,
            allocated=allocated,failed=failed,today_conflicts=today_conflicts,used=used,pct=pct,recent=recent,
            active_channels=active_channels,approved_waiting=approved_waiting,
            category_counts=category_counts,today=today)
    group_id=current_user.group_id
    own=RadioRequest.query.filter_by(group_id=group_id)
    own_pending=own.filter_by(status='PENDING_REVIEW').count()
    own_allocated=own.filter_by(status='ALLOCATED').count()
    own_failed=own.filter(RadioRequest.status.in_(['ALLOCATION_FAILED','PREEMPTED','REJECTED'])).count()
    upcoming=own.filter(RadioRequest.request_date>=today).order_by(RadioRequest.request_date,RadioRequest.start_slot).limit(6).all()
    notifications=Notification.query.filter_by(user_id=current_user.id,is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    return render_template('dashboard_group.html',group=current_user.group,own_pending=own_pending,
        own_allocated=own_allocated,own_failed=own_failed,upcoming=upcoming,notifications=notifications)

@main.route('/requests')
@login_required
def request_list():
    q=current_group_scope(RadioRequest.query.join(Group))
    status=request.args.get('status','').strip()
    group=request.args.get('group','').strip()
    date_filter=request.args.get('date','').strip()
    search=request.args.get('q','').strip()
    if status: q=q.filter(RadioRequest.status==status)
    if current_user.is_admin and group: q=q.filter(RadioRequest.group_id==group)
    if date_filter:
        d=safe_date(date_filter,None)
        if d: q=q.filter(RadioRequest.request_date==d)
    if search:
        q=q.filter((RadioRequest.request_code.ilike(f'%{search}%')) | (Group.group_name.ilike(f'%{search}%')))
    items=q.order_by(RadioRequest.submitted_at.desc()).limit(300).all()
    groups=Group.query.order_by(Group.group_name).all() if current_user.is_admin else []
    return render_template('requests.html',items=items,groups=groups,filters={'status':status,'group':group,'date':date_filter,'q':search})

@main.route('/requests/new',methods=['GET','POST'])
@login_required
def request_new():
    groups=Group.query.filter_by(is_active=True).order_by(Group.group_name).all()
    if request.method=='POST':
        group_id=request.form.get('group_id') if current_user.is_admin else current_user.group_id
        group=Group.query.filter_by(group_id=group_id,is_active=True).first()
        try:
            req_date=date.fromisoformat(request.form.get('request_date',''))
            start=int(request.form.get('start_slot','0')); end=int(request.form.get('end_slot','0'))
            count=int(request.form.get('channel_count','0'))
        except (ValueError,TypeError):
            flash('Enter a valid date, slot range and channel count.', 'error')
            return render_template('request_form.html',groups=groups,item=None)
        fixed_raw=request.form.get('fixed_channels','ANY').strip().upper() or 'ANY'
        purpose=request.form.get('purpose','').strip()
        is_emergency=request.form.get('is_emergency')=='on'
        justification=request.form.get('emergency_justification','').strip()
        if not group:
            flash('Select an active group.', 'error')
        elif not current_user.is_admin and group.group_id!=current_user.group_id:
            abort(403)
        elif not purpose:
            flash('Purpose is required.', 'error')
        elif not (1<=start<=end<=48):
            flash('Start and end slots must be between 1 and 48, with start no later than end.', 'error')
        elif end-start+1>8:
            flash('This request exceeds the maximum of 8 inclusive slots (4 hours).', 'error')
        elif count<1 or count>3:
            flash('Channel demand must be between 1 and 3.', 'error')
        elif is_emergency and not current_user.is_admin and not current_user.can_submit_emergency:
            flash('This account is not authorised to submit emergency requests.', 'error')
        elif is_emergency and not justification:
            flash('Emergency requests require a justification.', 'error')
        else:
            try:
                if fixed_raw!='ANY':
                    nums=tuple(int(x.strip()) for x in fixed_raw.replace(',', ';').split(';') if x.strip())
                    if len(nums)!=count or len(set(nums))!=len(nums): raise ValueError()
                    if 16 in nums:
                        flash('Channel 16 is reserved and cannot be requested.', 'error'); return render_template('request_form.html',groups=groups,item=None)
                    if any(n<1 or n>15 for n in nums): raise ValueError()
                    fixed=';'.join(str(x) for x in nums)
                else: fixed='ANY'
            except ValueError:
                flash('Fixed channels must be distinct channel numbers 1–15 and match the channel count.', 'error')
                return render_template('request_form.html',groups=groups,item=None)
            latest= db.session.query(func.max(RadioRequest.submission_sequence)).scalar() or 0
            code=f"WEB-{datetime.utcnow():%y%m%d}-{(latest+1):04d}"
            item=RadioRequest(request_code=code,user_id=current_user.id,group_id=group.group_id,request_date=req_date,
                start_slot=start,end_slot=end,channel_count=count,fixed_channels=fixed,purpose=purpose,
                is_emergency=is_emergency,emergency_justification=justification,
                submission_sequence=latest+1,status='PENDING_REVIEW')
            db.session.add(item); db.session.flush()
            create_event(item,'SUBMITTED','Request submitted from the website.')
            if current_user.is_admin:
                notify(current_user.id,'Request submitted',f'{code} was submitted.')
            else:
                for admin in User.query.filter_by(role='ADMIN',is_active=True).all():
                    notify(admin.id,'New request awaiting review',f'{code} from {group.group_name} requires review.',item.id)
            audit('REQUEST_SUBMITTED','REQUEST',code,'Request submitted from website')
            db.session.commit()
            flash(f'Request {code} submitted for administrator review.', 'success')
            return redirect(url_for('main.request_list'))
    return render_template('request_form.html',groups=groups,item=None)

@main.route('/requests/<int:item_id>/edit',methods=['GET','POST'])
@login_required
def request_edit(item_id):
    item=RadioRequest.query.get_or_404(item_id)
    if not current_user.is_admin and item.group_id!=current_user.group_id: abort(403)
    if item.status!='PENDING_REVIEW' and not (current_user.is_admin and item.status=='APPROVED'):
        flash('Only pending requests can be edited by group users; admins may edit approved requests before allocation.','error')
        return redirect(url_for('main.request_list'))
    groups=Group.query.filter_by(is_active=True).all()
    if request.method=='POST':
        try:
            start=int(request.form['start_slot']); end=int(request.form['end_slot']); count=int(request.form['channel_count'])
            req_date=date.fromisoformat(request.form['request_date'])
        except (KeyError,ValueError):
            flash('Check the date, slot range and channel count.','error'); return render_template('request_form.html',groups=groups,item=item)
        selected_group = item.group
        if current_user.is_admin:
            selected_group = Group.query.filter_by(
                group_id=request.form.get('group_id', item.group_id), is_active=True
            ).first()
        purpose=request.form.get('purpose','').strip()
        fixed_raw=request.form.get('fixed_channels','ANY').strip().upper() or 'ANY'
        is_emergency=request.form.get('is_emergency')=='on'
        justification=request.form.get('emergency_justification','').strip()
        if not (1<=start<=end<=48) or end-start+1>8 or not (1<=count<=3) or not purpose:
            flash('Request validation failed. Use 1–8 inclusive slots, 1–3 channels and a purpose.','error')
        elif current_user.is_admin and selected_group is None:
            flash('Select an active group for this request.','error')
        elif is_emergency and not current_user.is_admin and not current_user.can_submit_emergency:
            flash('This account is not authorised to submit emergency requests.','error')
        elif is_emergency and not justification:
            flash('Emergency requests require a justification.','error')
        else:
            try:
                if fixed_raw=='ANY': fixed='ANY'
                else:
                    nums=[int(x.strip()) for x in fixed_raw.replace(',', ';').split(';') if x.strip()]
                    if 16 in nums:
                        flash('Channel 16 is reserved and cannot be requested.','error')
                        return render_template('request_form.html',groups=groups,item=item)
                    if len(nums)!=count or len(set(nums))!=len(nums) or any(x<1 or x>15 for x in nums): raise ValueError
                    fixed=';'.join(map(str,nums))
            except ValueError:
                flash('Fixed channel list is invalid.','error'); return render_template('request_form.html',groups=groups,item=item)
            before=f"{item.group_id}|{item.request_date}|{item.start_slot}-{item.end_slot}|{item.channel_count}|{item.fixed_channels}|emergency={item.is_emergency}"
            if current_user.is_admin and selected_group is not None:
                item.group = selected_group
            item.request_date=req_date; item.start_slot=start; item.end_slot=end; item.channel_count=count
            item.purpose=purpose; item.fixed_channels=fixed
            item.is_emergency=is_emergency; item.emergency_justification=justification
            create_event(item,'EDITED',f'Previous values: {before}')
            audit('REQUEST_EDITED','REQUEST',item.request_code,'Request updated; previous values: '+before)
            db.session.commit(); flash('Request updated.','success'); return redirect(url_for('main.request_list'))
    return render_template('request_form.html',groups=groups,item=item)

@main.post('/admin/requests/<int:item_id>/approve')
@admin_required
def request_approve(item_id):
    item=RadioRequest.query.get_or_404(item_id)
    if item.status!='PENDING_REVIEW':
        flash('Only pending requests can be approved.','warning')
    else:
        item.status='APPROVED'; item.reviewed_by=current_user.id; item.reviewed_at=datetime.utcnow()
        item.review_comment=request.form.get('comment','').strip()
        create_event(item,'APPROVED',item.review_comment or 'Approved by administrator.')
        notify_group(item.group_id,'Request approved',f'{item.request_code} was approved and is waiting for allocation.',item.id)
        audit('REQUEST_APPROVED','REQUEST',item.request_code,item.review_comment)
        db.session.commit(); flash(f'{item.request_code} approved. Run allocation for its date to assign channels.','success')
    return redirect(request.referrer or url_for('main.request_list'))

@main.post('/admin/requests/<int:item_id>/reject')
@admin_required
def request_reject(item_id):
    item=RadioRequest.query.get_or_404(item_id)
    if item.status!='PENDING_REVIEW': flash('Only pending requests can be rejected.','warning')
    else:
        comment=request.form.get('comment','').strip()
        if not comment: flash('Enter a rejection reason.','error'); return redirect(request.referrer or url_for('main.request_list'))
        item.status='REJECTED'; item.reviewed_by=current_user.id; item.reviewed_at=datetime.utcnow(); item.review_comment=comment
        create_event(item,'REJECTED',comment); notify_group(item.group_id,'Request rejected',f'{item.request_code}: {comment}',item.id)
        audit('REQUEST_REJECTED','REQUEST',item.request_code,comment); db.session.commit(); flash('Request rejected.','success')
    return redirect(request.referrer or url_for('main.request_list'))

@main.post('/admin/requests/<int:item_id>/cancel')
@admin_required
def request_cancel(item_id):
    item=RadioRequest.query.get_or_404(item_id)
    if item.status not in ['ALLOCATED','APPROVED','ALLOCATION_FAILED']:
        flash('This request cannot be cancelled from its current state.','error')
    else:
        removed=Allocation.query.filter_by(request_id=item.id).all()
        snapshot=[{'date':a.allocation_date.isoformat(),'slot':a.slot,'channel':a.channel_no} for a in removed]
        for a in removed: db.session.delete(a)
        item.status='CANCELLED'; create_event(item,'CANCELLED','Cancelled by administrator.')
        db.session.add(AllocationHistory(request_id=item.id,event_type='CANCELLED',snapshot=json.dumps(snapshot),actor_id=current_user.id))
        notify_group(item.group_id,'Request cancelled',f'{item.request_code} was cancelled by an administrator.',item.id)
        audit('REQUEST_CANCELLED','REQUEST',item.request_code,'Admin cancellation')
        db.session.commit(); flash('Request cancelled; its current allocations were removed.','success')
    return redirect(request.referrer or url_for('main.request_list'))

@main.route('/admin/allocation-runs',methods=['GET','POST'])
@admin_required
def allocation_runs():
    if request.method=='POST':
        raw_target=request.form.get('allocation_date','').strip()
        try:
            target=date.fromisoformat(raw_target)
            if target.isoformat()!=raw_target:
                raise ValueError('Use YYYY-MM-DD date format.')
        except ValueError:
            flash('Choose a valid allocation date in YYYY-MM-DD format.','error')
            return redirect(url_for('main.allocation_runs'))
        try:
            # A per-date row lock serialises simultaneous allocation runs for the same schedule.
            schedule_lock=ScheduleLock.query.filter_by(schedule_date=target).with_for_update().first()
            if schedule_lock is None:
                schedule_lock=ScheduleLock(schedule_date=target)
                db.session.add(schedule_lock)
                db.session.flush()
            engine=master_engine()
            pending=RadioRequest.query.filter_by(request_date=target,status='APPROVED').order_by(RadioRequest.submission_sequence,RadioRequest.id).all()
            if not pending:
                flash('There are no approved, unallocated requests for this date.','info'); return redirect(url_for('main.allocation_runs'))
            prior=Allocation.query.filter_by(allocation_date=target).all()
            prior_run_exists=AllocationRun.query.filter_by(allocation_date=target,status='COMPLETED').first() is not None
            run=AllocationRun(allocation_date=target,started_by=current_user.id,run_type='WEB',status='RUNNING')
            db.session.add(run); db.session.flush()
            prior_requests={a.request_id:a.request for a in prior}
            existing_reqs=[request_to_engine(r) for r in prior_requests.values() if r]
            existing_assignments=[Assignment(a.allocation_date.isoformat(),a.slot,a.channel_no,a.group_id,a.request.request_code)
                                  for a in prior if a.request]
            if prior_run_exists:
                engine.add_existing(existing_reqs,existing_assignments)
                new_conflicts=[]
                for item in pending:
                    result=engine.allocate_late(request_to_engine(item))
                    new_conflicts.extend(result.conflicts)
            else:
                result=engine.allocate_initial([request_to_engine(x) for x in pending])
                new_conflicts=result.conflicts
            # Persist the final schedule delta. Existing rows are retained except those removed by pre-emption.
            old_keys={(a.request.request_code,a.slot,a.channel_no):a for a in prior if a.request}
            new_keys={(a.request_id,a.slot,a.channel_no):a for a in engine.assignments if a.date==target.isoformat()}
            for key, old in old_keys.items():
                if key not in new_keys:
                    snapshot=json.dumps({'date':old.allocation_date.isoformat(),'slot':old.slot,'channel':old.channel_no})
                    db.session.add(AllocationHistory(request_id=old.request_id,run_id=run.id,event_type='REMOVED_OR_PREEMPTED',snapshot=snapshot,actor_id=current_user.id))
                    db.session.delete(old)
            request_by_code={r.request_code:r for r in RadioRequest.query.filter(RadioRequest.request_date==target).all()}
            for key, assignment in new_keys.items():
                if key not in old_keys:
                    linked=request_by_code.get(assignment.request_id)
                    if linked:
                        db.session.add(Allocation(run_id=run.id,request_id=linked.id,allocation_date=target,slot=assignment.slot,
                                                  channel_no=assignment.channel_no,group_id=assignment.group_id))
                        db.session.add(AllocationHistory(request_id=linked.id,run_id=run.id,event_type='ASSIGNED',
                            snapshot=json.dumps({'date':target.isoformat(),'slot':assignment.slot,'channel':assignment.channel_no}),actor_id=current_user.id))
            # Statuses for newly processed requests and any pre-empted victims.
            for code,status in engine.statuses.items():
                linked=request_by_code.get(code)
                if linked and status in ['ALLOCATED','ALLOCATION_FAILED','PREEMPTED','MERGED','UNKNOWN_GROUP','DURATION_LIMIT','TOO_MANY_CHANNELS','RESERVED_CHANNEL']:
                    linked.status = status if status in ['ALLOCATED','ALLOCATION_FAILED','PREEMPTED','MERGED'] else 'ALLOCATION_FAILED'
                    if status=='PREEMPTED':
                        notify_group(linked.group_id,'Allocation pre-empted',f'{code} was removed to make room for a higher-priority late request.',linked.id)
                    elif status=='ALLOCATED':
                        notify_group(linked.group_id,'Channels allocated',f'{code} has been allocated.',linked.id)
                    elif status=='ALLOCATION_FAILED':
                        notify_group(linked.group_id,'Allocation unsuccessful',f'{code} could not be allocated for its full interval.',linked.id)
                    elif status=='MERGED':
                        notify_group(linked.group_id,'Request merged',f'{code} was merged with an overlapping request from the same group.',linked.id)
                    create_event(linked,'ALLOCATION_'+status,'Allocation run '+str(run.id))
            for seq, conflict in enumerate(new_conflicts, start=1):
                db.session.add(ConflictLog(run_id=run.id,allocation_date=target,request_code=conflict.request_id,
                    group_id=conflict.group_id,reason=conflict.reason,detail=conflict.detail,sequence_no=seq,
                    message=f"{conflict.reason}: {conflict.request_id}"))
            allocated_req_count=sum(1 for code,s in engine.statuses.items() if s=='ALLOCATED')
            failed_req_count=sum(1 for code,s in engine.statuses.items() if s=='ALLOCATION_FAILED')
            preempted_count=sum(1 for code,s in engine.statuses.items() if s=='PREEMPTED')
            run.status='COMPLETED'; run.completed_at=datetime.utcnow()
            run.summary=f"Allocated statuses: {allocated_req_count}; failed: {failed_req_count}; pre-empted: {preempted_count}; new conflicts: {len(new_conflicts)}"
            audit('ALLOCATION_RUN','ALLOCATION_RUN',run.id,run.summary)
            db.session.commit()
            flash(f"Allocation run completed. {run.summary}",'success')
        except Exception as exc:
            db.session.rollback()
            current_app.logger.exception('Allocation run failed')
            flash(f'Allocation run rolled back: {exc}','error')
        return redirect(url_for('main.allocation_runs'))
    runs=AllocationRun.query.order_by(AllocationRun.started_at.desc()).limit(50).all()
    approved_dates=db.session.query(RadioRequest.request_date).filter_by(status='APPROVED').distinct().order_by(RadioRequest.request_date).all()
    return render_template('allocation_runs.html',runs=runs,approved_dates=[x[0] for x in approved_dates])

@main.route('/schedule')
@login_required
def schedule():
    d=safe_date(request.args.get('date'),date.today())
    rows=Allocation.query.filter_by(allocation_date=d).all()
    if not current_user.is_admin: rows=[a for a in rows if a.group_id==current_user.group_id]
    mapping={(a.slot,a.channel_no):a for a in rows}
    slots=list(range(1,49))
    selected_group=request.args.get('group','') if current_user.is_admin else current_user.group_id
    if selected_group: rows=[a for a in rows if a.group_id==selected_group]
    mapping={(a.slot,a.channel_no):a for a in rows}
    groups=Group.query.order_by(Group.group_name).all() if current_user.is_admin else []
    return render_template('schedule.html',selected_date=d,slots=slots,mapping=mapping,groups=groups,selected_group=selected_group)

@main.route('/admin/channels')
@admin_required
def channels():
    items=Channel.query.order_by(Channel.channel_no).all()
    return render_template('channels.html',items=items)

@main.route('/admin/groups',methods=['GET','POST'])
@admin_required
def groups():
    if request.method=='POST':
        code=request.form.get('group_id','').strip().upper(); name=request.form.get('group_name','').strip()
        category=request.form.get('category','').strip().upper()
        priorities={'SECURITY':1,'MEDICAL':2,'EVENTS':3,'MAINTENANCE':4}
        if not code or not name or category not in priorities:
            flash('Group code, name and valid category are required.','error')
        elif Group.query.get(code): flash('That group code already exists.','error')
        else:
            item=Group(group_id=code,group_name=name,category=category,priority_rank=priorities[category],
                       contact_name=request.form.get('contact_name','').strip(),contact_mobile=request.form.get('contact_mobile','').strip())
            db.session.add(item); audit('GROUP_CREATED','GROUP',code,name); db.session.commit(); flash('Group created.','success')
        return redirect(url_for('main.groups'))
    items=Group.query.order_by(Group.priority_rank,Group.group_name).all()
    return render_template('groups.html',items=items)

@main.post('/admin/groups/<string:group_id>/toggle')
@admin_required
def group_toggle(group_id):
    item=Group.query.get_or_404(group_id); item.is_active=not item.is_active
    audit('GROUP_STATUS_CHANGED','GROUP',group_id,'Active='+str(item.is_active)); db.session.commit()
    flash(f'{group_id} is now {"active" if item.is_active else "inactive"}.','success')
    return redirect(url_for('main.groups'))

@main.route('/admin/groups/<string:group_id>/edit',methods=['GET','POST'])
@admin_required
def group_edit(group_id):
    item=Group.query.get_or_404(group_id)
    if request.method=='POST':
        name=request.form.get('group_name','').strip()
        category=request.form.get('category','').strip().upper()
        priorities={'SECURITY':1,'MEDICAL':2,'EVENTS':3,'MAINTENANCE':4}
        if not name or category not in priorities:
            flash('Group name and valid category are required.','error')
        else:
            item.group_name=name; item.category=category; item.priority_rank=priorities[category]
            item.contact_name=request.form.get('contact_name','').strip()
            item.contact_mobile=request.form.get('contact_mobile','').strip()
            audit('GROUP_UPDATED','GROUP',group_id,f'Name={name}; category={category}')
            db.session.commit(); flash('Group details updated. Existing request history is retained.','success')
            return redirect(url_for('main.groups'))
    return render_template('group_edit.html',item=item)

@main.route('/admin/users',methods=['GET','POST'])
@admin_required
def users():
    groups=Group.query.order_by(Group.group_name).all()
    if request.method=='POST':
        username=request.form.get('username','').strip(); full_name=request.form.get('full_name','').strip()
        password=request.form.get('password',''); role=request.form.get('role','GROUP_USER')
        group_id=request.form.get('group_id') or None
        if not username or not full_name or len(password)<10:
            flash('Full name, username and a password of at least 10 characters are required.','error')
        elif User.query.filter(func.lower(User.username)==username.lower()).first():
            flash('Username already exists.','error')
        elif role not in ['ADMIN','GROUP_USER'] or (role=='GROUP_USER' and not group_id):
            flash('Select a valid role and group.','error')
        elif role=='GROUP_USER' and not Group.query.filter_by(group_id=group_id,is_active=True).first():
            flash('Select an active registered group for this account.','error')
        else:
            u=User(username=username,full_name=full_name,role=role,group_id=(group_id if role=='GROUP_USER' else None),
                   can_submit_emergency=request.form.get('can_submit_emergency')=='on')
            u.set_password(password); db.session.add(u); db.session.flush()
            audit('USER_CREATED','USER',u.id,f'Role={role}; group={group_id}')
            db.session.commit(); flash('User account created.','success')
        return redirect(url_for('main.users'))
    items=User.query.order_by(User.created_at.desc()).all()
    return render_template('users.html',items=items,groups=groups)

@main.post('/admin/users/<int:user_id>/toggle')
@admin_required
def user_toggle(user_id):
    item=User.query.get_or_404(user_id)
    if item.id==current_user.id: flash('You cannot deactivate your own account.','error')
    else:
        item.is_active=not item.is_active; audit('USER_STATUS_CHANGED','USER',item.id,'Active='+str(item.is_active)); db.session.commit()
        flash('User status updated.','success')
    return redirect(url_for('main.users'))

@main.route('/admin/users/<int:user_id>/edit',methods=['GET','POST'])
@admin_required
def user_edit(user_id):
    item=User.query.get_or_404(user_id)
    groups=Group.query.order_by(Group.group_name).all()
    if request.method=='POST':
        full_name=request.form.get('full_name','').strip()
        role=request.form.get('role','GROUP_USER')
        group_id=request.form.get('group_id') or None
        new_password=request.form.get('new_password','')
        if not full_name or role not in ['ADMIN','GROUP_USER'] or (role=='GROUP_USER' and not group_id):
            flash('Provide a name, valid role and assigned group for group users.','error')
        elif role=='GROUP_USER' and not Group.query.filter_by(group_id=group_id,is_active=True).first():
            flash('Select an active registered group for this account.','error')
        elif item.id==current_user.id and role!='ADMIN':
            flash('You cannot remove administrator access from your own active session.','error')
        elif new_password and len(new_password)<10:
            flash('A reset password must contain at least 10 characters.','error')
        else:
            item.full_name=full_name; item.role=role; item.group_id=group_id if role=='GROUP_USER' else None
            item.can_submit_emergency=request.form.get('can_submit_emergency')=='on'
            if new_password:
                item.set_password(new_password); item.failed_login_attempts=0; item.locked_until=None
            audit('USER_UPDATED','USER',item.id,'Account details updated'+('; password reset' if new_password else ''))
            db.session.commit(); flash('User account updated.','success'); return redirect(url_for('main.users'))
    return render_template('user_edit.html',item=item,groups=groups)

@main.route('/admin/conflicts')
@admin_required
def conflicts():
    items=ConflictLog.query.order_by(ConflictLog.created_at.desc(),ConflictLog.sequence_no).limit(500).all()
    return render_template('conflicts.html',items=items)

@main.route('/reports')
@admin_required
def reports():
    d=safe_date(request.args.get('date'),date.today())
    allocations=Allocation.query.filter_by(allocation_date=d).all()
    used,available,pct=utilisation([Assignment(d.isoformat(),a.slot,a.channel_no,a.group_id,a.request.request_code) for a in allocations],d.isoformat())
    statuses={}
    for status in ['PENDING_REVIEW','APPROVED','ALLOCATED','ALLOCATION_FAILED','REJECTED','PREEMPTED','CANCELLED','MERGED']:
        statuses[status]=RadioRequest.query.filter_by(status=status,request_date=d).count()
    category_data=[]
    for cat in ['SECURITY','MEDICAL','EVENTS','MAINTENANCE']:
        count=RadioRequest.query.join(Group).filter(Group.category==cat,RadioRequest.request_date==d).count()
        category_data.append((cat,count))
    return render_template('reports.html',selected_date=d,used=used,available=available,pct=pct,statuses=statuses,category_data=category_data)

@main.get('/reports/official-export')
@admin_required
def official_export():
    # Make exact evaluation outputs from persisted, committed website allocations.
    export_dir=Path(current_app.config['EXPORT_FOLDER'])/'website_latest'; export_dir.mkdir(parents=True,exist_ok=True)
    channels={x.channel_no:x for x in Channel.query.all()}
    dates=set(x[0] for x in db.session.query(Allocation.allocation_date).distinct().all())
    dates.update(x[0] for x in db.session.query(RadioRequest.request_date).distinct().all())
    dates=sorted(dates)
    allocations=Allocation.query.order_by(Allocation.allocation_date,Allocation.slot,Allocation.channel_no).all()
    with (export_dir/'allocation_table.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,lineterminator='\n'); w.writerow(['date','slot','slot_start','channel_no','frequency_mhz','group_id','request_id'])
        for a in allocations: w.writerow([a.allocation_date.isoformat(),a.slot,slot_start(a.slot),a.channel_no,f'{float(channels[a.channel_no].frequency_mhz):.5f}',a.group_id,a.request.request_code])
    with (export_dir/'utilisation.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,lineterminator='\n'); w.writerow(['date','channel_slots_used','channel_slots_available','utilisation_pct'])
        for d in dates:
            used=sum(1 for a in allocations if a.allocation_date==d); w.writerow([d.isoformat(),used,720,f'{used/720*100:.2f}'])
    with (export_dir/'conflict_log.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,lineterminator='\n'); w.writerow(['date','request_id','group_id','reason','detail'])
        for c in ConflictLog.query.order_by(ConflictLog.created_at,ConflictLog.sequence_no).all(): w.writerow([c.allocation_date.isoformat(),c.request_code,c.group_id,c.reason,c.detail])
    audit('OFFICIAL_EXPORT','REPORT','website_latest','Generated three official CSV files')
    db.session.commit()
    return redirect(url_for('main.download_website_exports'))

@main.get('/reports/official-export/download')
@admin_required
def download_website_exports():
    files=['allocation_table.csv','utilisation.csv','conflict_log.csv']
    return render_template('download_exports.html',files=files,folder='website_latest')

@main.get('/downloads/website/<path:filename>')
@admin_required
def download_website_file(filename):
    if filename not in {'allocation_table.csv','utilisation.csv','conflict_log.csv'}: abort(404)
    return send_from_directory(Path(current_app.config['EXPORT_FOLDER'])/'website_latest',filename,as_attachment=True)

@main.route('/admin/command-center',methods=['GET','POST'])
@admin_required
def command_center():
    sample_folder=Path(current_app.config['SAMPLE_DATA_FOLDER'])
    if request.method=='POST':
        mode=request.form.get('mode','upload')
        batch_code=uuid4().hex[:12]
        work_dir=Path(current_app.config['UPLOAD_FOLDER'])/batch_code
        work_dir.mkdir(parents=True,exist_ok=True)
        out_dir=Path(current_app.config['EXPORT_FOLDER'])/batch_code
        try:
            if mode=='sample':
                src=sample_folder
                for name in ['channels.csv','groups.csv','commands.txt']:
                    shutil.copy2(src/name,work_dir/name)
                original='Bundled Team E037 official sample pack'
            else:
                original='Uploaded Team E037 files'
                expected=['commands.txt','channels.csv','groups.csv']
                for name in expected:
                    uploaded=request.files.get(name)
                    if not uploaded or not uploaded.filename:
                        raise ValueError(f'Upload all three files: {", ".join(expected)}.')
                    if Path(uploaded.filename).name!=name:
                        raise ValueError(f'Please upload the file with its original name: {name}.')
                    uploaded.save(work_dir/name)
            result=run_commands(work_dir/'commands.txt',work_dir/'channels.csv',work_dir/'groups.csv',out_dir)
            summary=(f"{result['channels_loaded']} channels; {result['groups_loaded']} groups; "
                     f"{result['requests_submitted']} requests; {result['allocated_rows']} allocation rows; "
                     f"{result['conflicts']} conflict records; {len(result['diagnostics'])} command diagnostics.")
            if result['diagnostics']:
                diagnostic_text='\n'.join(f"Line {d['line']}: {d['error']} | {d['raw']}" for d in result['diagnostics'])
                stored_summary=summary+'\nDiagnostics:\n'+diagnostic_text
            else:
                stored_summary=summary
            batch=ImportBatch(batch_code=batch_code,uploaded_by=current_user.id,original_filename=original,
                              status='COMPLETED' if not result['diagnostics'] else 'COMPLETED_WITH_DIAGNOSTICS',
                              summary=stored_summary,output_dir=str(out_dir))
            db.session.add(batch); audit('COMMAND_FILE_RUN','IMPORT_BATCH',batch_code,summary); db.session.commit()
            flash('Command file processing completed. '+summary,'success')
            return redirect(url_for('main.command_result',batch_code=batch_code))
        except Exception as exc:
            current_app.logger.exception('Command file run failed')
            shutil.rmtree(work_dir,ignore_errors=True)
            shutil.rmtree(out_dir,ignore_errors=True)
            flash(f'Command processing failed: {exc}','error')
    recent=ImportBatch.query.order_by(ImportBatch.created_at.desc()).limit(10).all()
    return render_template('command_center.html',recent=recent)

@main.get('/admin/command-center/<batch_code>')
@admin_required
def command_result(batch_code):
    batch=ImportBatch.query.filter_by(batch_code=batch_code).first_or_404()
    folder=Path(batch.output_dir)
    files=[x for x in ['allocation_table.csv','utilisation.csv','conflict_log.csv'] if (folder/x).exists()]
    return render_template('command_result.html',batch=batch,files=files)

@main.get('/admin/command-center/<batch_code>/download/<filename>')
@admin_required
def command_download(batch_code,filename):
    if filename not in {'allocation_table.csv','utilisation.csv','conflict_log.csv'}: abort(404)
    batch=ImportBatch.query.filter_by(batch_code=batch_code).first_or_404()
    return send_from_directory(batch.output_dir,filename,as_attachment=True)

@main.route('/admin/notifications',methods=['GET','POST'])
@login_required
def notifications():
    if request.method=='POST':
        n=Notification.query.filter_by(id=request.form.get('notification_id'),user_id=current_user.id).first()
        if n: n.is_read=True; db.session.commit()
        return redirect(url_for('main.notifications'))
    items=Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(100).all()
    return render_template('notifications.html',items=items)

@main.get('/admin/audit')
@admin_required
def audit_logs():
    items=AuditLog.query.order_by(AuditLog.created_at.desc()).limit(300).all()
    return render_template('audit.html',items=items)

@main.route('/profile',methods=['GET','POST'])
@login_required
def profile():
    if request.method=='POST':
        current=request.form.get('current_password',''); new=request.form.get('new_password','')
        if not current_user.check_password(current): flash('Current password is incorrect.','error')
        elif len(new)<10: flash('New password must contain at least 10 characters.','error')
        else:
            current_user.set_password(new); audit('PASSWORD_CHANGED','USER',current_user.id,'Self-service password change')
            db.session.commit(); flash('Password changed successfully.','success')
    return render_template('profile.html')

@main.get('/health')
def health():
    return {'status':'ok','application':'Team E037 Campus Walkie-Talkie Engine'},200

@main.get('/health/db')
def health_db():
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return {'status':'ok','database':'connected'},200
    except Exception:
        db.session.rollback(); return {'status':'error','database':'unavailable'},503
