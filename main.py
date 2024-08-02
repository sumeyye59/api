import os
import requests
import logging
import threading
import pygame
from pydub import AudioSegment
from pydub.playback import play
from microphone import MicrophoneStream 
import keyboard
from os import system
      
def record_audio_to_mp3(filename):
    RATE = 44100
    CHUNK = 1024
    audio_data = bytearray()

    try:
        with MicrophoneStream(RATE, CHUNK) as stream:
            print("Mikrofon dinleniyor...")
            audio_generator = stream.generator()

            #start_time = time.time()
            print("Kaydı durdurmak için 'q' tuşuna basın...")
            while True:
                try:
                    for chunk in audio_generator:
                        audio_data.extend(chunk)
                       
                        if keyboard.is_pressed('q'):
                            print("Kayıt durduruldu.")
                            stream.closed = True
                            break
                    if stream.closed:
                        break    
                except KeyboardInterrupt:
                    print("Kayıt manuel olarak durduruldu.")
                    break

        print("Ses verisi işleniyor ve MP3 dosyasına kaydediliyor...")
        # AudioSegment ile bytearray verisini işleme
        audio_segment = AudioSegment(
            data=bytes(audio_data),
            sample_width=2,
            frame_rate=RATE,
            channels=1
        )

        # MP3 olarak kaydetme
        audio_segment.export(filename, format="wav")
        print(f"Ses kaydı {filename} dosyasına kaydedildi.")

    except Exception as e:
        print(f"Bir hata oluştu: {e}")

def play(file_path,lang):             
    print(f"{lang} dilinde oynatılıyor..")
    pygame.init()
    pygame.mixer.init()
    sound = pygame.mixer.Sound(file_path)

# Sesi çalmaya başlayın
    sound.play()
    pygame.time.wait(int(sound.get_length() * 1000))
    
    system("cls")
        
def send_audio_to_api(file_path, langin, langout):
    url = 'http://127.0.0.1:5000/process_audio'
    files = {'file': open(file_path, 'rb')}
    response = requests.post(url, files=files, data={'langin': langin, 'langout': langout})
    return response
      
def main():
    # Mikrofondan kayıt alma
    #record_audio_to_mp3("audio\\input.wav")  
    target_languages = ['Amerika']  # Çevirmek istediğiniz dillerin listesi
    for lang in target_languages:
        response = send_audio_to_api("input.wav", 'tr', lang)
        if response.status_code == 200:
            output_file = f"audio\\{lang.lower()}.wav"
            with open(output_file, "wb") as f:
                f.write(response.content)
            play(output_file,lang)
        else:
            logging.error(f"Error converting text to speech for {lang}: {response.status_code}")
            print(f"Metin sese dönüştürülürken bir hata oluştu!!!: {response.status_code}")

    
    pygame.mixer.quit()
    pygame.quit() 
    
                     
if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)
    main()