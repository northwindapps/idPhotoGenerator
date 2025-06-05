import awsgi
from io import BytesIO
from flask import Flask, Response, jsonify, request, send_file

from rembg import new_session, remove
from PIL import Image
import io
import base64


app = Flask(__name__)

session = new_session("u2net")
#session = new_session(model_path="/app/u2net_human_seg.onnx")

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
        image = Image.open(uploaded_file).convert("RGBA")
    except Exception as e:
        print(f"Error processing image: {e}")
        return {"error": str(e)}, 500

    # Remove background
    foreground = remove(image, session=session)

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