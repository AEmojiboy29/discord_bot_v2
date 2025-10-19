import os
import sys
import time
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

if __name__ == '__main__':
    print("\n🎯 INITIALIZING SERVICES...")
    
    # Show the correct public URL
    web_url = os.environ.get('WEB_API_URL', f"http://0.0.0.0:{os.environ.get('PORT', '8080')}")
    print(f"🌐 Public URL: {web_url}")
    print(f"📊 Health check: {web_url}/health")
    print(f"⚙️  Admin panel: {web_url}/admin")
    
    # Start Discord bot in background thread
    try:
        start_discord_bot()
        print("🤖 Discord bot startup initiated")
    except Exception as e:
        print(f"⚠️  Discord bot startup warning: {e}")
    
    # Start web server in main thread
    port = int(os.environ.get('PORT', 8080))
    print(f"🔄 Starting web server on port {port}...")
    
    serve(app, host='0.0.0.0', port=port, threads=8)
