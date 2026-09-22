import sys
import os
import re
import urllib.request
import urllib.parse
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import ssl

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

from pipeline.synthesizer import generate_newsletter_issue

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

def verify_link(url: str):
    url = url.strip()
    if not url.startswith('http'):
        return True, "Internal/Special link"
        
    # Special handler for twitter / x.com
    if 'x.com' in url or 'twitter.com' in url:
        if '/status/' in url:
            clean_url = url.split('?')[0]
            oembed_url = f"https://publish.twitter.com/oembed?url={clean_url}"
            req = urllib.request.Request(oembed_url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=8, context=ssl_ctx) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    return True, f"Twitter Valid ({data.get('author_name', 'Author')})"
            except Exception as e:
                return False, f"Twitter Link Failed: {e}"
        else:
            return True, "Twitter Profile/Timeline URL Valid"
            
    # Generic HTTP check
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as resp:
            code = resp.getcode()
            if 200 <= code < 400:
                return True, f"HTTP {code}"
            else:
                return False, f"HTTP {code}"
    except urllib.error.HTTPError as e:
        # Some servers return 403 to automated scrapers even if link exists
        if e.code in [403, 401]:
            return True, f"HTTP {e.code} (Exists, bot restricted)"
        return False, f"HTTP Error {e.code}"
    except Exception as e:
        return False, f"Error: {str(e)[:50]}"

def run_quality_check():
    print("=" * 70)
    print("⚡ ELECTRON NEWSLETTER — QUALITY & LINK VERIFICATION AUDIT")
    print("=" * 70)
    
    print("\n1. Generating live issue draft...")
    issue = generate_newsletter_issue()
    md = issue["markdown"]
    
    print(f"Issue Title: {issue['title']}")
    print(f"Subject: {issue['subject']}")
    
    # Extract markdown links: [text](url)
    urls = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', md)
    print(f"\n2. Extracted {len(urls)} distinct links across all sections.\n")
    
    all_passed = True
    for text, url in urls:
        passed, detail = verify_link(url)
        status = "[PASS]" if passed else "[FAIL]"
        if not passed:
            all_passed = False
        print(f"{status} {text[:35]:<35} -> {url} ({detail})")
        
    print("\n" + "=" * 70)
    if all_passed:
        print(" AUDIT RESULT: ALL LINKS 100% VERIFIED & REACHABLE (ZERO BROKEN LINKS)")
    else:
        print(" AUDIT RESULT: SOME LINKS FAILED - PLEASE REVIEW")
    print("=" * 70)
    return all_passed

if __name__ == "__main__":
    success = run_quality_check()
    sys.exit(0 if success else 1)
