import os
import tempfile
from flask import Flask, request, Response, send_file, make_response
from google.cloud import storage
import google
from frameserve.blueprints.user import user

def create_app():
    app = Flask(__name__)
    app.register_blueprint(user)
    return app


@user.route('/')
def root():
    return 'hi'


@user.route('/images/latest')
def latest():
    api_secret = os.getenv('API_SECRET')
    if not api_secret:
        return Response(status=500)

    authz = request.headers.get('authorization')
    if not authz or authz != api_secret:
        return Response(status=401)

    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    if not project_id:
        return Response(status=500)

    bucket_name = '%s.appspot.com' % project_id
    prefix = 'public/'

    storage_client = storage.Client()
    blobs = storage_client.list_blobs(bucket_name, prefix=prefix, delimiter='/')

    blob = None
    for b in blobs:
        if b.name == prefix:
            continue

        if b.etag in request.if_none_match:
            return Response(status=304)

        blob = b
        break

    if not blob:
        return Response(status=404)

    with tempfile.NamedTemporaryFile() as temp:
        try:
            blob.download_to_filename(temp.name, if_etag_not_match=request.if_none_match)
        except google.api_core.exceptions.NotModified:
            return Response(status=304)


        #TODO mime type from gcs metadata?
        response = make_response(send_file(temp.name, attachment_filename='latest.jpg'))
        response.headers['etag'] = blob.etag
        return response
