"""
DartConnect Scraper Diagnostic Tool
Helps you understand the HTML structure of a DartConnect page
and customize the scraper accordingly.
"""

import requests
from bs4 import BeautifulSoup
import json
from typing import Dict, List


def inspect_dartconnect_page(url: str):
    """
    Fetch and analyze a DartConnect Match Recap page structure.
    
    Args:
        url: DartConnect Match Recap URL
    """
    print("="*80)
    print("DARTCONNECT PAGE INSPECTOR")
    print("="*80)
    print(f"\nFetching: {url}\n")
    
    try:
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("✅ Page fetched successfully!\n")
        
        # Analyze page structure
        print("-"*80)
        print("PAGE STRUCTURE ANALYSIS")
        print("-"*80)
        
        # 1. Find all tables
        tables = soup.find_all('table')
        print(f"\n1. TABLES FOUND: {len(tables)}")
        for i, table in enumerate(tables, 1):
            print(f"\n   Table {i}:")
            # Get table classes/ids
            table_attrs = table.attrs
            if table_attrs:
                print(f"   Attributes: {table_attrs}")
            
            # Get headers
            headers = table.find_all('th')
            if headers:
                header_texts = [h.get_text(strip=True) for h in headers]
                print(f"   Headers: {header_texts}")
            
            # Get first row of data
            first_row = table.find('tr')
            if first_row:
                cells = first_row.find_all(['td', 'th'])
                if cells:
                    cell_texts = [c.get_text(strip=True) for c in cells[:8]]  # First 8 cells
                    print(f"   First row sample: {cell_texts}")
        
        # 2. Find divs with common class patterns
        print(f"\n2. COMMON DIV STRUCTURES:")
        common_classes = ['player', 'stats', 'score', 'match', 'recap', 'game', 'result']
        for class_name in common_classes:
            divs = soup.find_all('div', class_=lambda x: x and class_name in x.lower() if x else False)
            if divs:
                print(f"   - Divs with '{class_name}' in class: {len(divs)}")
                if len(divs) <= 3:
                    for div in divs:
                        print(f"     Classes: {div.get('class')}")
        
        # 3. Find potential player names
        print(f"\n3. POTENTIAL PLAYER DATA:")
        
        # Look for text that might be player names (longer text, capitalized)
        all_text = soup.find_all(string=True)
        potential_names = []
        for text in all_text:
            text = text.strip()
            if len(text) > 3 and len(text) < 50 and any(c.isupper() for c in text):
                parent = text.find_parent()
                if parent and parent.name not in ['script', 'style', 'meta', 'link']:
                    potential_names.append({
                        'text': text,
                        'tag': parent.name,
                        'class': parent.get('class', [])
                    })
        
        # Filter unique and likely candidates
        seen = set()
        print("   Possible player names or labels:")
        for item in potential_names[:20]:  # Show first 20
            key = item['text']
            if key not in seen and not key.isdigit() and '.' in key or ' ' in key or key[0].isupper():
                print(f"   - '{item['text']}' in <{item['tag']}> {item['class']}")
                seen.add(key)
        
        # 4. Find numeric data (stats)
        print(f"\n4. NUMERIC DATA PATTERNS:")
        numeric_cells = soup.find_all(['td', 'span', 'div'], string=lambda x: x and any(c.isdigit() for c in x) if x else False)
        
        # Group by parent structure
        stat_patterns = {}
        for cell in numeric_cells[:30]:  # Sample first 30
            text = cell.get_text(strip=True)
            parent = cell.parent
            parent_key = f"{parent.name}[{parent.get('class', ['no-class'])}]"
            
            if parent_key not in stat_patterns:
                stat_patterns[parent_key] = []
            stat_patterns[parent_key].append(text)
        
        for pattern, values in list(stat_patterns.items())[:5]:
            print(f"   {pattern}: {values[:5]}")
        
        # 5. Export raw HTML structure
        print(f"\n5. EXPORTING HTML SAMPLE...")
        
        # Save a cleaned version of the page
        with open('dartconnect_page_sample.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("   ✅ Saved to: dartconnect_page_sample.html")
        
        # 6. Generate scraper hints
        print("\n" + "="*80)
        print("SCRAPER CUSTOMIZATION HINTS")
        print("="*80)
        
        print("\n📋 Based on this analysis, here's what to look for:\n")
        
        if tables:
            print("1. TABLE-BASED SCRAPING:")
            print("   - Focus on modifying _parse_standard_table() method")
            print(f"   - You have {len(tables)} table(s) to work with")
            print("   - Look for tables with player stats (check headers)")
            print("   - Typical columns: Player Name, 3DA, First 9, 100+, 140+, 180s, High Finish")
        
        print("\n2. KEY SELECTORS TO TRY:")
        print("   soup.find_all('table')  # All tables")
        print("   soup.find('table', class_='...')  # Specific table")
        print("   table.find_all('tr')  # All rows")
        print("   row.find_all('td')  # All cells in a row")
        
        print("\n3. NEXT STEPS:")
        print("   a) Open 'dartconnect_page_sample.html' in a browser")
        print("   b) Use browser DevTools (F12) to inspect the page structure")
        print("   c) Identify the exact table/div containing player stats")
        print("   d) Note the HTML classes/IDs used")
        print("   e) Update scraper.py with the correct selectors")
        
        print("\n4. TESTING:")
        print("   python scraper_diagnostic.py test YOUR_URL")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching page: {e}")
        print("\nPossible reasons:")
        print("- Invalid URL")
        print("- Page requires authentication")
        print("- Network issues")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_scraper_with_url(url: str):
    """
    Test the current scraper implementation with a URL.
    """
    print("="*80)
    print("TESTING CURRENT SCRAPER")
    print("="*80)
    print(f"\nTesting URL: {url}\n")
    
    try:
        from scraper import DartConnectScraper
        
        scraper = DartConnectScraper()
        results = scraper.scrape_match_recap(url)
        
        if results:
            print(f"✅ Successfully scraped {len(results)} player(s)!\n")
            print("Results:")
            print(json.dumps(results, indent=2))
        else:
            print("❌ Scraper returned no results.")
            print("\nThis means the scraper couldn't find player data.")
            print("Run: python scraper_diagnostic.py inspect YOUR_URL")
            print("to analyze the page structure and customize the scraper.")
    
    except Exception as e:
        print(f"❌ Error testing scraper: {e}")


def generate_scraper_template(url: str):
    """
    Generate a custom scraper template based on page analysis.
    """
    print("="*80)
    print("GENERATING CUSTOM SCRAPER TEMPLATE")
    print("="*80)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the most promising table
        tables = soup.find_all('table')
        
        template = '''
def _parse_dartconnect_custom(self, soup: BeautifulSoup) -> List[Dict]:
    """
    Custom parser for your DartConnect format.
    Modify this based on your page structure.
    """
    players = []
    
    # TODO: Update this selector to match your table
    table = soup.find('table')  # or soup.find('table', class_='your-class')
    
    if not table:
        return players
    
    rows = table.find_all('tr')
    
    for row in rows[1:]:  # Skip header row
        cells = row.find_all('td')
        
        if len(cells) < 6:  # Adjust based on your column count
            continue
        
        try:
            # TODO: Adjust these indices based on your table structure
            player_name = cells[0].get_text(strip=True)
            three_dart_avg = float(cells[1].get_text(strip=True))
            
            # Extract other stats...
            # first_9_avg = float(cells[2].get_text(strip=True))
            # hundreds_plus = int(cells[3].get_text(strip=True))
            # etc...
            
            stats = {
                "player_name": player_name,
                "three_dart_avg": three_dart_avg,
                "legs_played": 5,  # TODO: Extract if available
                "first_9_avg": three_dart_avg,  # TODO: Extract if available
                "hundreds_plus": 0,  # TODO: Extract
                "one_forty_plus": 0,  # TODO: Extract
                "one_eighties": 0,  # TODO: Extract
                "high_finish": 0  # TODO: Extract
            }
            
            players.append(stats)
        
        except (ValueError, IndexError) as e:
            continue
    
    return players
'''
        
        print("Generated template:")
        print(template)
        
        print("\n📋 To use this template:")
        print("1. Add this method to the DartConnectScraper class in scraper.py")
        print("2. Call it from scrape_match_recap() method")
        print("3. Adjust the selectors and indices based on your page structure")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("DartConnect Scraper Diagnostic Tool")
        print("\nUsage:")
        print("  python scraper_diagnostic.py inspect <URL>    - Analyze page structure")
        print("  python scraper_diagnostic.py test <URL>       - Test current scraper")
        print("  python scraper_diagnostic.py template <URL>   - Generate scraper template")
        print("\nExample:")
        print("  python scraper_diagnostic.py inspect https://www.dartconnect.com/game/recap/12345")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if len(sys.argv) < 3:
        print("❌ Error: URL required")
        print("Usage: python scraper_diagnostic.py <command> <URL>")
        sys.exit(1)
    
    url = sys.argv[2]
    
    if command == "inspect":
        inspect_dartconnect_page(url)
    elif command == "test":
        test_scraper_with_url(url)
    elif command == "template":
        generate_scraper_template(url)
    else:
        print(f"❌ Unknown command: {command}")
        print("Valid commands: inspect, test, template")
