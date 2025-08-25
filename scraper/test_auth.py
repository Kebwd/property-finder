"""
Test authentication token generation
"""

import hashlib
import base64
import time

# Test authentication generation
payload = {
    'params': '{"city_id": 110000, "mobile_type": "android", "version": "8.0.1"}',
    'fields': '{"city_info": "", "city_config_all": ""}',
    'request_ts': str(int(time.time()))
}

app_config = {
    'app_id': '20161001_android',
    'app_secret': '7df91ff794c67caee14c3dacd5549b35'
}

# Sort parameters
data = list(payload.items())
data.sort()

# Build token string
token = app_config['app_secret']
for key, value in data:
    token += f'{key}={value}'

print('🔐 Token string:', token[:100] + '...')

# Generate hash
token_hash = hashlib.sha1(token.encode()).hexdigest()
token_string = f"{app_config['app_id']}:{token_hash}"
auth_token = base64.b64encode(token_string.encode()).decode()

print('📱 App ID:', app_config['app_id'])
print('🔑 Token Hash:', token_hash)
print('🎫 Authorization:', auth_token)
print('🕐 Timestamp:', payload['request_ts'])
