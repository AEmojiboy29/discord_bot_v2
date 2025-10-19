import discord
from discord.ext import commands
import json
import requests
import os
from flask import Flask, request, render_template_string, redirect, jsonify

print("=== ROBLOX WHITELIST BOT STARTING ===")

# Load config
try:
    with open('config.json') as f:
        config = json.load(f)
    BOT_TOKEN = config['BOT_TOKEN']
    GUILD_ID = int(config['GUILD_ID'])
    WEB_API_URL = config.get('WEB_API_URL', 'https://discordbotv2-production.up.railway.app')
    ADMIN_ROLE_IDS = config.get('ADMIN_ROLE_IDS', [])
    print("✅ Config loaded successfully!")
except Exception as e:
    print(f"❌ Config error: {e}")
    exit()

# Flask web server setup
app = Flask(__name__)

# Discord bot setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Web API functions (your existing functions)
def api_check_whitelist(user_id):
    try:
        response = requests.get(f"{WEB_API_URL}/check_whitelist?user_id={user_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"API check error: {e}")
        return None

def api_verify_username(username):
    try:
        response = requests.get(f"{WEB_API_URL}/verify?username={username}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"API verify error: {e}")
        return None

def api_add_whitelist(user_id, username, discord_user):
    try:
        payload = {
            'user_id': user_id,
            'username': username,
            'discord_user': discord_user,
            'action': 'add'
        }
        response = requests.post(f"{WEB_API_URL}/webhook_verify", json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"API add error: {e}")
        return False

def api_remove_whitelist(user_id):
    """Remove user from whitelist via API"""
    try:
        # Try POST method first
        payload = {'user_id': user_id}
        response = requests.post(f"{WEB_API_URL}/whitelist/remove", json=payload, timeout=10)
        
        if response.status_code == 200:
            return True
        
        # If POST fails, try DELETE method
        response = requests.delete(f"{WEB_API_URL}/whitelist/{user_id}", timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        print(f"API remove error: {e}")
        return False

def api_get_whitelist():
    """Get all whitelisted users"""
    try:
        response = requests.get(f"{WEB_API_URL}/whitelist", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"API get whitelist error: {e}")
        return None

# === FLASK WEB ROUTES ===
@app.route('/admin')
def admin_panel():
    """Web interface for managing whitelist"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Whitelist Management</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 40px;
                background: #f5f5f5;
            }
            .container {
                max-width: 600px;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .form-group { 
                margin: 20px 0; 
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            input[type="text"] { 
                padding: 10px; 
                width: 200px; 
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            button { 
                padding: 10px 20px; 
                margin: 5px; 
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
            }
            .add-btn { background: #4CAF50; color: white; }
            .remove-btn { background: #f44336; color: white; }
            .view-btn { background: #2196F3; color: white; }
            .success { 
                color: green; 
                background: #e8f5e8;
                padding: 10px;
                border-radius: 4px;
                margin: 10px 0;
            }
            .error { 
                color: red; 
                background: #ffebee;
                padding: 10px;
                border-radius: 4px;
                margin: 10px 0;
            }
            h1 { color: #333; }
            h3 { color: #555; margin-bottom: 15px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 Whitelist Management</h1>
            
            <!-- Add User Form -->
            <div class="form-group">
                <h3>➕ Add User to Whitelist</h3>
                <form action="/add_user" method="post">
                    <input type="text" name="user_id" placeholder="Roblox User ID" required>
                    <button type="submit" class="add-btn">Add User</button>
                </form>
            </div>

            <!-- Remove User Form -->
            <div class="form-group">
                <h3>➖ Remove User from Whitelist</h3>
                <form action="/remove_user" method="post">
                    <input type="text" name="user_id" placeholder="Roblox User ID" required>
                    <button type="submit" class="remove-btn">Remove User</button>
                </form>
            </div>

            <!-- Current Whitelist Info -->
            <div class="form-group">
                <h3>📋 Current Whitelist</h3>
                <a href="/whitelist" target="_blank">
                    <button type="button" class="view-btn">View Full Whitelist</button>
                </a>
                <a href="/api/whitelist" target="_blank">
                    <button type="button" class="view-btn">View JSON API</button>
                </a>
            </div>

            <!-- Messages -->
            {% if message %}
            <div class="{{ 'success' if message_type == 'success' else 'error' }}">
                {{ message }}
            </div>
            {% endif %}

            <!-- Quick Stats -->
            <div class="form-group">
                <h3>📊 Quick Stats</h3>
                <a href="/status" target="_blank">
                    <button type="button" class="view-btn">System Status</button>
                </a>
            </div>
        </div>
    </body>
    </html>
    ''', message=request.args.get('message'), message_type=request.args.get('type'))

@app.route('/add_user', methods=['POST'])
def add_user():
    """Add a user to whitelist via web form"""
    user_id = request.form['user_id'].strip()
    
    try:
        # Use your existing API function to add user
        success = api_add_whitelist(user_id, "Web_Form_Add", "Web_Admin")
        
        if success:
            return redirect('/admin?message=User %s added successfully!&type=success' % user_id)
        else:
            return redirect('/admin?message=Failed to add user %s via API&type=error' % user_id)
        
    except Exception as e:
        return redirect('/admin?message=Error: %s&type=error' % str(e))

@app.route('/remove_user', methods=['POST'])
def remove_user():
    """Remove a user from whitelist via web form"""
    user_id = request.form['user_id'].strip()
    
    try:
        # Use your existing API function to remove user
        success = api_remove_whitelist(user_id)
        
        if success:
            return redirect('/admin?message=User %s removed successfully!&type=success' % user_id)
        else:
            return redirect('/admin?message=Failed to remove user %s via API&type=error' % user_id)
        
    except Exception as e:
        return redirect('/admin?message=Error: %s&type=error' % str(e))

@app.route('/api/whitelist')
def api_whitelist_web():
    """JSON endpoint to view whitelist via web"""
    try:
        data = api_get_whitelist()
        if data:
            return jsonify(data)
        return jsonify({'error': 'Could not fetch whitelist'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def status_web():
    """Web status page"""
    try:
        # Test API connectivity
        whitelist_data = api_get_whitelist()
        user_count = len(whitelist_data.get('whitelist', [])) if whitelist_data else 0
        
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>System Status</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .status-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; }
                .status-item { margin: 10px 0; }
                .live { color: green; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="status-card">
                <h1>🤖 System Status</h1>
                <div class="status-item">
                    <strong>Web API:</strong> <span class="live">✅ Live</span>
                </div>
                <div class="status-item">
                    <strong>Whitelisted Users:</strong> {{ user_count }}
                </div>
                <div class="status-item">
                    <strong>API URL:</strong> {{ api_url }}
                </div>
                <br>
                <a href="/admin">← Back to Admin Panel</a>
            </div>
        </body>
        </html>
        ''', user_count=user_count, api_url=WEB_API_URL)
    except Exception as e:
        return f"Status error: {str(e)}"

@app.route('/')
def home():
    """Home page redirects to admin panel"""
    return redirect('/admin')

# Admin check function (your existing function)
def is_admin():
    async def predicate(ctx):
        # Check if user has administrator permission
        if ctx.author.guild_permissions.administrator:
            return True
        
        # Check if user has any of the admin roles
        if ADMIN_ROLE_IDS:
            user_roles = [role.id for role in ctx.author.roles]
            return any(role_id in user_roles for role_id in ADMIN_ROLE_IDS)
        
        return False
    return commands.check(predicate)

# === DISCORD BOT EVENTS & COMMANDS (your existing code below) ===
@bot.event
async def on_ready():
    print(f'✅ {bot.user} is now online!')
    print(f'🌐 Web API: {WEB_API_URL}')
    print(f'🌐 Web Admin Panel: https://discordbotv2-production.up.railway.app/admin')
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name="Roblox Whitelist System"
        )
    )

# === ADMIN COMMANDS ===
@bot.command(name='whitelist')
@is_admin()
async def whitelist_command(ctx, action: str, user_id: int = None):
    """Whitelist management commands"""
    if action.lower() == "add":
        if user_id is None:
            await ctx.send("❌ Please provide a UserID: `!whitelist add USERID`")
            return
            
        # Add to whitelist via API
        if api_add_whitelist(user_id, "Manual_Add", ctx.author.name):
            embed = discord.Embed(
                title="✅ User Whitelisted!",
                description=f"Roblox UserID `{user_id}` has been added to the whitelist!",
                color=0x00ff00
            )
            embed.add_field(name="Added by", value=ctx.author.mention, inline=True)
            embed.add_field(name="Web Panel", value=f"[Manage Whitelist]({WEB_API_URL}/admin)", inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Failed to add user to whitelist via API")
            
    elif action.lower() == "remove":
        if user_id is None:
            await ctx.send("❌ Please provide a UserID: `!whitelist remove USERID`")
            return
            
        # Check if user exists in whitelist first
        check_result = api_check_whitelist(user_id)
        if not check_result or not check_result.get('whitelisted'):
            await ctx.send(f"❌ User `{user_id}` is not in the whitelist!")
            return
            
        # Remove from whitelist via API
        if api_remove_whitelist(user_id):
            embed = discord.Embed(
                title="🗑️ User Removed!",
                description=f"Roblox UserID `{user_id}` has been removed from the whitelist!",
                color=0xffa500
            )
            embed.add_field(name="Removed by", value=ctx.author.mention, inline=True)
            embed.add_field(name="Web Panel", value=f"[Manage Whitelist]({WEB_API_URL}/admin)", inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Failed to remove user from whitelist via API")
            
    elif action.lower() == "list":
        try:
            data = api_get_whitelist()
            if data and data.get('status') == 'success':
                whitelist_data = data.get('whitelist', [])
                if whitelist_data:
                    user_list = "\n".join([f"• `{uid}`" for uid in whitelist_data[:10]])  # Show first 10
                    embed = discord.Embed(
                        title="📋 Whitelisted Users",
                        description=user_list,
                        color=0x0099ff
                    )
                    embed.set_footer(text=f"Total: {len(whitelist_data)} users - See full list at {WEB_API_URL}/admin")
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="📋 Whitelisted Users",
                        description="No users whitelisted",
                        color=0x0099ff
                    )
                    await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Could not fetch whitelist from API")
        except Exception as e:
            await ctx.send(f"❌ API error: {str(e)}")
            
    elif action.lower() == "api":
        embed = discord.Embed(
            title="🌐 Web API Endpoints",
            color=0x0099ff
        )
        embed.add_field(
            name="Web Admin Panel",
            value=f"[{WEB_API_URL}/admin]({WEB_API_URL}/admin)",
            inline=False
        )
        embed.add_field(
            name="Check Whitelist",
            value=f"`{WEB_API_URL}/check_whitelist?user_id=USERID`",
            inline=False
        )
        embed.add_field(
            name="Get All Whitelisted",
            value=f"`{WEB_API_URL}/whitelist`",
            inline=False
        )
        await ctx.send(embed=embed)
        
    elif action.lower() == "check":
        if user_id is None:
            await ctx.send("❌ Please provide a UserID: `!whitelist check USERID`")
            return
            
        result = api_check_whitelist(user_id)
        if result and result.get('success'):
            is_whitelisted = result.get('whitelisted', False)
            status = "✅ Whitelisted" if is_whitelisted else "❌ Not Whitelisted"
            embed = discord.Embed(
                title="🔍 Whitelist Check",
                description=f"UserID: `{user_id}`",
                color=0x00ff00 if is_whitelisted else 0xff0000
            )
            embed.add_field(name="Status", value=status, inline=True)
            embed.add_field(name="Web Panel", value=f"[Manage]({WEB_API_URL}/admin)", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ Could not check whitelist status for user `{user_id}`")
            
    else:
        await ctx.send("❌ Invalid action. Use `add`, `remove`, `list`, `check`, or `api`")

# ... (rest of your existing Discord bot commands remain unchanged)
# [Keep all your existing @bot.command functions exactly as they are]

@bot.command(name='setup')
@is_admin()
async def setup_command(ctx):
    """Initial setup guide"""
    embed = discord.Embed(
        title="🛠️ Whitelist System Setup Guide",
        description="The system is now set up and ready!",
        color=0x0099ff
    )
    
    embed.add_field(
        name="🌐 Web Admin Panel",
        value=f"[{WEB_API_URL}/admin]({WEB_API_URL}/admin)",
        inline=False
    )
    
    embed.add_field(
        name="👑 Admin Commands",
        value="`!whitelist add USERID` - Add user\n`!whitelist remove USERID` - Remove user\n`!whitelist list` - Show users\n`!whitelist check USERID` - Check status\n`!whitelist api` - API endpoints",
        inline=False
    )
    
    embed.add_field(
        name="👤 Player Commands",
        value="`!verify ROBLOX_USERNAME` - Request access\n`!status` - Check system status",
        inline=False
    )
    
    await ctx.send(embed=embed)

# ... (rest of your existing code: verify_command, status_command, etc.)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found. Use `!commands` for available commands.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument. Check the command syntax.")
    else:
        print(f"Error: {error}")
        await ctx.send("❌ An error occurred while executing the command.")

def run_flask():
    """Run Flask web server"""
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    import threading
    
    # Start Flask web server in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🌐 Flask web server started!")
    
    # Start Discord bot
    bot.run(BOT_TOKEN)
