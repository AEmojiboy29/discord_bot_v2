import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_server import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Starting Roblox Whitelist API on port {port}")
    print(f"🌐 Web Admin: http://0.0.0.0:{port}/admin")
    print(f"🔧 Debug Mode: {os.environ.get('FLASK_DEBUG', 'False')}")
    
    # Get all relevant environment variables for debugging
    env_vars = {
        'BOT_TOKEN': '✅ Set' if os.environ.get('BOT_TOKEN') else '❌ Missing',
        'GUILD_ID': os.environ.get('GUILD_ID', 'Not set'),
        'ADMIN_ROLE_IDS': os.environ.get('ADMIN_ROLE_IDS', 'Not set'),
        'WEB_API_URL': os.environ.get('WEB_API_URL', 'Not set'),
        'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT', 'Not detected'),
        'RAILWAY_PUBLIC_DOMAIN': os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'Not set')
    }
    
    print("=== ENVIRONMENT VARIABLES ===")
    for key, value in env_vars.items():
        print(f"{key}: {value}")
    
    # Run the application
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
