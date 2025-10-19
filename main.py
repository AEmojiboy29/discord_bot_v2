import os
import sys
import time
import threading
from waitress import serve

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🚀 Starting Roblox Whitelist System...")

# Check environment variables
env_vars = {
    'BOT_TOKEN': os.environ.get('BOT_TOKEN'),
    'GUILD_ID': os.environ.get('GUILD_ID'),
    'ADMIN_ROLE_IDS': os.environ.get('ADMIN_ROLE_IDS'),
    'WEB_API_URL': os.environ.get('WEB_API_URL'),
    'PORT': os.environ.get('PORT', '8080'),
}

for key, value in env_vars.items():
    status = '✅ Set' if value and value != 'NOT_SET' else '❌ Missing'
    print(f"   {key}: {status}")

try:
    from web_server import app, start_discord_bot
    
    print("✅ Successfully imported web_server module")
    
    # Add health check endpoint
    @app.route('/health')
    def health_check():
        return {
            'status': 'healthy', 
            'service': 'Roblox Whitelist API',
            'timestamp': time.time(),
            'discord_bot': 'online'
        }
    
except Exception as e:
    print(f"❌ Failed to import web_server: {e}")
    raise

def run_web_server():
    """Run the web server"""
    port = int(os.environ.get('PORT', 8080))
    print(f"🌐 Starting web server on port {port}")
    print(f"📊 Health check: http://0.0.0.0:{port}/health")
    print(f"⚙️  Admin panel: http://0.0.0.0:{port}/admin")
    
    # Use waitress production server instead of Flask dev server
    serve(app, host='0.0.0.0', port=port, threads=8)

if __name__ == '__main__':
    print("\n🎯 INITIALIZING SERVICES...")
    
    # Start Discord bot in background thread
    try:
        start_discord_bot()
        print("🤖 Discord bot startup initiated")
    except Exception as e:
        print(f"⚠️  Discord bot startup warning: {e}")
    
    # Start web server in main thread (this keeps the process alive)
    print("🔄 Starting web server (this will keep the container running)...")
    run_web_server()
