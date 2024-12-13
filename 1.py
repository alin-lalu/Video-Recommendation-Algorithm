import os
import time
import json
import requests
import openai
from flask import Flask, request, render_template, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure your API keys and other credentials
DALL_E_API_KEY = "your-dalle-api-key"
VIDEO_API_KEY = "your-video-api-key"
EMAIL_USER = "your-email@example.com"
EMAIL_PASSWORD = "your-email-password"

# Flask app setup
app = Flask(__name__)

# Database setup
Base = declarative_base()
DB_URL = "sqlite:///ai_generation.db"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

class ContentGeneration(Base):
    __tablename__ = 'content_generation'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True)
    prompt = Column(Text)
    video_paths = Column(Text)
    image_paths = Column(Text)
    status = Column(String)
    generated_at = Column(DateTime)

Base.metadata.create_all(engine)

# Function to generate images using DALL-E
openai.api_key = DALL_E_API_KEY
def generate_images(prompt, user_id):
    image_paths = []
    try:
        response = openai.Image.create(prompt=prompt, n=5, size="1024x1024")
        for i, img_data in enumerate(response['data']):
            image_url = img_data['url']
            image_path = f"generated_content/{user_id}/image_{i + 1}.jpg"
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            with open(image_path, "wb") as f:
                img_bytes = requests.get(image_url).content
                f.write(img_bytes)
            image_paths.append(image_path)
    except Exception as e:
        print(f"Error generating images: {e}")
    return image_paths

# Function to generate videos
def generate_videos(prompt, user_id):
    video_paths = []
    for i in range(5):
        video_path = f"generated_content/{user_id}/video_{i + 1}.mp4"
        os.makedirs(os.path.dirname(video_path), exist_ok=True)
        with open(video_path, "w") as f:
            f.write(f"Mock video for prompt: {prompt}")
        video_paths.append(video_path)
    return video_paths

# Function to send email notifications
def send_email_notification(email, user_id):
    subject = "Your AI-generated content is ready!"
    body = f"Your content is ready! Visit: http://127.0.0.1:5000/user/{user_id} to view your content."

    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()

    # API Integration Functions
    def fetch_api_data(endpoint):
        headers = {"Authorization": "Bearer your_api_token"}  # Replace with actual token if required
        try:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from API: {e}")
            return None

    @app.route('/api/viewed_posts', methods=['GET'])
    def get_viewed_posts():
        data = fetch_api_data("https://api.socialverseapp.com/posts/view?page=1&page_size=1000&resonance_algorithm=resonance_algorithm_cjsvervb7dbhss8bdrj89s44jfjdbsjd0xnjkbvuire8zcjwerui3njfbvsujc5if")
        return jsonify(data or {"error": "Failed to fetch viewed posts"})

    @app.route('/api/liked_posts', methods=['GET'])
    def get_liked_posts():
        data = fetch_api_data("https://api.socialverseapp.com/posts/like?page=1&page_size=1000&resonance_algorithm=resonance_algorithm_cjsvervb7dbhss8bdrj89s44jfjdbsjd0xnjkbvuire8zcjwerui3njfbvsujc5if")
        return jsonify(data or {"error": "Failed to fetch liked posts"})

    @app.route('/api/inspired_posts', methods=['GET'])
    def get_inspired_posts():
        data = fetch_api_data("https://api.socialverseapp.com/posts/inspire?page=1&page_size=1000&resonance_algorithm=resonance_algorithm_cjsvervb7dbhss8bdrj89s44jfjdbsjd0xnjkbvuire8zcjwerui3njfbvsujc5if")
        return jsonify(data or {"error": "Failed to fetch inspired posts"})

    @app.route('/api/rated_posts', methods=['GET'])
    def get_rated_posts():
        data = fetch_api_data("https://api.socialverseapp.com/posts/rating?page=1&page_size=1000&resonance_algorithm=resonance_algorithm_cjsvervb7dbhss8bdrj89s44jfjdbsjd0xnjkbvuire8zcjwerui3njfbvsujc5if")
        return jsonify(data or {"error": "Failed to fetch rated posts"})


@app.route('/api/all_posts', methods=['GET'])
def get_all_posts():
    data = fetch_api_data("https://api.socialverseapp.com/posts/summary/get?page=1&page_size=1000")
    return jsonify(data or {"error": "Failed to fetch all posts"})
@app.route('/')
def home():
    return "Welcome to the AI Content Generation Service!"



@app.route('/api/all_users', methods=['GET'])
def get_all_users():
    data = fetch_api_data("https://api.socialverseapp.com/users/get_all?page=1&page_size=1000")
    return jsonify(data or {"error": "Failed to fetch all users"})


# Route to display user content
@app.route('/user/<user_id>', methods=['GET'])
def display_content(user_id):
    user_content = session.query(ContentGeneration).filter_by(user_id=user_id).first()
    if not user_content:
        return "User content not found.", 404

    if user_content.status == "Processing":
        return "Your content is being generated. Please check back later."

    videos = json.loads(user_content.video_paths)
    images = json.loads(user_content.image_paths)

    return jsonify({
        'videos': videos,
        'images': images
    })

if __name__ == '__main__':
    app.run(debug=False)

