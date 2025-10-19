import os
import sys
import time
import signal
import asyncio

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
    'RAILWAY_PUBLIC_DOMAIN': os.environ.get('RAILWAY_PUBLIC_DOMAIN')
}

for key, value in env_vars.items():
    status = '✅ Set' if value and value != 'NOT_SET' else '❌ Missing'
    print(f"   {key}: {status}")

try:
    from web_server import app, bot, BOT_TOKEN, start_discord_bot
    
    print("✅ Successfully imported web_server module")
    
except Exception as e:
    print(f"❌ Failed to import web_server: {e}")
    raise

# Global variable to track shutdown
shutting_down = False

def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutting_down
    print(f"\n⚠️  Received shutdown signal {signum}")
    shutting_down = True
    
    # Shutdown Discord bot gracefully
    try:
        if bot and bot.is_ready():
            print("🤖 Shutting down Discord bot...")
            asyncio.create_task(bot.close())
    except Exception as e:
        print(f"⚠️  Error during bot shutdown: {e}")
    
    # Exit the application
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    
    print("\n🚀 STARTING SERVER...")
    print(f"   Port: {port}")
    print(f"   Host: 0.0.0.0")
    
    railway_domain = env_vars['RAILWAY_PUBLIC_DOMAIN']
    if railway_domain:
        print(f"   Web Admin: https://{railway_domain}/admin")
        print(f"   Health Check: https://{railway_domain}/health")
    else:
        print(f"   Web Admin: http://0.0.0.0:{port}/admin")
        print(f"   Health Check: http://0.0.0.0:{port}/health")
    
    # Start Discord bot (only once)
    try:
        if BOT_TOKEN and BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
            print("🤖 Starting Discord bot...")
            # Import the function to start the bot thread
            from web_server import start_discord_bot
            start_discord_bot()
            print("✅ Discord bot startup initiated")
        else:
            print("❌ No valid BOT_TOKEN - Discord bot disabled")
    except Exception as e:
        print(f"⚠️  Discord bot startup warning: {e}")
    
    # Run web server
    try:
        print("\n📡 WEB SERVER STARTING...")
        print("💡 Server is now running and should stay online")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ Web server failed: {e}")
        if not shutting_down:
            raise
