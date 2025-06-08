import awsgi
from io import BytesIO
from flask import Flask, Response, jsonify, request, send_file
import cv2
from rembg import new_session, remove
from PIL import Image
import io
import base64
import numpy as np


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
        return jsonify({"error": "No image provided"}), 400

    uploaded_file = request.files["image"]
    uploaded_file.seek(0)

    try:
        pil_image = Image.open(uploaded_file).convert("RGBA")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGR)

    alpha = float(request.args.get("alpha", 1.0))
    beta = int(request.args.get("beta", 0))
    adjusted = cv2.convertScaleAbs(cv_image, alpha=alpha, beta=beta)

    final_p_image = Image.fromarray(cv2.cvtColor(adjusted, cv2.COLOR_BGR2RGBA))
    foreground = remove(final_p_image, session=session)

    white_bg = Image.new("RGBA", foreground.size, (255, 255, 255, 255))
    result = Image.alpha_composite(white_bg, foreground).convert("RGB")

    img_io = io.BytesIO()
    result.save(img_io, format="JPEG")
    img_io.seek(0)

    encoded = base64.b64encode(img_io.getvalue()).decode("utf-8")
    response = jsonify({
        "body": encoded
    })

    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set("Access-Control-Allow-Methods", "POST, OPTIONS")
    response.headers.set("Access-Control-Allow-Headers", "Content-Type")
    return response

    # return Response(img_io.getvalue(), mimetype='image/jpeg') for local testing

# Even in proxy mode, API Gateway often requires a clean response to OPTIONS.
@app.route("/process-image", methods=["OPTIONS"])
def options_process_image():
    response = Response()
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set("Access-Control-Allow-Methods", "POST, OPTIONS")
    response.headers.set("Access-Control-Allow-Headers", "Content-Type")
    return response

@app.route("/test-upload", methods=["POST"])
def test_upload():
    if "image" not in request.files:
        return {"error": "No image"}, 400
    f = request.files["image"]
    print("Filename:", f.filename)
    try:
        img = Image.open(f)
        print("Image format:", img.format)
    except Exception as e:
        return {"error": f"Cannot open image: {str(e)}"}, 400
    return {"message": "Image opened successfully", "format": img.format}

# Get all users
@app.route("/users", methods=["GET"])
def get_users():
    return jsonify(users)
# for local use
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=8000, debug=True)



def lambda_handler(event, context):
    if "httpMethod" not in event:
        print("Invalid event: missing 'httpMethod'")
        return {"statusCode": 400, "body": "Invalid request format"}

    return awsgi.response(app, event, context, base64_content_types={"image/jpeg", "image/png"})