from flask import Flask, render_template, request, jsonify, url_for, send_file
import os
import io
from PIL import Image
import rembg
from pydub import AudioSegment
from moviepy.video.io.VideoFileClip import VideoFileClip

app = Flask(__name__)


UPLOAD_FOLDER = 'uploads'
COMPRESSED_FOLDER = 'compressed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)


def compress_image(input_path, output_path, quality):
    """
    Compress an image, handling transparency for RGBA images.
    """
    img = Image.open(input_path)
    
    
    if img.mode == "RGBA":
        img = img.convert("RGB")
    

    img.save(output_path, "JPEG", quality=quality, optimize=True)


def compress_audio(input_path, output_path, bitrate="128k"):
    # changes
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="mp3", bitrate=bitrate)
    except Exception as e:
        raise Exception(f"Audio compression failed: {str(e)}")


def compress_video(input_path, output_path, target_size_mb):
    video = VideoFileClip(input_path)
    current_size_mb = os.path.getsize(input_path) / (1024 * 1024)
    compression_ratio = target_size_mb / current_size_mb

    if compression_ratio >= 1.0:
        video.write_videofile(output_path, codec="libx264", audio_codec="aac")
    else:
        video.write_videofile(output_path, codec="libx264", audio_codec="aac", bitrate=f"{int(compression_ratio * video.bitrate)}k")
        


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/page2')
def page2():
    return render_template('page2.html')


@app.route('/compressor')
def compressor():
    return render_template('compressor.html')

@app.route('/background_remover')
def background_remover():
    return render_template('background_remover.html')

@app.route('/remove_background', methods=['POST'])
def remove_background():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if not file:
        return jsonify({"error": "No file provided"}), 400

    try:
        # Read the uploaded file bytes
        input_bytes = file.read()

        # Validate the file is not empty
        if not input_bytes:
            return jsonify({"error": "Uploaded file is empty"}), 400

        # Use rembg to remove the background (this returns the processed image in bytes)
        output_bytes = rembg.remove(input_bytes)

        # Open the processed image from the output bytes
        output_image = Image.open(io.BytesIO(output_bytes))

        # Save the processed image to a file
        output_filename = f"background_removed_{file.filename}"
        output_path = os.path.join(COMPRESSED_FOLDER, output_filename)
        output_image.save(output_path, "PNG")
    
        return jsonify({
            "message": "Background removed successfully!",
            "download_url": url_for('download_file', filename=output_filename, _external=True)
        })
    except Exception as e:
        return jsonify({"error": f"Background removal failed: {str(e)}"}), 500

@app.route('/converter')
def converter():
    return render_template('converter.html')

@app.route('/convert', methods=['POST'])
def convert_file():
    file_path = request.form.get('file_path')
    file_format = request.form.get('format')
    if not file_path or not file_format:
        return jsonify({"error": "Missing file path or format"}), 400
    if not os.path.exists(file_path):
        return jsonify({"error": "Uploaded file not found"}), 404
    try:
        output_filename = os.path.splitext(os.path.basename(file_path))[0] + f".{file_format.lower()}"
        output_path = os.path.join(COMPRESSED_FOLDER, output_filename)
        img = Image.open(file_path)
        if file_format.lower() in ["jpg", "jpeg"]:
            if img.mode == "RGBA" or img.mode == "P":
                img = img.convert("RGB")
            img.save(output_path, "JPEG", quality=95)
        elif file_format.lower() in ["png", "bmp", "gif", "tiff"]:
            img.save(output_path, file_format.upper())

        # Remove the uploaded file after processing
        if os.path.exists(file_path):
            os.remove(file_path)     
        else:
            return jsonify({"error": "Unsupported format"}), 400
        return jsonify({
            "message": "File converted successfully!",
            "download_url": url_for('download_file', filename=output_filename, _external=True)
        })
    except Exception as e:
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file:
        input_path = os.path.join(UPLOAD_FOLDER, file.filename)
        try:
            file.save(input_path)
            if not os.path.exists(input_path):
                return jsonify({"error": "File could not be saved"}), 500
            return jsonify({"file_path": input_path, "message": "File uploaded successfully!"})
        except Exception as e:
            return jsonify({"error": f"Upload failed: {str(e)}"}), 500
    return jsonify({"error": "Invalid file"}), 400


@app.route('/process', methods=['POST'])
def process_file():
    file_path = request.form.get('file_path')
    file_type = request.form.get('file_type')
    output_path = os.path.join(COMPRESSED_FOLDER, f"compressed_{os.path.basename(file_path)}")

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found. Please re-upload."}), 400

    try:
        if file_type == 'image':
            quality = int(request.form.get('quality', 50))
            compress_image(file_path, output_path, quality)
        elif file_type == 'audio':
            bitrate = request.form.get('bitrate', "128k")
            compress_audio(file_path, output_path, bitrate)
        elif file_type == 'video':
            target_size_mb = float(request.form.get('target_size', 50))
            compress_video(file_path, output_path, target_size_mb)
        else:
            return jsonify({"error": "Invalid file type"}), 400
            
        # Remove the uploaded file after processing
        if os.path.exists(file_path):
            os.remove(file_path)    

        if not os.path.exists(output_path):
            return jsonify({"error": "File processing failed"}), 500

        return jsonify({
            "message": "File processed successfully!",
            "download_url": url_for('download_file', filename=os.path.basename(output_path), _external=True)
        })
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500


@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(COMPRESSED_FOLDER, filename)
    if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
    else:
        return jsonify({"error": "File not found."}), 404
    

if __name__ == '__main__':
    app.run(debug=True) 