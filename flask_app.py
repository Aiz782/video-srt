from flask import Flask, request, jsonify, render_template, send_file
from yt_dlp import YoutubeDL
from moviepy.editor import VideoFileClip
import whisper
import os
import tempfile
from datetime import timedelta

app = Flask(__name__)

def download_video(url, download_path):
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': os.path.join(download_path, 'video.mp4'),
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return os.path.join(download_path, "video.mp4")

def extract_audio(video_path, audio_path):
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(audio_path, codec='aac')

def transcribe_audio(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, language='en')
    return result

def format_timestamp(seconds):
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((td.total_seconds() - total_seconds) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def convert_to_srt(transcription):
    srt = []
    for i, segment in enumerate(transcription['segments']):
        start_time = segment['start']
        end_time = segment['end']
        text = segment['text']
        
        start_timestamp = format_timestamp(start_time)
        end_timestamp = format_timestamp(end_time)
        
        srt_entry = f"{i + 1}\n{start_timestamp} --> {end_timestamp}\n{text}\n"
        srt.append(srt_entry)
    return "\n".join(srt)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcribe', methods=['GET'])
def transcribe():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    with tempfile.TemporaryDirectory() as temp_dir:
        video_path = download_video(url, temp_dir)
        
        audio_path = os.path.join(temp_dir, "audio.aac")
        extract_audio(video_path, audio_path)
        
        transcription = transcribe_audio(audio_path)
        srt_transcript = convert_to_srt(transcription)
        
        return jsonify({"srt": srt_transcript})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
