from flask import Flask, jsonify, redirect, url_for, render_template, request, Response
from flask_cors import CORS
from PIL import Image
from io import BytesIO
from s3_manager import upload_to_s3
from database import init_db, get_db, add_image_to_db, delete_media
from models import Media
import os
import mimetypes
import requests
import uuid

app = Flask(__name__)

MAX_SIZE_MB = 2
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024

allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5000").split(",")
CORS(app, resources={
    r"/*": {
        "origins": [o.strip() for o in allowed_origins if o.strip()],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

"""

HELP: The image processor doesn't appear to be compressing images properly.

"""
def process_image(file):
    img = Image.open(file)
    fmt = img.format

    quality = 95
    min_quality = 20
    step = 5

    while True:
        buffer = BytesIO()
        img.save(buffer, format=fmt, quality=quality)
        data = buffer.getvalue()
        if len(data) <= MAX_SIZE_BYTES or quality <= min_quality:
            break
        quality -= step
    
    # If still too large, start reducing size
    while len(data) > MAX_SIZE_BYTES:
        width, height = img.size
        img = img.resize((width // 2, height // 2))
        buffer = BytesIO()
        img.save(buffer, format=fmt, quality=quality)
        data = buffer.getvalue()

    img.save(buffer, format=fmt)
    size = buffer.tell() / (1024 * 1024)

    return data, Image.MIME[fmt], size

@app.route("/health")
def health():
    return jsonify({"message": "Media Management Microservice Online"}), 200

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"message": "file not provided"}), 400
    
    file = request.files["file"]
    mimetype = file.mimetype or mimetypes.guess_type(file.filename)[0]

    #Validate file size
    file.seek(0, 2)
    file_size = file.tell() / (1024 * 1024)
    file.seek(0)

    if mimetype and mimetype.startswith("image"):
        try:
            file_bytes, mimetype, file_size = process_image(file)
        except Exception as e:
            return jsonify({"message": "invalid image file", "error": {str(e)}}), 400
    else:
        # this will make it upload any file that's not an image at ful size
        # this is dangerous but not sure how to proceed just yet
        file_bytes = file.read()

    ext = mimetypes.guess_extension(mimetype) or ""
    image_id = uuid.uuid4()
    key = f"uploads/{image_id}{ext}"
    return add_image_to_db(
        image_id = image_id,
        file_name = file.filename,
        mime_type = mimetype,
        file_size = file_size,
        backend_url = upload_to_s3(file_bytes, key, mimetype),
        key = key
    )

@app.route("/access/<url_id>", methods=["GET"])
def access_media(url_id):
    with get_db() as db:
        media = db.query(Media).filter(Media.url_id == url_id).first()
        if not media:
            return jsonify({"message": "media not found"}), 400
        
        r = requests.get(media.backend_url, stream=True)
        if r.status_code != 200:
            return jsonify({"message": "file unavailable"}), 500
        
        return Response(r.content, mimetype=r.headers.get("Content-Type"))

@app.route("/access-link/<url_id>")
def access_media_link(url_id):
    with get_db() as db:
        media = db.query(Media).filter(Media.url_id == url_id).first()
        if not media:
            return jsonify({"message": "media not found"}), 400
        
        return jsonify({"link": media.backend_url}), 200

@app.route("/delete/<url_id>", methods=["POST"])
def delete_media_route(url_id):
    return delete_media(url_id = url_id)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5004"))
    init_db()
    with get_db() as db:
        all_media = db.query(Media).all()
        print(all_media)
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)