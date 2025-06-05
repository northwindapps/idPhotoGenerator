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
        print("Image key missing in request.files")
        return {"error": "No image provided"}, 400

    uploaded_file = request.files["image"]

    print(f"Received: {uploaded_file.filename}, Content-Type: {uploaded_file.content_type}")
    print(f"Length: {len(uploaded_file.read())}")
    uploaded_file.seek(0)

    try:
        pil_image = Image.open(uploaded_file).convert("RGBA")
    except Exception as e:
        print(f"Error processing image: {e}")
        return {"error": str(e)}, 500
    
    cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGR)

    # Adjust brightness and contrast
    alpha = float(request.args.get("alpha", 1.0))  # default 1.0
    beta = int(request.args.get("beta", 0))        # default 0
    adjusted = cv2.convertScaleAbs(cv_image, alpha=alpha, beta=beta)

    # Optionally apply gamma correction
    # adjusted = adjust_gamma(adjusted, gamma=1.3)

    # Convert back to PIL Image (RGBA for rembg)
    final_p_image = Image.fromarray(cv2.cvtColor(adjusted, cv2.COLOR_BGR2RGBA))

    # Remove background
    foreground = remove(final_p_image, session=session)

    # Create white background
    white_bg = Image.new("RGBA", foreground.size, (255, 255, 255, 255))
    result = Image.alpha_composite(white_bg, foreground)

    # Convert to RGB
    result = result.convert("RGB")

    # Save to buffer
    img_io = io.BytesIO()
    result.save(img_io, format="JPEG")
    img_io.seek(0)

    # Return Lambda proxy-compatible response
    # return {
    #     "statusCode": 200,
    #     "headers": {
    #         "Content-Type": "image/jpeg"
    #     },
    #     "isBase64Encoded": True,
    #     "body": base64.b64encode(img_io.getvalue()).decode("utf-8")
    # }
    return Response(img_io.getvalue(), mimetype='image/jpeg')


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