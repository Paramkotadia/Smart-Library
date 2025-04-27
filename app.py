from flask import Flask, render_template, request, jsonify
import cv2
import pytesseract
import numpy as np
import time
from threading import Thread

app = Flask(__name__)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Global variables for camera and detection
camera = None
detection_active = False
current_result = ""
processing_frame = False

def detect_book_from_camera(book_query):
    global camera, detection_active, current_result, processing_frame

    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0)
        time.sleep(2)  # Allow camera to warm up

    detection_active = True
    current_result = ""

    for _ in range(100):  # 100 frames max
        if not detection_active:
            break

        ret, frame = camera.read()
        if not ret:
            break

        # Resize frame for better view (optional)
        frame = cv2.resize(frame, (800, 600))

        # Show live feed
        cv2.imshow("📚 Live Book Scanning - Press 'q' to Stop", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Preprocess frame for better OCR
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        # Perform OCR
        processing_frame = True
        text = pytesseract.image_to_string(gray)
        processing_frame = False

        print("[OCR TEXT]:", text.strip())

        if book_query.lower() in text.lower():
            current_result = "✅ Book Found!"
            break

    if not current_result:
        current_result = "❌ Book Not Found."

    detection_active = False

    # Release the window after scanning
    cv2.destroyAllWindows()
    return current_result

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", result="")

@app.route("/start", methods=["POST"])
def start():
    book_query = request.form["book_query"]

    # Run detection in a separate thread to avoid blocking
    detection_thread = Thread(target=detect_book_from_camera, args=(book_query,))
    detection_thread.start()

    return render_template("index.html", result="Searching...", book_query=book_query)

@app.route("/get_result", methods=["GET"])
def get_result():
    global current_result
    return jsonify({"result": current_result})

@app.route("/stop", methods=["POST"])
def stop():
    global detection_active, camera
    detection_active = False
    if camera and camera.isOpened():
        camera.release()
        camera = None
    cv2.destroyAllWindows()
    return jsonify({"status": "stopped"})

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
    app.run(debug=True, threaded=True)