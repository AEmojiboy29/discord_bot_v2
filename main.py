import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Debug environment variables before importing web_server
print("🔍 DEBUG: Checking environment variables before import...")
env_vars_to_check = ['BOT_TOKEN', 'GUILD_ID', 'ADMIN_ROLE_IDS', 'WEB_API_URL']
for var in env_vars_to_check:
    value = os.environ.get(var, 'NOT_SET')
    print(f"🔍 {var}: '{value}' (length: {len(value)})")

# Check GUILD_ID specifically
guild_id_raw = os.environ.get('GUILD_ID', 'NOT_SET')
print(f"🔍 GUILD_ID raw: '{guild_id_raw}'")
print(f"🔍 GUILD_ID repr: {repr(guild_id_raw)}")

try:
    from web_server import app
    print("✅ Successfully imported web_server")
except Exception as e:
    print(f"❌ Failed to import web_server: {e}")
    print("💡 This is likely due to environment variable issues")
    raise

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Starting Roblox Whitelist API on port {port}")
    print(f"🌐 Web Admin: http://0.0.0.0:{port}/admin")
    
    # Run the application
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
