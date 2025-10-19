from flask import Flask, request, jsonify
import requests
import os
import json
from threading import Lock

app = Flask(__name__)

# In-memory storage
whitelist_data = {}
data_lock = Lock()

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

@app.route('/')
def home():
    return jsonify({
        "status": "online", 
        "service": "Roblox Whitelist API",
        "endpoints": {
            "check_whitelist": "/check_whitelist?user_id=123",
            "verify_user": "/verify?username=RobloxUser"
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
            'username': whitelist_data.get(user_id, {}).get('username', 'Unknown')
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

@app.route('/webhook_verify', methods=['POST'])
def webhook_verify():
    """Webhook endpoint for Roblox game servers"""
    try:
        data = request.json
        user_id = data.get('user_id')
        action = data.get('action', 'check')
        
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
                'username': user_data.get('username', 'Unknown')
            })
            
        elif action == 'add':
            username = data.get('username', 'Unknown')
            discord_user = data.get('discord_user', 'API')
            
            with data_lock:
                whitelist_data[user_id] = {
                    'username': username,
                    'discord_user': discord_user,
                    'added_at': data.get('added_at', 'Unknown')
                }
            
            return jsonify({
                'success': True,
                'message': f'User {username} whitelisted'
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)