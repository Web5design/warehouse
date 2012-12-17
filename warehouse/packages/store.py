from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import hashlib
import os

import flask

from sqlalchemy.orm.exc import NoResultFound

from warehouse import db
from warehouse.packages.models import (
                                    Classifier,
                                    Project,
                                    Version,
                                    File,
                                    FileType,
                                )
from warehouse.utils import ropen


def classifier(trove):
    try:
        c = Classifier.query.filter_by(trove=trove).one()
    except NoResultFound:
        c = Classifier(trove)
        db.session.add(c)

    return c


def project(name):
    try:
        project = Project.query.filter_by(name=name).one()

        # This object already exists, so if yanked is True we need to make it
        #   "new"
        if project.yanked:
            db.session.delete(project)
            db.session.flush()
            project = None
    except NoResultFound:
        project = None

    if project is None:
        project = Project(name)

    db.session.add(project)

    return project


def version(project, release):
    try:
        version = Version.query.filter_by(project=project,
                                          version=release["version"]).one()

        # This object already exists, so if yanked is True we need to make it
        #   "new"
        if version.yanked:
            db.session.delete(version)
            db.session.flush()
            version = None
    except NoResultFound:
        version = None

    if version is None:
        version = Version(project=project, version=release["version"])

    version.summary = release.get("summary", "")
    version.description = release.get("description", "")

    version.author = release.get("author", "")
    version.author_email = release.get("author_email", "")

    version.maintainer = release.get("maintainer", "")
    version.maintainer_email = release.get("maintainer_email", "")

    version.license = release.get("license", "")

    version.requires_python = release.get("requires_python", "")
    version.requires_external = release.get("requires_external", [])

    # We cannot use the association proxy here because of a bug, and because
    #   of a race condition in multiple green threads.
    #   See: https://github.com/mitsuhiko/flask-sqlalchemy/issues/112
    version._classifiers = [Classifier.query.filter_by(trove=t).one()
                                for t in release.get("classifiers", [])]

    version.keywords = release.get("keywords", [])

    version.uris = release.get("uris", {})

    version.download_uri = release.get("download_uri", "")

    db.session.add(version)

    return version


def distribution(project, version, dist):
    try:
        vfile = File.query.filter_by(version=version,
                                     filename=dist["filename"]).one()

        # This object already exists, so if yanked is True we need to make it
        #   "new"
        if vfile.yanked:
            db.session.delete(vfile)
            db.session.flush()
            vfile = None
    except NoResultFound:
        vfile = None

    if vfile is None:
        vfile = File(version=version, filename=dist["filename"])

    vfile.filesize = dist["filesize"]
    vfile.python_version = dist["python_version"]

    vfile.type = FileType.from_string(dist["type"])

    vfile.comment = dist.get("comment", "")

    db.session.add(vfile)

    return vfile


def distribution_file(project, version, distribution, dist_file):
    app = flask.current_app

    # Generate all the hashes for this file
    hashes = {}
    for algorithm in hashlib.algorithms:
        hashes[algorithm] = getattr(hashlib, algorithm)(dist_file).hexdigest()

    parts = []
    # If we have a hash selected include it in the filename parts
    if app.config.get("STORAGE_HASH"):
        parts += list(hashes[app.config["STORAGE_HASH"]][:5])
        parts += [hashes[app.config["STORAGE_HASH"]]]
    # Finally end the filename parts with the actual filename
    parts += [distribution.filename]

    # Join together the parts to get the final filename
    filename = os.path.join(*parts)

    # Open the file with the redirected open (ropen) and save the contents
    with ropen(filename, "w") as fp:
        fp.write(dist_file)

    # Set the hashes and filename for the distribution
    distribution.hashes = hashes
    distribution.file = filename
