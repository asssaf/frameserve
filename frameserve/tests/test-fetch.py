import os
import pytest
from frameserve.frameserve import create_app


@pytest.fixture()
def app():
    os.environ['GOOGLE_CLOUD_PROJECT'] = 'frameserve'
    os.environ['API_SECRET'] = 'foobarsecret'
    app = create_app()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_fetch_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"hi" in response.data


def test_fetch_latest(client):
    headers = {}
    path = '/images/latest'

    # no authorization
    response = client.head(path, headers=headers)
    assert response.status_code == 401

    # bad authorization
    headers['Authorization'] = 'bad'
    response = client.head(path, headers=headers)
    assert response.status_code == 401

    # good authrization
    headers['Authorization'] = os.environ['API_SECRET']
    response = client.head(path, headers=headers)
    assert response.status_code == 200
    etag = response.headers['etag']
    assert etag
    assert response.content_length > 0

    content_disposition = response.headers.get('Content-Disposition')
    assert content_disposition == 'inline; filename=latest.bin'

    # if not changed a 304 is returned
    headers['If-None-Match'] = etag
    response = client.head(path, headers=headers)
    assert response.status_code == 304
    assert not response.content_length

    # if changed a 200 is returned
    headers['If-None-Match'] = etag + "123"
    response = client.head(path, headers=headers)
    assert response.status_code == 200
    assert response.content_length > 0
