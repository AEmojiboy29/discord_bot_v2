import os
import sys
import time

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔍 Starting Roblox Whitelist System...")
print("📋 Environment Check:")

# Check critical environment variables
env_vars = {
    'BOT_TOKEN': os.environ.get('BOT_TOKEN'),
    'GUILD_ID': os.environ.get('GUILD_ID'),
    'ADMIN_ROLE_IDS': os.environ.get('ADMIN_ROLE_IDS'),
    'WEB_API_URL': os.environ.get('WEB_API_URL'),
    'PORT': os.environ.get('PORT', '8080'),
    'RAILWAY_PUBLIC_DOMAIN': os.environ.get('RAILWAY_PUBLIC_DOMAIN')
}

for key, value in env_vars.items():
    status = '✅ Set' if value and value != 'NOT_SET' else '❌ Missing'
    print(f"   {key}: {status} ({value})")

try:
    from web_server import app, start_discord_bot, WEB_API_URL
    
    print("✅ Successfully imported web_server module")
    print(f"🌐 Web API URL configured: {WEB_API_URL}")
    
    # Add a simple health check endpoint
    @app.route('/health')
    def health_check():
        return {
            'status': 'healthy', 
            'service': 'Roblox Whitelist API',
            'timestamp': time.time(),
            'whitelisted_users': len(getattr(app, 'whitelist_data', {})),
            'discord_bot': 'online'
        }
    
    @app.route('/')
    def home():
        return {
            "status": "online",
            "service": "Roblox Whitelist API",
            "timestamp": time.time(),
            "endpoints": {
                "health": "/health",
                "admin_panel": "/admin",
                "check_whitelist": "/check_whitelist?user_id=123",
                "verify_user": "/verify?username=RobloxUser", 
                "get_whitelist": "/whitelist",
                "server_status": "/status"
            }
        }
    
    print("✅ Routes initialized successfully")
    
except Exception as e:
    print(f"❌ Failed to import web_server: {e}")
    print("💡 Check for syntax errors in web_server.py")
    raise

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    
    print("\n🚀 STARTING SERVER...")
    print(f"   Port: {port}")
    print(f"   Host: 0.0.0.0")
    print(f"   Web Admin: http://0.0.0.0:{port}/admin")
    print(f"   Health Check: http://0.0.0.0:{port}/health")
    print(f"   API Status: http://0.0.0.0:{port}/")
    print(f"   Public URL: {env_vars['RAILWAY_PUBLIC_DOMAIN'] or 'Not set'}")
    
    # Start Discord bot in background
    try:
        start_discord_bot()
        print("🤖 Discord bot startup initiated")
    except Exception as e:
        print(f"⚠️  Discord bot startup warning: {e}")
    
    # Run the Flask application
    try:
        print("\n📡 WEB SERVER IS NOW RUNNING...")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"❌ Web server failed to start: {e}")
        print("💡 Check if the port is available and dependencies are installed")
        raise
