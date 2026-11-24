from pathlib import Path
from config import Config

def create_app(test_config=None):
    # Flask dependencies are imported only when a web app is requested. The standalone
    # command-line allocator can therefore run without importing the web framework.
    from flask import Flask
    from .extensions import db, login_manager, csrf, migrate
    from .models import User
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
    Path(app.config['EXPORT_FOLDER']).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = 'main.login'
    login_manager.init_app(app)
    @login_manager.user_loader
    def load_user(user_id):
        user = db.session.get(User, int(user_id))
        return user if user and user.is_active else None
    csrf.init_app(app)
    from .routes import main
    app.register_blueprint(main)
    @app.context_processor
    def inject_globals():
        return {'project_title': 'Campus Walkie-Talkie Channel and Time-Slot Allocation Engine'}
    @app.errorhandler(403)
    def forbidden(_error):
        from flask import render_template
        return render_template('error.html', code=403, message='You do not have permission to access this page.'), 403
    @app.errorhandler(404)
    def not_found(_error):
        from flask import render_template
        return render_template('error.html', code=404, message='The requested page could not be found.'), 404
    @app.errorhandler(413)
    def too_large(_error):
        from flask import flash, redirect, url_for
        flash('Upload exceeds the 12 MB limit.', 'error')
        return redirect(url_for('main.command_center'))
    return app
