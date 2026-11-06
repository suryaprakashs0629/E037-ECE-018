from pathlib import Path
import csv
import pytest
from app.services.command_runner import run_commands, load_channels, load_groups
from app.services.allocation_engine import AllocationEngine, Request

ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'sample_data'/'team_e037'

@pytest.fixture
def masters():
    return load_channels(PACK/'channels.csv'), load_groups(PACK/'groups.csv')

def test_official_pack_runs_without_command_diagnostics(tmp_path):
    result=run_commands(PACK/'commands.txt',PACK/'channels.csv',PACK/'groups.csv',tmp_path)
    assert result['channels_loaded']==16
    assert result['groups_loaded']==15
    assert result['requests_submitted']==128
    assert result['dates']==['2026-10-12','2026-10-13','2026-10-14']
    assert result['diagnostics']==[]
    for name in ['allocation_table.csv','utilisation.csv','conflict_log.csv']:
        assert (tmp_path/name).is_file()

def test_official_output_headers_exact(tmp_path):
    run_commands(PACK/'commands.txt',PACK/'channels.csv',PACK/'groups.csv',tmp_path)
    expected={
      'allocation_table.csv':['date','slot','slot_start','channel_no','frequency_mhz','group_id','request_id'],
      'utilisation.csv':['date','channel_slots_used','channel_slots_available','utilisation_pct'],
      'conflict_log.csv':['date','request_id','group_id','reason','detail']}
    for filename,header in expected.items():
        with (tmp_path/filename).open(newline='') as f:
            assert next(csv.reader(f))==header

def test_official_planted_scenarios(tmp_path):
    result=run_commands(PACK/'commands.txt',PACK/'channels.csv',PACK/'groups.csv',tmp_path)
    status=result['statuses']
    assert status['REQ-0105']=='ALLOCATED'          # exactly 8 slots
    assert status['REQ-0108']=='DURATION_LIMIT'     # 9 slots
    assert status['REQ-0115']=='RESERVED_CHANNEL'   # fixed channel 16
    assert status['REQ-0116']=='ALLOCATED'          # fixed channel 6 works
    assert status['REQ-0121']=='TOO_MANY_CHANNELS'  # 4 channels
    assert status['REQ-0126']=='UNKNOWN_GROUP'      # unknown master group
    assert status['REQ-0078']=='MERGED'             # same-group overlap
    assert status['REQ-0062']=='PREEMPTED'          # late Security pre-emption
    assert status['REQ-0083']=='ALLOCATED'
    assert status['REQ-0031']=='ALLOCATION_FAILED' # 14/15 adjacency trap
    # Same-group adjacent channels are allowed.
    a=[x.channel_no for x in result['assignments'] if x.request_id=='REQ-0023' and x.slot==34]
    assert a==[11,12]
    # Continuity after a clash: moves to channel 3 and retains it.
    by_slot={x.slot:x.channel_no for x in result['assignments'] if x.request_id=='REQ-0032'}
    assert by_slot=={24:1,25:1,26:3,27:3,28:3,29:3}
    # The initial request on the 13th allocates without pre-emption; only the later saturated request pre-empts.
    assert not any(c.request_id=='REQ-0042' for c in result['conflict_rows'])
    assert any(c.request_id=='REQ-0062' and c.reason=='PREEMPTED' and c.detail=='REQ-0083' for c in result['conflict_rows'])
    # Late Security takes channel 14 after the Maintenance reservation is removed.
    assert {(x.slot,x.channel_no) for x in result['assignments'] if x.request_id=='REQ-0083'}=={(20,14),(21,14)}

def test_inclusive_duration_boundaries():
    channels=load_channels(PACK/'channels.csv'); groups=load_groups(PACK/'groups.csv')
    engine=AllocationEngine(channels,groups)
    group='GRP-01'
    eight=Request('T8',group,'2026-11-01',18,25,1,None,1)
    nine=Request('T9',group,'2026-11-01',18,26,1,None,2)
    assert engine.validate(eight) is None
    assert engine.validate(nine).reason=='DURATION_LIMIT'

def test_reserved_channel_validation(masters):
    channels,groups=masters; engine=AllocationEngine(channels,groups)
    req=Request('R16','GRP-06','2026-11-01',1,2,1,(16,),1)
    assert engine.validate(req).reason=='RESERVED_CHANNEL'

def test_no_partial_assignment_when_one_slot_fails():
    channels=load_channels(PACK/'channels.csv')
    groups=load_groups(PACK/'groups.csv')
    engine=AllocationEngine(channels,groups)
    # Seed channels 1,3,...,13 in slot 2; a two-slot fixed request can use 15 in slot 1,
    # but it must fail at slot 2 where fixed channel 14 is adjacent to channel 13.
    seed=[]
    from app.services.allocation_engine import Assignment
    for n,g in [(1,'GRP-01'),(3,'GRP-02'),(5,'GRP-03'),(7,'GRP-04'),(9,'GRP-05'),(11,'GRP-06'),(13,'GRP-07')]:
        seed.append(Assignment('2026-11-02',2,n,g,f'SEED-{n}'))
    engine.assignments=seed
    req=Request('ATOMIC','GRP-08','2026-11-02',1,2,1,(14,),99)
    planned,failed=engine._plan_request(req,engine.assignments)
    assert planned is None
    assert failed==2
    assert all(a.request_id!='ATOMIC' for a in engine.assignments)

def test_utilisation_uses_unique_committed_channel_slots(tmp_path):
    run_commands(PACK/'commands.txt',PACK/'channels.csv',PACK/'groups.csv',tmp_path)
    with (tmp_path/'utilisation.csv').open(newline='') as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==3
    assert all(int(row['channel_slots_available'])==720 for row in rows)
    assert all(0 <= float(row['utilisation_pct']) <= 100 for row in rows)

def test_outputs_are_deterministic_for_same_official_input(tmp_path):
    out_a = tmp_path / 'run_a'
    out_b = tmp_path / 'run_b'
    run_commands(PACK/'commands.txt', PACK/'channels.csv', PACK/'groups.csv', out_a)
    run_commands(PACK/'commands.txt', PACK/'channels.csv', PACK/'groups.csv', out_b)
    for name in ('allocation_table.csv', 'utilisation.csv', 'conflict_log.csv'):
        assert (out_a/name).read_bytes() == (out_b/name).read_bytes()


def test_command_runner_reports_bad_date_and_duplicate_request_id(tmp_path):
    commands = tmp_path / 'commands.txt'
    commands.write_text(
        'LOAD_CHANNELS|channels.csv\n'
        'LOAD_GROUPS|groups.csv\n'
        'REQUEST|R-1|GRP-01|2026-10-12|1|1|1|ANY\n'
        'REQUEST|R-1|GRP-01|2026-10-12|2|2|1|ANY\n'
        'REQUEST|R-2|GRP-01|2026-02-30|1|1|1|ANY\n'
        'ALLOCATE|2026-10-12\n', encoding='utf-8')
    result = run_commands(commands, PACK/'channels.csv', PACK/'groups.csv', tmp_path/'out')
    assert len(result['diagnostics']) == 2
    assert 'Duplicate request_id' in result['diagnostics'][0]['error']
    assert 'day is out of range' in result['diagnostics'][1]['error']
