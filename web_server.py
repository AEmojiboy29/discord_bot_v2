from flask import Flask, request, jsonify
import requests
import os
import json
from threading import Lock
import time

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
            "remove_user_direct": "/whitelist/<user_id> (DELETE)"
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Starting Roblox Whitelist API on port {port}")
    print(f"📊 Pre-loaded {len(whitelist_data)} users")
    print(f"🆕 Remove functionality: ✅ IMPLEMENTED")
    app.run(host='0.0.0.0', port=port, debug=False)
