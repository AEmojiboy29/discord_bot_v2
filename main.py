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
    WEB_API_URL = os.environ.get('WEB_API_URL', 'http://localhost:8080')
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

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is now online!')
    print(f'🌐 Web API: {WEB_API_URL}')
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name="Roblox Whitelist System"
        )
    )

@bot.command(name='verify')
async def verify_command(ctx, roblox_username: str = None):
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
        value=f"✅ Approve: `!whitelist add {user_id}`\n❌ Deny: Ignore",
        inline=False
    )
    embed.add_field(
        name="Profile",
        value=f"[View Roblox Profile](https://www.roblox.com/users/{user_id}/profile)",
        inline=False
    )
    
    for member in ctx.guild.members:
        if member.guild_permissions.administrator and not member.bot:
            try:
                await member.send(embed=embed)
            except:
                pass
    
    await ctx.send(f"✅ Verification request for **{verified_username}** sent to admins!")

@bot.command(name='whitelist')
async def whitelist_command(ctx, action: str, user_id: int = None):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ You need administrator permissions to use this command.")
        return
        
    if action == "add" and user_id:
        # Get username from Roblox
        username = f"User_{user_id}"  # Default
        result = api_verify_username("")  # We'll get username from ID differently
        
        if api_add_whitelist(user_id, username, ctx.author.name):
            embed = discord.Embed(
                title="✅ User Whitelisted!",
                description=f"Roblox UserID `{user_id}` has been whitelisted!",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Failed to whitelist user via API.")
    elif action == "list":
        try:
            response = requests.get(f"{WEB_API_URL}/check_whitelist?user_id=1")
            await ctx.send("📋 Whitelist functionality is active! Use the web API to view full list.")
        except:
            await ctx.send("❌ API is not responding.")

if __name__ == "__main__":
    bot.run(BOT_TOKEN)