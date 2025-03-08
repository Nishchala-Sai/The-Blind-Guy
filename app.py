from flask import Flask, render_template, request, jsonify
import os
import subprocess

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/capture', methods=['POST'])
def capture():
    try:
        result = subprocess.run(['python', 'dumbo.py'], capture_output=True, text=True)
        description = result.stdout.strip()
        image_path = os.path.join(UPLOAD_FOLDER, 'captured_image.png')  # Assuming dumbo.py saves the image here
    except Exception as e:
        description = str(e)
        image_path = ''
    
    return jsonify({'image_url': image_path, 'description': description})

if __name__ == '__main__':
    app.run(debug=True)
