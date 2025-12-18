"""
Extract match URLs from DartConnect event page

This script parses the event page HTML/JavaScript to find all match recap URLs.
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import html as html_module

def extract_match_urls_from_event(event_url):
    """
    Extract all match recap URLs from a DartConnect event page
    
    Args:
        event_url: URL to the event matches page (e.g., https://tv.dartconnect.com/event/mt_joe6163l_1/matches)
    
    Returns:
        List of match recap URLs
    """
    print(f"Fetching event page: {event_url}")
    
    response = requests.get(event_url)
    if response.status_code != 200:
        print(f"❌ Failed to fetch page: {response.status_code}")
        return []
    
    print(f"✅ Page fetched ({len(response.text)} bytes)")
    
    match_urls = []
    
    # Method 1: Look for match IDs in JavaScript/JSON data
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Check Inertia.js data
    app_div = soup.find('div', {'id': 'app'})
    if app_div and app_div.has_attr('data-page'):
        print("📄 Analyzing Inertia.js data...")
        
        try:
            page_data_encoded = app_div['data-page']
            page_data = html_module.unescape(page_data_encoded)
            
            # Search for match IDs in the JSON data
            # Match IDs are 24-character hex strings
            match_id_pattern = r'[0-9a-f]{24}'
            
            # Also look for specific patterns that might contain match IDs
            patterns_to_check = [
                page_data,  # Full JSON
                str(page_data)  # String representation
            ]
            
            all_matches = []
            for pattern_text in patterns_to_check:
                found = re.findall(match_id_pattern, pattern_text)
                all_matches.extend(found)
            
            # Deduplicate and filter out common non-match IDs
            unique_ids = list(set(all_matches))
            
            # Filter out IDs that are clearly not match IDs (too common, etc.)
            filtered_ids = []
            for match_id in unique_ids:
                # Basic validation - match IDs shouldn't be all the same digit
                if len(set(match_id)) > 3:  # At least 4 different hex characters
                    filtered_ids.append(match_id)
            
            print(f"  Found {len(unique_ids)} potential IDs, {len(filtered_ids)} after filtering")
            
            # Convert to recap URLs
            for match_id in filtered_ids:
                recap_url = f"https://recap.dartconnect.com/matches/{match_id}"
                match_urls.append(recap_url)
        
        except Exception as e:
            print(f"  ⚠ Error parsing Inertia data: {e}")
    
    # Method 2: Look for recap URLs directly in HTML
    html_text = response.text
    recap_pattern = r'https?://recap\.dartconnect\.com/matches/[0-9a-f]{24}'
    found_urls = re.findall(recap_pattern, html_text)
    
    if found_urls:
        print(f"📄 Found {len(found_urls)} URLs in HTML")
        for url in found_urls:
            if url not in match_urls:
                match_urls.append(url)
    
    # Deduplicate final list
    match_urls = list(set(match_urls))
    
    return match_urls

def main():
    """
    Main function - extract and display match URLs
    """
    print("=" * 70)
    print("DartConnect Event Match URL Extractor")
    print("=" * 70)
    
    # Get event URL from user
    default_url = "https://tv.dartconnect.com/event/mt_joe6163l_1/matches"
    print(f"\nDefault: {default_url}")
    event_url = input("Enter event URL (or press Enter for default): ").strip()
    
    if not event_url:
        event_url = default_url
    
    print()
    
    # Extract URLs
    match_urls = extract_match_urls_from_event(event_url)
    
    if not match_urls:
        print("\n❌ No match URLs found")
        return
    
    # Display results
    print(f"\n{'=' * 70}")
    print(f"FOUND {len(match_urls)} MATCH URLs")
    print("=" * 70)
    
    for i, url in enumerate(sorted(match_urls), 1):
        print(f"{i:3}. {url}")
    
    # Save to file
    output_file = "match_urls.txt"
    with open(output_file, 'w') as f:
        for url in sorted(match_urls):
            f.write(url + '\n')
    
    print(f"\n✅ URLs saved to {output_file}")
    print(f"\n💡 You can now use these URLs with batch_scrape_event.py")
    print(f"   Or pipe them directly:")
    print(f"   cat match_urls.txt | python batch_scrape_event.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
