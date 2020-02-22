from flask import Flask, render_template, request, redirect, current_app ,jsonify, make_response
from flask import session
from flask.ext.session import Session
import json
from google.cloud import storage, vision
from google.cloud.vision import types
import io
import os
import six
from werkzeug import secure_filename
from werkzeug.exceptions import BadRequest
import datetime
from oauth2client.contrib.flask_util import UserOAuth2
app = Flask(__name__)   

oauth2 = UserOAuth2()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]= "private_key"


@app.route('/')
def login():
    return render_template('visionPage.html')


@app.route('/addimage', methods=['POST'])
def addimage():
    image = request.files['file']
    print(image)
    image_url =upload_image_file(image)
    print(image_url)
    image_url =( "gs://zdjeciowe-wiaderko/"+image_url.split('/')[4])
    imageBucketURL=str(image_url)
    uploadedName= image.filename

    res = make_response(jsonify({"imageBucketURL":imageBucketURL}), 200)
    return res 


@app.route('/printlabels', methods=['GET', 'POST'])
def printlabels():
    imageBucketURL = request.form['imageBucketURL']
    print(imageBucketURL)
    labels = detect_labels_uri(imageBucketURL)
    print(labels)
    listlabels = []
    for label in labels:
        listlabels.append(label.description)
    print(listlabels)
    res = make_response(jsonify({"list":listlabels}), 200)
    print(res)
    return res 



def upload_image_file(file):
    """
    Upload the user-uploaded file to Google Cloud Storage and retrieve its
    publicly-accessible URL.
    """
    if not file:
        return None

    public_url = upload_file(
        file.read(),
        file.filename,
        file.content_type
    )

    return public_url


def detect_labels_uri(uri):
    """Detects labels in the file located in Google Cloud Storage or on the
    Web."""
    
    client = vision.ImageAnnotatorClient()
    image = vision.types.Image()
    image.source.image_uri = uri

    response = client.label_detection(image=image)
    labels = response.label_annotations
    print('Labels:')

    

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

    return labels


def upload_file(file_stream, filename, content_type):
    """
    Uploads a file to a given Cloud Storage bucket and returns the public url
    to the new object.
    """
    _check_extension(filename, ('jpg', 'png'))
    filename = _safe_filename(filename)

    client = _get_storage_client()
    bucket = client.bucket('zdjeciowe-wiaderko')
    blob = bucket.blob(filename)

    blob.upload_from_string(
        file_stream,
        content_type=content_type)

    url = blob.public_url

    if isinstance(url, six.binary_type):
        url = url.decode('utf-8')

    return url


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )


def _get_storage_client():
    return storage.Client(
        project='visionproject-266515')


def _check_extension(filename, allowed_extensions):
    if ('.' not in filename or
            filename.split('.').pop().lower() not in allowed_extensions):
        raise BadRequest(
            "{0} has an invalid name or extension".format(filename))


def _safe_filename(filename):
    """
    Generates a safe filename that is unlikely to collide with existing objects
    in Google Cloud Storage.

    ``filename.ext`` is transformed into ``filename-YYYY-MM-DD-HHMMSS.ext``
    """
    filename = secure_filename(filename)
    date = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H%M%S")
    basename, extension = filename.rsplit('.', 1)
    return "{0}-{1}.{2}".format(basename, date, extension)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)