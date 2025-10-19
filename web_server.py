from flask import Flask, request, jsonify, render_template_string, redirect
import requests
import os
import json
from threading import Lock
import time
import threading
import discord
from discord.ext import commands
import asyncio

app = Flask(__name__)

# In-memory storage (replace with database in production)
whitelist_data = {}
data_lock = Lock()

# Pre-whitelisted users (your friends)
PRE_WHITELISTED_USERS = {
    "melkinjereet": None,
    "xpfarmdedgame8": None, 
    "xpfarmdedgame5": None,
    "xpfarmdedgame6": None,
    "xpfarmdedgame7": None,
    "gpv_t": None
}

# Load config from environment variables (more secure)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GUILD_ID = int(os.environ.get('GUILD_ID', '0'))
ADMIN_ROLE_IDS_STR = os.environ.get('ADMIN_ROLE_IDS', '[]')
WEB_API_URL = os.environ.get('WEB_API_URL', 'https://discordbotv2-production.up.railway.app')

# Parse ADMIN_ROLE_IDS from JSON string
# REMOVE THIS DUPLICATE LINE: ADMIN_ROLE_IDS_STR = os.environ.get('ADMIN_ROLE_IDS', '[]')
try:
    ADMIN_ROLE_IDS = json.loads(ADMIN_ROLE_IDS_STR)
    if not isinstance(ADMIN_ROLE_IDS, list):
        ADMIN_ROLE_IDS = []
except:
    ADMIN_ROLE_IDS = []

print("=== ENVIRONMENT CONFIG ===")
print(f"🔑 BOT_TOKEN: {'✅ Set' if BOT_TOKEN else '❌ Missing'}")
print(f"🏠 GUILD_ID: {GUILD_ID}")
print(f"👑 ADMIN_ROLE_IDS: {ADMIN_ROLE_IDS}")
print(f"🌐 WEB_API_URL: {WEB_API_URL}")

# Validate critical configuration
if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("❌ CRITICAL: BOT_TOKEN not properly configured!")
    
if GUILD_ID == 0:
    print("❌ CRITICAL: GUILD_ID not properly configured!")

# Check if we're running on Railway
if os.environ.get('RAILWAY_ENVIRONMENT'):
    print("🚄 Running on Railway Platform")
    # Ensure WEB_API_URL uses the Railway provided URL
    railway_public_url = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
    if railway_public_url:
        WEB_API_URL = f"https://{railway_public_url}"
        print(f"🔗 Using Railway URL: {WEB_API_URL}")
        
# Roblox API functions
def get_roblox_user_id(username):
    """Get Roblox UserID from username"""
    try:
        url = f"https://api.roblox.com/users/get-by-username?username={username}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('Id'), data.get('Username')
        return None, None
    except Exception as e:
        print(f"Roblox API error: {e}")
        return None, None

def get_roblox_username(user_id):
    """Get Roblox username from UserID"""
    try:
        url = f"https://api.roblox.com/users/{user_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('Username')
        return None
    except Exception as e:
        print(f"Roblox API error: {e}")
        return None
# Initialize with some test data for demonstration
def initialize_sample_data():
    """Add some sample data for testing"""
    sample_users = {
        123456789: {
            "username": "TestUser1",
            "discord_user": "Admin",
            "added_at": "2024-01-01T00:00:00",
            "added_by": "System"
        },
        987654321: {
            "username": "TestUser2", 
            "discord_user": "Admin",
            "added_at": "2024-01-01T00:00:00",
            "added_by": "System"
        }
    }
    with data_lock:
        whitelist_data.update(sample_users)

# Initialize sample data
initialize_sample_data()

# === DISCORD BOT SETUP ===
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Web API functions for Discord bot
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

# Admin check function
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

# Discord Bot Events
@bot.event
async def on_ready():
    print(f'✅ Discord Bot: {bot.user} is now online!')
    print(f'🌐 Web Admin Panel: {WEB_API_URL}/admin')
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name="Roblox Whitelist System"
        )
    )

# Discord Bot Commands
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

@bot.command(name='verify')
async def verify_command(ctx, roblox_username: str = None):
    """Request whitelist access"""
    if roblox_username is None:
        await ctx.send("❌ Please provide your Roblox username: `!verify YourRobloxUsername`")
        return
    
    result = api_verify_username(roblox_username)
    
    if not result or not result.get('success'):
        await ctx.send("❌ Could not verify Roblox username. Please check the spelling.")
        return
    
    user_id = result['user_id']
    verified_username = result['username']
    is_whitelisted = result['whitelisted']
    
    if is_whitelisted:
        embed = discord.Embed(
            title="✅ Already Whitelisted!",
            description=f"**{verified_username}** (`{user_id}`) is already whitelisted!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
        return
    
    embed = discord.Embed(
        title="🔒 Verification Request",
        color=0xffa500
    )
    embed.description = f"**Player:** {verified_username}\n**UserID:** `{user_id}`\n**Discord User:** {ctx.author.mention}"
    embed.add_field(
        name="Actions",
        value=f"✅ Approve: `!whitelist add {user_id}`\n❌ Remove: `!whitelist remove {user_id}`",
        inline=False
    )
    embed.add_field(
        name="Profile",
        value=f"[View Roblox Profile](https://www.roblox.com/users/{user_id}/profile)",
        inline=False
    )
    
    # Send to admins
    admin_count = 0
    for member in ctx.guild.members:
        if member.guild_permissions.administrator and not member.bot:
            try:
                await member.send(embed=embed)
                admin_count += 1
            except:
                pass
    
    await ctx.send(f"✅ Verification request for **{verified_username}** sent to {admin_count} admins!")

@bot.command(name='status')
async def status_command(ctx):
    """Check bot status"""
    embed = discord.Embed(
        title="🤖 Bot Status",
        color=0x00ff00
    )
    
    embed.add_field(name="Server", value=ctx.guild.name, inline=True)
    embed.add_field(name="Ping", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="Web API", value="✅ Live", inline=True)
    embed.add_field(name="API URL", value=WEB_API_URL, inline=False)
    
    # Test API connectivity
    try:
        response = requests.get(f"{WEB_API_URL}/whitelist", timeout=5)
        if response.status_code == 200:
            data = response.json()
            user_count = len(data.get('whitelist', []))
            embed.add_field(name="Whitelisted Users", value=str(user_count), inline=True)
        else:
            embed.add_field(name="Whitelisted Users", value="❌ API Error", inline=True)
    except:
        embed.add_field(name="Whitelisted Users", value="❌ Unreachable", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='ping')
async def ping(ctx):
    """Test bot response time"""
    await ctx.send(f'🏓 Pong! {round(bot.latency * 1000)}ms')

@bot.command(name='commands')
async def help_command(ctx):
    """Show all commands"""
    embed = discord.Embed(
        title="🤖 Roblox Whitelist Bot - Commands",
        color=0x0099ff
    )
    
    embed.add_field(
        name="👑 Admin Commands",
        value="`!whitelist add USERID` - Add user\n`!whitelist remove USERID` - Remove user\n`!whitelist list` - Show users\n`!whitelist check USERID` - Check status\n`!whitelist api` - API endpoints\n`!setup` - Setup guide",
        inline=False
    )
    
    embed.add_field(
        name="👤 Player Commands", 
        value="`!verify ROBLOX_USERNAME` - Request access\n`!status` - System status\n`!ping` - Test bot",
        inline=False
    )
    
    embed.add_field(
        name="🌐 Web Admin Panel",
        value=f"[{WEB_API_URL}/admin]({WEB_API_URL}/admin)",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found. Use `!commands` for available commands.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument. Check the command syntax.")
    else:
        print(f"Discord Bot Error: {error}")
        await ctx.send("❌ An error occurred while executing the command.")

def run_discord_bot():
    """Run Discord bot in background"""
    if BOT_TOKEN and BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
        try:
            print("🤖 Starting Discord bot...")
            bot.run(BOT_TOKEN)
        except Exception as e:
            print(f"❌ Discord bot failed: {e}")
    else:
        print("❌ No valid BOT_TOKEN found, skipping Discord bot")

# Start Discord bot in background thread
def start_discord_bot():
    if BOT_TOKEN and BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
        bot_thread = threading.Thread(target=run_discord_bot, daemon=True)
        bot_thread.start()
        print("✅ Discord bot thread started!")
    else:
        print("❌ No valid BOT_TOKEN configured - Discord bot disabled")

# === WEB FORM ROUTES ===
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
                <form action="/web_add_user" method="post">
                    <input type="text" name="user_id" placeholder="Roblox User ID" required>
                    <button type="submit" class="add-btn">Add User</button>
                </form>
            </div>

            <!-- Remove User Form -->
            <div class="form-group">
                <h3>➖ Remove User from Whitelist</h3>
                <form action="/web_remove_user" method="post">
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
                <p><strong>Total Whitelisted Users:</strong> {{ user_count }}</p>
                <a href="/status" target="_blank">
                    <button type="button" class="view-btn">System Status</button>
                </a>
            </div>
        </div>
    </body>
    </html>
    ''', message=request.args.get('message'), message_type=request.args.get('type'), user_count=len(whitelist_data))

@app.route('/web_add_user', methods=['POST'])
def web_add_user():
    """Add a user to whitelist via web form"""
    user_id = request.form['user_id'].strip()
    
    try:
        user_id = int(user_id)
        username = get_roblox_username(user_id) or f"User_{user_id}"
        
        with data_lock:
            whitelist_data[user_id] = {
                'username': username,
                'discord_user': 'Web_Admin',
                'added_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'added_by': 'Web_Form'
            }
        
        return redirect('/admin?message=User %s added successfully!&type=success' % user_id)
        
    except ValueError:
        return redirect('/admin?message=Invalid User ID format&type=error')
    except Exception as e:
        return redirect('/admin?message=Error: %s&type=error' % str(e))

@app.route('/web_remove_user', methods=['POST'])
def web_remove_user():
    """Remove a user from whitelist via web form"""
    user_id = request.form['user_id'].strip()
    
    try:
        user_id = int(user_id)
        
        with data_lock:
            if user_id in whitelist_data:
                removed_user = whitelist_data[user_id]
                del whitelist_data[user_id]
                return redirect('/admin?message=User %s removed successfully!&type=success' % user_id)
            else:
                return redirect('/admin?message=User %s not found in whitelist&type=error' % user_id)
                
    except ValueError:
        return redirect('/admin?message=Invalid User ID format&type=error')
    except Exception as e:
        return redirect('/admin?message=Error: %s&type=error' % str(e))

# API Routes
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Roblox Whitelist API",
        "timestamp": time.time(),
        "whitelisted_users_count": len(whitelist_data),
        "endpoints": {
            "check_whitelist": "/check_whitelist?user_id=123",
            "verify_user": "/verify?username=RobloxUser",
            "get_whitelist": "/whitelist",
            "server_status": "/status",
            "webhook_verify": "/webhook_verify (POST)",
            "add_user": "/whitelist/add (POST)",
            "remove_user": "/whitelist/remove (POST)",
            "remove_user_direct": "/whitelist/<user_id> (DELETE)",
            "web_admin_panel": "/admin"
        }
    })

@app.route('/check_whitelist', methods=['GET'])
def check_whitelist():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'No user_id provided'}), 400
    
    try:
        user_id = int(user_id)
        with data_lock:
            is_whitelisted = user_id in whitelist_data
            
            return jsonify({
                'whitelisted': is_whitelisted,
                'user_id': user_id,
                'username': whitelist_data.get(user_id, {}).get('username', 'Unknown'),
                'discord_user': whitelist_data.get(user_id, {}).get('discord_user', 'Unknown')
            })
    except ValueError:
        return jsonify({'error': 'Invalid user_id'}), 400

@app.route('/verify', methods=['GET'])
def verify_username():
    """Verify Roblox username and get UserID"""
    username = request.args.get('username')
    
    if not username:
        return jsonify({'error': 'No username provided'}), 400
    
    user_id, verified_username = get_roblox_user_id(username)
    
    if user_id:
        with data_lock:
            is_whitelisted = user_id in whitelist_data
            
        return jsonify({
            'success': True,
            'user_id': user_id,
            'username': verified_username,
            'whitelisted': is_whitelisted,
            'profile_url': f'https://www.roblox.com/users/{user_id}/profile'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'User not found on Roblox'
        }), 404

@app.route('/whitelist', methods=['GET'])
def get_whitelist():
    """Get all whitelisted users"""
    with data_lock:
        # Format the data for better readability
        formatted_users = {}
        for user_id, user_data in whitelist_data.items():
            formatted_users[str(user_id)] = user_data
        
        return jsonify({
            'status': 'success',
            'whitelist': list(whitelist_data.keys()),
            'whitelisted_users': formatted_users,
            'total_count': len(whitelist_data),
            'timestamp': time.time()
        })

@app.route('/whitelist/add', methods=['POST'])
def add_to_whitelist():
    """Add user to whitelist via POST"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'No user_id provided'}), 400
        
        user_id = int(user_id)
        username = data.get('username')
        
        if not username:
            username = get_roblox_username(user_id) or f"User_{user_id}"
        
        discord_user = data.get('discord_user', 'API')
        
        with data_lock:
            whitelist_data[user_id] = {
                'username': username,
                'discord_user': discord_user,
                'added_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'added_by': data.get('added_by', 'API')
            }
        
        return jsonify({
            'status': 'success',
            'message': f'User {username} ({user_id}) added to whitelist',
            'user_id': user_id,
            'username': username,
            'whitelist': list(whitelist_data.keys())
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid user_id format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/whitelist/remove', methods=['POST'])
def remove_from_whitelist():
    """Remove user from whitelist via POST"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'No user_id provided'}), 400
        
        user_id = int(user_id)
        
        with data_lock:
            if user_id in whitelist_data:
                removed_user = whitelist_data[user_id]
                del whitelist_data[user_id]
                return jsonify({
                    'status': 'success',
                    'message': f'User {removed_user.get("username", "Unknown")} ({user_id}) removed from whitelist',
                    'user_id': user_id,
                    'username': removed_user.get('username', 'Unknown'),
                    'whitelist': list(whitelist_data.keys())
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'User {user_id} not found in whitelist'
                }), 404
                
    except ValueError:
        return jsonify({'error': 'Invalid user_id format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/whitelist/<user_id>', methods=['DELETE'])
def remove_from_whitelist_direct(user_id):
    """Remove user from whitelist via DELETE request"""
    try:
        if not user_id:
            return jsonify({'error': 'No user_id provided'}), 400
        
        user_id = int(user_id)
        
        with data_lock:
            if user_id in whitelist_data:
                removed_user = whitelist_data[user_id]
                del whitelist_data[user_id]
                return jsonify({
                    'status': 'success',
                    'message': f'User {removed_user.get("username", "Unknown")} ({user_id}) removed from whitelist',
                    'user_id': user_id,
                    'username': removed_user.get('username', 'Unknown'),
                    'whitelist': list(whitelist_data.keys())
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'User {user_id} not found in whitelist'
                }), 404
                
    except ValueError:
        return jsonify({'error': 'Invalid user_id format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """Get server status"""
    return jsonify({
        'status': 'online',
        'timestamp': time.time(),
        'users_whitelisted': len(whitelist_data),
        'special_users': list(PRE_WHITELISTED_USERS.keys()),
        'service': 'Roblox Whitelist API'
    })

@app.route('/webhook_verify', methods=['POST'])
def webhook_verify():
    """Webhook endpoint for Roblox game servers to verify users"""
    try:
        data = request.json
        
        user_id = data.get('user_id')
        action = data.get('action', 'check')  # check, add, remove
        
        if not user_id:
            return jsonify({'error': 'No user_id provided'}), 400
        
        user_id = int(user_id)
        
        if action == 'check':
            with data_lock:
                is_whitelisted = user_id in whitelist_data
                user_data = whitelist_data.get(user_id, {})
            
            return jsonify({
                'whitelisted': is_whitelisted,
                'user_id': user_id,
                'username': user_data.get('username', 'Unknown'),
                'discord_user': user_data.get('discord_user', 'Unknown')
            })
            
        elif action == 'add':
            username = data.get('username')
            if not username:
                username = get_roblox_username(user_id) or f"User_{user_id}"
                
            discord_user = data.get('discord_user', 'API')
            
            with data_lock:
                whitelist_data[user_id] = {
                    'username': username,
                    'discord_user': discord_user,
                    'added_at': data.get('added_at', time.strftime('%Y-%m-%dT%H:%M:%S')),
                    'added_by': data.get('added_by', 'API')
                }
            
            return jsonify({
                'success': True,
                'message': f'User {username} ({user_id}) added to whitelist',
                'user_id': user_id,
                'username': username
            })
            
        elif action == 'remove':
            with data_lock:
                if user_id in whitelist_data:
                    removed_user = whitelist_data[user_id]
                    del whitelist_data[user_id]
                    return jsonify({
                        'success': True, 
                        'message': f'User {removed_user.get("username", "Unknown")} removed from whitelist'
                    })
                else:
                    return jsonify({'error': 'User not in whitelist'}), 404
        
        else:
            return jsonify({'error': 'Invalid action. Use "check", "add", or "remove"'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add_user', methods=['POST'])
def add_user():
    """Direct endpoint to add users to whitelist"""
    try:
        data = request.json
        user_id = data.get('user_id')
        username = data.get('username')
        
        if not user_id:
            return jsonify({'error': 'No user_id provided'}), 400
        
        user_id = int(user_id)
        
        if not username:
            username = get_roblox_username(user_id) or f"User_{user_id}"
        
        with data_lock:
            whitelist_data[user_id] = {
                'username': username,
                'discord_user': data.get('discord_user', 'Manual'),
                'added_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'added_by': data.get('added_by', 'Manual')
            }
        
        return jsonify({
            'success': True,
            'message': f'User {username} added successfully',
            'user_id': user_id,
            'username': username
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Start Discord bot when web server starts
start_discord_bot()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Starting Roblox Whitelist API on port {port}")
    print(f"🌐 Web Admin: http://0.0.0.0:{port}/admin")
    app.run(host='0.0.0.0', port=port, debug=False)
