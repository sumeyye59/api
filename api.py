from flask import Flask, request, jsonify,send_file
import deepl
import requests
import os
import io
from google.cloud import speech
from google.cloud import speech_v1p1beta1 as speech
from google.cloud.speech_v1p1beta1 import types
from flask_mysqldb import MySQL
from pydub import AudioSegment
RATE = 44100
CHUNK = 1024
auth_key = "6b373e6f-2061-4da3-a1c8-0bcc37e4de9d:fx" # DeepL API key https://www.deepl.com/en/your-account/keys
translator = deepl.Translator(auth_key)

voice_id = "v6FyINIoYIaiI5TZzUbu"  
xi_api_key = "sk_fc2b4c8e1b117be421ece3f3095315a66787e1f3f6b1c966" # ElevanLabs API key https://elevenlabs.io/app/speech-synthesis

client = speech.SpeechClient()

api = Flask(__name__)

api.config['MYSQL_HOST'] = 'localhost'
api.config['MYSQL_USER'] = 'root'
api.config['MYSQL_PASSWORD'] = '1234'
api.config['MYSQL_DB'] = 'languages'
api.config['MYSQL_PORT'] = 3306
mysql = MySQL(api)

def text_to_speech(text, lang):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": xi_api_key
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True
    }
    }
    response = requests.post(url, json=data, headers=headers)
    return io.BytesIO(response.content)  


def convert_mp3_to_wav(mp3_bytes):
    # MP3 bytes verisini AudioSegment nesnesine yükleyin
    audio = AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")
    
    # WAV formatında bir BytesIO nesnesine dönüştürün
    wav_bytes_io = io.BytesIO()
    audio.export(wav_bytes_io, format="wav")
    wav_bytes_io.seek(0)  # Okuma konumunu sıfırlayın

    return wav_bytes_io

def speech_to_text(file,langin):
    # Dosyayı oku ve Google Cloud API'ye gönder
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=file.read())

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code=langin,
    )

    response = client.recognize(config=config, audio=audio)
    transcript = ""

    for result in response.results:
        transcript += result.alternatives[0].transcript
    return transcript 
        
@api.route('/process_audio', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
      return "No file part", 400
    data = request.form
    lang1 = data.get('langin','en-EN')
    lang2 = data.get('langout','İtalya')
    file = request.files['file']
    
    if file.filename == '':
        return "No selected file", 400
    cur = mysql.connection.cursor()
    query = "SELECT langcode FROM languages.countries WHERE CountryName = %s"
    cur.execute(query, (lang2,))
    code = cur.fetchone()
    cur.close()

    if not code:
        return jsonify({"error": "Country not found"}), 404
    targetlang=code[0]
    
    transcript=speech_to_text(file,lang1)
    #metni belirtilen dile çevir
    result = translator.translate_text(transcript, target_lang=targetlang)
    translated=result.text
    print(translated)
    audio_content=text_to_speech(translated,"EN-US")
    wav_data = convert_mp3_to_wav(audio_content.getvalue())
    return send_file(wav_data, mimetype='audio/wav')
    #return jsonify({"transcript": transcript})
    
    
#sesi texte çevirme isteği
@api.route('/s2t',methods=['POST'])
def upload_f():
    if 'file' not in request.files:
      return "No file part", 400
    data = request.form
    langin = data.get('langin','tr')
    file = request.files['file']
   
    if file.filename == '':
        return "No selected file", 400
    transcript=speech_to_text(file,langin)
    return transcript
#texti sese çevirme isteği
@api.route('/t2s',methods=['POST'])
def upload_text():
    data = request.json
    txt=data['text']
    audio=text_to_speech(txt,"TR")
    return send_file(audio, mimetype='audio/wav')
    
if __name__ == "__main__":
    api.run(debug=True,port=5000)
