"""Official Team E037 commands.txt processor and exact CSV writer."""
from __future__ import annotations
import csv
from datetime import date as date_type
from pathlib import Path
from typing import Dict, List, Optional
from .allocation_engine import AllocationEngine, Assignment, Channel, Conflict, Group, Request, slot_start, utilisation

class CommandFileError(Exception):
    pass


def load_channels(path: Path) -> List[Channel]:
    rows=[]
    try:
        with path.open(newline='', encoding='utf-8-sig') as f:
            reader=csv.DictReader(f)
            required={'channel_no','frequency_mhz','spacing_khz','is_emergency'}
            if not required.issubset(reader.fieldnames or []):
                raise CommandFileError(f"{path.name}: missing columns {sorted(required-set(reader.fieldnames or []))}")
            for line_no, row in enumerate(reader, start=2):
                n=int(row['channel_no'])
                emergency=row['is_emergency'].strip().lower()=='true'
                if emergency != (n == 16):
                    raise CommandFileError(f"{path.name}:{line_no}: is_emergency must be true only for channel 16")
                rows.append(Channel(n, row['frequency_mhz'].strip(), row['spacing_khz'].strip(), emergency))
    except (OSError, ValueError, AttributeError) as exc:
        if isinstance(exc, CommandFileError): raise
        raise CommandFileError(f"{path.name}: invalid channel master data: {exc}") from exc
    if sorted(x.channel_no for x in rows) != list(range(1,17)):
        raise CommandFileError(f"{path.name}: expected channels 1 through 16 exactly once")
    return rows


def load_groups(path: Path) -> List[Group]:
    rows=[]
    expected={'SECURITY':1,'MEDICAL':2,'EVENTS':3,'MAINTENANCE':4}
    try:
        with path.open(newline='', encoding='utf-8-sig') as f:
            reader=csv.DictReader(f)
            required={'group_id','group_name','category','priority_rank','contact_name','contact_mobile'}
            if not required.issubset(reader.fieldnames or []):
                raise CommandFileError(f"{path.name}: missing columns {sorted(required-set(reader.fieldnames or []))}")
            for line_no, row in enumerate(reader, start=2):
                group_id=row['group_id'].strip()
                group_name=row['group_name'].strip()
                category=row['category'].strip().upper()
                rank=int(row['priority_rank'])
                mobile=(row.get('contact_mobile') or '').strip()
                if not group_id or not group_name:
                    raise CommandFileError(f"{path.name}:{line_no}: group_id and group_name are required")
                if category not in expected or rank != expected[category]:
                    raise CommandFileError(f"{path.name}:{line_no}: invalid category/priority pair")
                if mobile and (len(mobile)!=10 or not mobile.isdigit() or mobile[0] not in '6789'):
                    raise CommandFileError(f"{path.name}:{line_no}: contact_mobile must be a 10-digit number starting 6–9")
                rows.append(Group(group_id, group_name, category, rank, row.get('contact_name',''), mobile))
    except (OSError, ValueError, AttributeError) as exc:
        if isinstance(exc, CommandFileError): raise
        raise CommandFileError(f"{path.name}: invalid group master data: {exc}") from exc
    ids=[x.group_id for x in rows]
    if len(ids)!=len(set(ids)):
        raise CommandFileError(f"{path.name}: group_id values must be unique")
    return rows


def run_commands(commands_path: Path, channels_path: Optional[Path]=None, groups_path: Optional[Path]=None, output_dir: Optional[Path]=None) -> Dict:
    commands_path=Path(commands_path).resolve()
    output_dir=Path(output_dir or commands_path.parent/'outputs').resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    engine: Optional[AllocationEngine]=None
    channels=[]; groups=[]
    pending: Dict[str,List[Request]]={}
    allocated_dates=set()
    sequence=0
    printed_dates=set()
    diagnostics=[]
    command_trace=[]
    seen_request_ids=set()

    def validate_date(value: str) -> str:
        parsed=date_type.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError('Date must use YYYY-MM-DD format')
        return value

    def resolve_master(argument: str, fallback: Optional[Path]) -> Path:
        # Master names are file names inside the batch directory, never arbitrary paths.
        if Path(argument).name != argument or argument in {'.', '..'} or '/' in argument or '\\' in argument:
            raise CommandFileError('Master file argument must be a simple filename in the uploaded batch.')
        candidate=(commands_path.parent/argument).resolve()
        if candidate.exists(): return candidate
        if fallback and Path(fallback).exists(): return Path(fallback).resolve()
        raise CommandFileError(f"Master file not found: {argument}")

    with commands_path.open(encoding='utf-8-sig') as stream:
        for line_no, raw in enumerate(stream, start=1):
            line=raw.strip()
            if not line or line.startswith('#'):
                continue
            parts=[x.strip() for x in line.split('|')]
            command=parts[0].upper()
            try:
                if command=='LOAD_CHANNELS':
                    if len(parts)!=2: raise ValueError('LOAD_CHANNELS expects one filename')
                    channels=load_channels(resolve_master(parts[1], channels_path))
                    command_trace.append({'line':line_no,'command':command,'status':'loaded'})
                elif command=='LOAD_GROUPS':
                    if len(parts)!=2: raise ValueError('LOAD_GROUPS expects one filename')
                    groups=load_groups(resolve_master(parts[1], groups_path))
                    command_trace.append({'line':line_no,'command':command,'status':'loaded'})
                elif command=='REQUEST':
                    if len(parts)!=8: raise ValueError('REQUEST expects 7 arguments')
                    if engine is None:
                        if not channels or not groups: raise ValueError('LOAD_CHANNELS and LOAD_GROUPS must precede REQUEST')
                        engine=AllocationEngine(channels, groups)
                    if parts[1] in seen_request_ids:
                        raise ValueError(f'Duplicate request_id {parts[1]}')
                    request_date=validate_date(parts[3])
                    fixed=None if parts[7].upper()=='ANY' else tuple(int(v.strip()) for v in parts[7].split(';'))
                    sequence+=1
                    req=Request(parts[1],parts[2],request_date,int(parts[4]),int(parts[5]),int(parts[6]),fixed,sequence)
                    seen_request_ids.add(parts[1])
                    if req.date in allocated_dates:
                        result=engine.allocate_late(req)
                        # For CLI, retain late outcome in the in-memory result and trace.
                        status=engine.statuses.get(req.request_id, 'UNKNOWN')
                    else:
                        pending.setdefault(req.date,[]).append(req)
                        status='QUEUED'
                    command_trace.append({'line':line_no,'command':command,'request_id':parts[1],'status':status})
                elif command=='ALLOCATE':
                    if len(parts)!=2: raise ValueError('ALLOCATE expects one YYYY-MM-DD date')
                    if engine is None: raise ValueError('Load master files before ALLOCATE')
                    date=validate_date(parts[1])
                    if date in allocated_dates: raise ValueError(f'{date} has already been allocated')
                    engine.allocate_initial(pending.get(date,[]))
                    allocated_dates.add(date); printed_dates.add(date)
                    command_trace.append({'line':line_no,'command':command,'date':date,'status':'completed'})
                elif command=='PRINT_TABLE':
                    if len(parts)!=2: raise ValueError('PRINT_TABLE expects a date')
                    printed_date=validate_date(parts[1])
                    printed_dates.add(printed_date); command_trace.append({'line':line_no,'command':command,'date':printed_date,'status':'queued'})
                elif command=='PRINT_UTILISATION':
                    if len(parts)!=2: raise ValueError('PRINT_UTILISATION expects a date')
                    printed_date=validate_date(parts[1])
                    printed_dates.add(printed_date); command_trace.append({'line':line_no,'command':command,'date':printed_date,'status':'queued'})
                elif command=='PRINT_CONFLICTS':
                    if len(parts)!=2 or parts[1].upper()!='ALL': raise ValueError('PRINT_CONFLICTS expects ALL')
                    command_trace.append({'line':line_no,'command':command,'status':'queued'})
                else:
                    raise ValueError(f'Unknown command {command}')
            except Exception as exc:
                diagnostics.append({'line':line_no,'raw':raw.rstrip('\r\n'),'error':str(exc)})

    if engine is None:
        raise CommandFileError('No valid LOAD_CHANNELS / LOAD_GROUPS / REQUEST sequence was processed.')

    assignments=sorted(engine.assignments, key=lambda a:(a.date,a.slot,a.channel_no))
    conflicts=list(engine.conflicts)
    output_dir.mkdir(parents=True, exist_ok=True)
    # Exact evaluator output headers and ordering.
    with (output_dir/'allocation_table.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f, lineterminator='\n')
        w.writerow(['date','slot','slot_start','channel_no','frequency_mhz','group_id','request_id'])
        for a in assignments:
            ch=engine.channels[a.channel_no]
            w.writerow([a.date,a.slot,slot_start(a.slot),a.channel_no,f"{float(ch.frequency_mhz):.5f}",a.group_id,a.request_id])
    dates=sorted(printed_dates | allocated_dates)
    with (output_dir/'utilisation.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,lineterminator='\n'); w.writerow(['date','channel_slots_used','channel_slots_available','utilisation_pct'])
        for date in dates:
            used,available,pct=utilisation(assignments,date)
            w.writerow([date,used,available,pct])
    with (output_dir/'conflict_log.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,lineterminator='\n'); w.writerow(['date','request_id','group_id','reason','detail'])
        for c in conflicts:
            w.writerow([c.date,c.request_id,c.group_id,c.reason,c.detail])
    return {
        'channels_loaded':len(channels),'groups_loaded':len(groups),
        'requests_submitted':sequence,'allocated_rows':len(assignments),
        'conflicts':len(conflicts),'dates':dates,'diagnostics':diagnostics,
        'trace':command_trace,'assignments':assignments,'conflict_rows':conflicts,
        'output_dir':str(output_dir),'statuses':dict(engine.statuses)
    }
