import os
import json
import requests

from google.cloud import storage
from google.auth import app_engine
from google.cloud.storage.bucket import Bucket
from google.cloud.exceptions import NotFound


PROJECT_NAME = 'hyperion'
STORAGE_BUCKET_NAME = 'hyperion_bucket'


def get_oauth2_token():
    credentials = app_engine.Credentials()
    return credentials.token


def get_or_create_storage_bucket():

    client = storage.Client()
    try:
        bucket = client.get_bucket(STORAGE_BUCKET_NAME)
    except NotFound:
        bucket = client.create_bucket(STORAGE_BUCKET_NAME)
        assert isinstance(bucket, Bucket)
    return bucket


bucket = get_or_create_storage_bucket()


def create_or_update_blob(bucket, gae_file_path, **kwargs):

    file = bucket.blob(gae_file_path)
    if file.exists():

        if gae_file_path == 'cron.yaml':
            data = file.download_as_string()
            base_path = os.path.abspath('../gae_hyperion')
            file_path = os.path.join(base_path, 'cron_partial.yaml')
            with open(file_path, 'r') as f:
                data = f.read()
                cron_kwargs = {
                    'url': kwargs.get('url'),
                    'status': kwargs.get('status'),
                    'email': kwargs.get('email'),
                    'schedule': kwargs.get('schedule'),
                }
                new_cron_data = data.format(**cron_kwargs)
            data = '\n'.join([data, new_cron_data])

            blob = storage.Blob(gae_file_path, bucket)
            blob.upload_from_string(data)
    else:
        base_path = os.path.abspath('../gae_hyperion')
        file_path = os.path.join(base_path, gae_file_path)
        with open(file_path, 'r') as f:
            data = f.read()
            if gae_file_path == 'main.py':
                SENDGRID_API_KEY = os.environ['SENDGRID_API_KEY']
                data = data.replace('<SENDGRID_API_KEY>', SENDGRID_API_KEY)
            elif gae_file_path == 'cron.yaml':
                cron_kwargs = {
                    'url': kwargs.get('url'),
                    'status': kwargs.get('status'),
                    'email': kwargs.get('email'),
                    'schedule': kwargs.get('schedule'),
                }
                data = data.format(**cron_kwargs)
        blob = storage.Blob(gae_file_path, bucket)
        blob.upload_from_string(data)
    return file


def get_app_json(files_data):
    bucket = ""
    app_json = {
        "deployment": {
            "files": {}
        },
        "id": "v1",
        "handlers": [{
            "urlRegex": "/.*",
            "script": {
                "scriptPath": "main.app"
            }
        },
        ],
        "runtime": "python27",
        "threadsafe": True,
    }

    for file_name, kwargs in files_data.items():
        file_name_data = {
            "sourceUrl": "https://storage.googleapis.com/%s/%s" % (bucket.id, file_name)
        }
        create_or_update_blob(bucket, file_name, **kwargs)
        app_json["deployment"]["files"][file_name] = file_name_data

    return json.dumps(app_json)


def deploy_to_google_app_engine(files_data):

    proj_id = os.environ.get('PROJECT_ID', 1)
    app_json = get_app_json(files_data)
    token = get_oauth2_token()

    base_url = 'https://appengine.googleapis.com/v1'
    deployment_url = '%s/apps/{proj_id}/services/default/versions' % (base_url)
    deployment_url = deployment_url.format(proj_id=proj_id)

    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-Type": "application/json",
    }
    files = {
        "app.json": app_json
    }
    r1 = requests.post(deployment_url, headers=headers, files=files)
    r1_conform_url = r1.json()['name']
    r2 = requests.get(r1_conform_url, headers=headers)

    return r2.json()['done']
