import os
import sys
import time

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔍 Starting Roblox Whitelist System...")

# Check critical environment variables
env_vars = {
    'BOT_TOKEN': os.environ.get('BOT_TOKEN'),
    'GUILD_ID': os.environ.get('GUILD_ID'),
    'ADMIN_ROLE_IDS': os.environ.get('ADMIN_ROLE_IDS'),
    'WEB_API_URL': os.environ.get('WEB_API_URL'),
    'PORT': os.environ.get('PORT', '8080'),
    'RAILWAY_PUBLIC_DOMAIN': os.environ.get('RAILWAY_PUBLIC_DOMAIN'),
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

# Start Discord bot when the app loads
if __name__ == 'main':
    print("🚀 Initializing application...")
    
    # Start Discord bot
    try:
        start_discord_bot()
        print("🤖 Discord bot startup initiated")
    except Exception as e:
        print(f"⚠️  Discord bot startup warning: {e}")
    
    print("✅ Application initialization complete")
