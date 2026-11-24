from pathlib import Path
import argparse, json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.services.command_runner import run_commands

parser=argparse.ArgumentParser(description='Run Team E037 official commands.txt allocation engine')
parser.add_argument('--commands',default=str(ROOT/'sample_data/team_e037/commands.txt'))
parser.add_argument('--channels',default=str(ROOT/'sample_data/team_e037/channels.csv'))
parser.add_argument('--groups',default=str(ROOT/'sample_data/team_e037/groups.csv'))
parser.add_argument('--output',default=str(ROOT/'exports/official_run'))
args=parser.parse_args()
result=run_commands(Path(args.commands),Path(args.channels),Path(args.groups),Path(args.output))
summary={k:result[k] for k in ['channels_loaded','groups_loaded','requests_submitted','allocated_rows','conflicts','dates','diagnostics','output_dir']}
print(json.dumps(summary,indent=2))
if result['diagnostics']:
    print('One or more command lines could not be processed; inspect diagnostics above.')
    raise SystemExit(2)
