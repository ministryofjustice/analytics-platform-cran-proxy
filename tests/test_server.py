#!/usr/bin/env python
import io
import os
import shutil
import tarfile
import tempfile
from pathlib import Path

import pytest
from aioresponses import aioresponses
from urlobject.path import URLPath

DIR = Path(os.path.dirname(__file__))


def tarify(buf, path: Path):
    with tarfile.open("file.tar.gz", "w:gz", fileobj=buf) as tf:
        tf.add(path, arcname="DESCRIPTION")
        tf.close()
    buf.seek(0)


@pytest.fixture
def r_package_binary():
    buf = io.BytesIO()
    tarify(buf, DIR / Path("fixtures/DESCRIPTION_BINARY"))
    yield buf.read()
    buf.close()


@pytest.fixture
def r_package():
    buf = io.BytesIO()
    tarify(buf, DIR / Path("fixtures/DESCRIPTION_NON_BINARY"))
    yield buf.read()
    buf.close()


@pytest.fixture
def app():
    from server import app

    listeners = app.listeners
    app.config.OUTPUT_BINARY_PATH = Path(tempfile.mkdtemp())
    # clear the compiler listener because that will
    # cause the tests to hang forever.
    listeners["after_server_start"] = []
    yield app
    shutil.rmtree(app.config.OUTPUT_BINARY_PATH, ignore_errors=True)


@pytest.fixture
def mock_aioresponse():
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        yield m


def test_healthcheck(app):
    request, response = app.test_client.get("/healthz")
    assert response.status == 200


def test_get_packages(app, mock_aioresponse):
    packages_index_path = URLPath("/src/contrib/PACKAGES")
    remote_path = app.config.UPSTREAM_CRAN_SERVER_URL.add_path(packages_index_path)
    mock_aioresponse.get(remote_path, status=200)

    request, response = app.test_client.get(packages_index_path)

    assert response.status == 200
    reqs = {k: v for k, v in mock_aioresponse.requests}

    # check that remote request was made
    remote_req = reqs["GET"]
    assert len(reqs) == 1

    assert remote_req.path_qs == packages_index_path


def test_get_single_binary_package(app, mock_aioresponse, r_package_binary):
    package_path = URLPath("/src/contrib/later_0.7.5.tar.gz")
    remote_path = app.config.UPSTREAM_CRAN_SERVER_URL.add_path(package_path)
    mock_aioresponse.get(remote_path, status=200, body=r_package_binary)

    request, response = app.test_client.get(package_path, allow_redirects=False)
    assert response.status == 302
    assert response.headers["location"] == remote_path
    assert not app.compile_queue.empty()


def test_get_single_src_package(app, mock_aioresponse, r_package):
    package_path = URLPath("/src/contrib/latest_0.7.5.tar.gz")
    remote_path = app.config.UPSTREAM_CRAN_SERVER_URL.add_path(package_path)
    mock_aioresponse.get(remote_path, status=200, body=r_package)

    request, response = app.test_client.get(package_path, allow_redirects=False)
    assert response.status == 302
    assert response.headers["location"] == remote_path

    # if it's a non binary r package then don't add to the compile queue
    assert app.compile_queue.empty()
