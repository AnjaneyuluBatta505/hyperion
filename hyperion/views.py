from flask import render_template, request, flash
from . import app
from .forms import WatcherForm
from .gae_utils import deploy_to_google_app_engine


@app.route("/", methods=['GET', 'POST'])
def home():
    form = WatcherForm()
    if request.method == 'POST' and form.validate_on_submit():
        files_data = {
            'app.yaml': {},
            'cron.yaml': {
                'url': form.data.get('url'),
                'status': form.data.get('status'),
                'email': form.data.get('email'),
                'schedule': form.data.get('schedule'),
            },
            'main.py': {},
            'requirements.txt': {},
        }
        result = deploy_to_google_app_engine(files_data)
        if result:
            flash('Successfull created a watcher in google cloud appengine')
        else:
            flash('Failed to create a watcher in google cloud appengine')

    context = {
        'form': form
    }
    return render_template('home.html', **context)
