import awsgi
from flask import Flask, jsonify, request, send_file

from rembg import new_session, remove
from PIL import Image
import io


app = Flask(__name__)

session = new_session("u2net")

# Sample data for a sample route
users = [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"}
]

@app.route("/process-image", methods=["POST"])
def process_image():
    if "image" not in request.files:
        return {"error": "No image provided"}, 400

    # Read the uploaded image
    uploaded_file = request.files["image"]
    image = Image.open(uploaded_file).convert("RGBA")

    # Remove background
    foreground = remove(image, session=session)

    # Create background (white or any color)
    white_bg = Image.new("RGBA", foreground.size, (255, 255, 255, 255))
    result = Image.alpha_composite(white_bg, foreground)

    # Convert to RGB (JPEG compatibility)
    result = result.convert("RGB")

    # Save to in-memory buffer
    img_io = io.BytesIO()
    result.save(img_io, format="JPEG")
    img_io.seek(0)

    return send_file(img_io, mimetype="image/jpeg")

# Get all users
@app.route("/users", methods=["GET"])
def get_users():
    return jsonify(users)
# for local use
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=8000, debug=True)



def lambda_handler(event, context):
    return awsgi.response(app, event, context, base64_content_types={"image/png"})
