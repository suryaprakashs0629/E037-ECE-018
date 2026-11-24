from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT/'.env')
from app import create_app
from app.extensions import db
from app.models import Channel, Group
from app.services.command_runner import load_channels, load_groups

app=create_app()
with app.app_context():
    db.create_all()
    sample=ROOT/'sample_data'/'team_e037'
    channels=load_channels(sample/'channels.csv')
    groups=load_groups(sample/'groups.csv')
    for item in channels:
        obj=db.session.get(Channel,item.channel_no)
        if obj is None:
            db.session.add(Channel(channel_no=item.channel_no,frequency_mhz=item.frequency_mhz,
                                   spacing_khz=item.spacing_khz,is_emergency=item.is_emergency))
        else:
            obj.frequency_mhz=item.frequency_mhz; obj.spacing_khz=item.spacing_khz; obj.is_emergency=item.is_emergency
    for item in groups:
        obj=db.session.get(Group,item.group_id)
        if obj is None:
            db.session.add(Group(group_id=item.group_id,group_name=item.group_name,category=item.category,
                                 priority_rank=item.priority_rank,contact_name=item.contact_name,
                                 contact_mobile=item.contact_mobile,is_active=True))
        else:
            obj.group_name=item.group_name; obj.category=item.category; obj.priority_rank=item.priority_rank
            obj.contact_name=item.contact_name; obj.contact_mobile=item.contact_mobile
    db.session.commit()
    print(f'Database ready. Loaded {len(channels)} channels and {len(groups)} official groups.')
