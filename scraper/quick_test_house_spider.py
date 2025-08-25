#!/usr/bin/env python3
"""
Quick Anti-Bot Test for House Spider
Tests if the house spider is working with anti-bot protection
"""

import subprocess
import sys
from pathlib import Path
import json

def quick_test_house_spider():
    """Quick test of house spider with anti-bot protection"""
    print("🏠 Quick House Spider Anti-Bot Test")
    print("=" * 50)
    
    # Test with minimal settings for quick results
    cmd = [
        sys.executable, "-m", "scrapy", "crawl", "house_spider",
        "-a", "mode=test",
        "-a", "max_pages=1",  # Limit to 1 page for quick test
        "-L", "INFO",
        "-s", "DOWNLOAD_DELAY=5",  # Shorter delay for test
        "-s", "CONCURRENT_REQUESTS=1",
        "-s", "CLOSESPIDER_ITEMCOUNT=5",  # Stop after 5 items
        "-o", "test_output.json"
    ]
    
    print(f"🚀 Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=180  # 3 minute timeout
        )
        
        print(f"📊 Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ Spider completed successfully!")
            
            # Check output
            output_file = Path("test_output.json")
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        print(f"📊 Items scraped: {len(data)}")
                        
                        if data:
                            sample = data[0]
                            print(f"🏠 Sample property: {sample.get('estate_name_zh', 'N/A')}")
                            print(f"💰 Price: ¥{sample.get('deal_price', 'N/A'):,}")
                            print(f"📐 Area: {sample.get('area', 'N/A')}㎡")
                            print("✅ Test successful - anti-bot protection is working!")
                        else:
                            print("⚠️  No data scraped - likely blocked by anti-bot detection")
                        
                        # Cleanup
                        output_file.unlink()
                        
                    except json.JSONDecodeError:
                        print("❌ Invalid JSON output")
            else:
                print("❌ No output file created")
        else:
            print(f"❌ Spider failed with return code: {result.returncode}")
            
            # Show error output
            if result.stderr:
                print("📋 Error output:")
                print(result.stderr[-1000:])  # Last 1000 chars
                
    except subprocess.TimeoutExpired:
        print("❌ Test timed out (>3 minutes)")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    quick_test_house_spider()
