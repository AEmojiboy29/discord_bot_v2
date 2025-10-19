import discord
from discord.ext import commands
import json
import requests
import os

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

# Discord bot setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Web API functions
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

# === DISCORD BOT EVENTS ===
@bot.event
async def on_ready():
    print(f'✅ {bot.user} is now online!')
    print(f'🌐 Web API: {WEB_API_URL}')
    print(f'🌐 Web Admin Panel: {WEB_API_URL}/admin')
    
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

# === USER COMMANDS ===
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

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
