from flask import Flask, render_template, request, jsonify
import cv2
import pytesseract
import pyttsx3
import googlemaps
import requests
from bs4 import BeautifulSoup
import sqlite3
import datetime
import re

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan_receipt', methods=['POST'])
def scan_receipt():
    image_path = request.json['image_path']
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    dosage = re.findall(r'\d+mg', text)
    return jsonify({"dosage": dosage})

@app.route('/speak', methods=['POST'])
def speak():
    text = request.json['text']
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    return jsonify({"status": "success"})

@app.route('/find_pharma_stores', methods=['POST'])
def find_pharma_stores():
    api_key = request.json['api_key']
    address = request.json['address']
    gmaps = googlemaps.Client(key=api_key)
    location = gmaps.geocode(address)[0]['geometry']['location']
    pharma_stores = gmaps.places_nearby(location, radius=10000, type='pharmacy')
    stores = [{"name": store['name'], "vicinity": store['vicinity']} for store in pharma_stores['results']]
    return jsonify(stores)

@app.route('/get_medicine_info', methods=['POST'])
def get_medicine_info():
    medicine_name = request.json['medicine_name']
    url = f'https://www.webmd.com/drugs/2/drug-9009-1943/{medicine_name}-oral/details'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    benefits = soup.find('div', {'class': 'benefits'}).text
    side_effects = soup.find('div', {'class': 'side-effects'}).text
    return jsonify({"benefits": benefits, "side_effects": side_effects})

@app.route('/recommend_physician', methods=['POST'])
def recommend_physician():
    api_key = request.json['api_key']
    address = request.json['address']
    last_prescription_date = datetime.date.fromisoformat(request.json['last_prescription_date'])
    if datetime.date.today() > last_prescription_date + datetime.timedelta(days=180):
        gmaps = googlemaps.Client(key=api_key)
        location = gmaps.geocode(address)[0]['geometry']['location']
        physicians = gmaps.places_nearby(location, radius=10000, type='doctor')
        doctors = [{"name": physician['name'], "vicinity": physician['vicinity']} for physician in physicians['results']]
        return jsonify(doctors)
    return jsonify({"status": "no recommendation"})

@app.route('/check_older_patients', methods=['POST'])
def check_older_patients():
    patients = request.json['patients']
    due_for_checkup = []
    for patient, birthdate_str in patients.items():
        birthdate = datetime.date.fromisoformat(birthdate_str)
        age = (datetime.date.today() - birthdate).days // 365
        if age > 50:
            last_checkup = datetime.date(2025, 1, 1)  # Example checkup date
            if datetime.date.today() > last_checkup + datetime.timedelta(days=60):
                due_for_checkup.append(patient)
    return jsonify(due_for_checkup)

if __name__ == '__main__':
    app.run(debug=True)
