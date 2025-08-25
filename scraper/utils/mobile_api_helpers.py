"""
Mobile API HTTP Helpers - Authentication and connection testing
"""

import hashlib
import base64
import time
import aiohttp
import asyncio
from urllib.parse import urlencode


async def test_mobile_api_connection(endpoint, city_id, app_config):
    """Test mobile API connectivity and authentication"""
    try:
        # Prepare payload
        payload = {
            'params': f'{{"city_id": {city_id}, "mobile_type": "android", "version": "8.0.1"}}',
            'fields': '{"city_info": "", "city_config_all": ""}',
            'request_ts': int(time.time())
        }
        
        # Generate authentication token
        auth_token = generate_auth_token(payload, app_config)
        
        headers = {
            'User-Agent': app_config['user_agent'],
            'Authorization': auth_token,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint,
                data=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('errno') == 0:
                        city_info = data.get('data', {}).get('city_info', {})
                        if city_info:
                            return {
                                'success': True,
                                'message': 'Mobile API authentication successful',
                                'city_count': len(city_info.get('info', []))
                            }
                    else:
                        return {
                            'success': False,
                            'error': f"API Error: {data.get('error', 'Unknown error')}"
                        }
                else:
                    return {
                        'success': False,
                        'error': f"HTTP {response.status}: {await response.text()}"
                    }
                    
    except Exception as e:
        return {
            'success': False,
            'error': f"Connection error: {str(e)}"
        }


def generate_auth_token(payload, app_config):
    """Generate authentication token for mobile API"""
    # Sort parameters
    data = list(payload.items())
    data.sort()
    
    # Build token string
    token = app_config['app_secret']
    for key, value in data:
        token += f'{key}={value}'
    
    # Generate hash
    token_hash = hashlib.sha1(token.encode()).hexdigest()
    token_string = f"{app_config['app_id']}:{token_hash}"
    
    # Base64 encode
    return base64.b64encode(token_string.encode()).decode()


async def test_community_page_access(city_abbr, community_id, user_agent):
    """Test access to community detail pages"""
    url = f"https://m.lianjia.com/{city_abbr}/xiaoqu/{community_id}/pinzhi"
    
    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Referer': f'https://m.lianjia.com/{city_abbr}/xiaoqu/'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Check for success indicators
                    success_indicators = ['hdic_key', 'hdic_value', '小区']
                    blocked_indicators = ['验证码', 'captcha', '人机验证']
                    
                    has_success = any(indicator in content for indicator in success_indicators)
                    has_blocked = any(indicator in content for indicator in blocked_indicators)
                    
                    return {
                        'success': has_success and not has_blocked,
                        'status_code': response.status,
                        'content_length': len(content),
                        'has_data': has_success,
                        'is_blocked': has_blocked
                    }
                else:
                    return {
                        'success': False,
                        'status_code': response.status,
                        'error': f"HTTP {response.status}"
                    }
                    
    except Exception as e:
        return {
            'success': False,
            'error': f"Request failed: {str(e)}"
        }
