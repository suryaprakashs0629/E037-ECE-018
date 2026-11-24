from pathlib import Path
import sys, getpass
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT/'.env')
from app import create_app
from app.extensions import db
from app.models import User

app=create_app()
with app.app_context():
    db.create_all()
    username=input('Administrator username: ').strip()
    full_name=input('Administrator full name: ').strip()
    while True:
        password=getpass.getpass('Password (minimum 10 characters): ')
        confirm=getpass.getpass('Confirm password: ')
        if len(password)<10: print('Use at least 10 characters.'); continue
        if password!=confirm: print('Passwords do not match.'); continue
        break
    if User.query.filter_by(username=username).first():
        print('That username already exists.'); raise SystemExit(1)
    user=User(username=username,full_name=full_name,role='ADMIN',group_id=None,is_active=True)
    user.set_password(password)
    db.session.add(user); db.session.commit()
    print(f'Administrator account created: {username}')
