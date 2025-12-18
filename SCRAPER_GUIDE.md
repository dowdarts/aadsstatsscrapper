# Customizing the DartConnect Scraper

This guide will help you adapt the scraper to work with your specific DartConnect pages.

## 🔍 Step 1: Analyze Your DartConnect Page

Get a real DartConnect Match Recap URL from a completed match, then run:

```powershell
python scraper_diagnostic.py inspect https://www.dartconnect.com/game/recap/YOUR_MATCH_ID
```

This will:
- ✅ Fetch and analyze the page structure
- ✅ Identify tables, divs, and data patterns
- ✅ Export a cleaned HTML sample (`dartconnect_page_sample.html`)
- ✅ Provide customization hints

## 📋 Step 2: Inspect the HTML Structure

Open the exported `dartconnect_page_sample.html` in your browser:

```powershell
start dartconnect_page_sample.html
```

Then press **F12** to open DevTools and:

1. **Find the player statistics table**
   - Look for a `<table>` element with player names and stats
   - Note any `class` or `id` attributes
   - Identify the column order

2. **Check the column headers**
   - Common columns: Player Name, 3DA, First 9, 100+, 140+, 180s, High Finish
   - Your page might have different columns or order

3. **Look at a data row**
   - Right-click a player's row → Inspect
   - Count how many `<td>` cells there are
   - Note which cell contains which stat

## 🛠️ Step 3: Update the Scraper

Based on what you found, modify `scraper.py`:

### Option A: Simple Table Format

If DartConnect uses a standard table with player data in rows:

**Edit `scraper.py` around line 150-200:**

```python
def _extract_player_from_row(self, cells: List) -> Optional[Dict]:
    """Extract player statistics from a table row."""
    try:
        # Skip header rows
        if cells[0].name == 'th':
            return None
        
        # Extract text from cells
        cell_texts = [cell.get_text(strip=True) for cell in cells]
        
        # TODO: CUSTOMIZE THESE INDICES BASED ON YOUR TABLE
        # Adjust based on your column order:
        player_name = cell_texts[0]      # Column 0: Player Name
        three_dart_avg = float(cell_texts[1])  # Column 1: 3DA
        first_9_avg = float(cell_texts[2])     # Column 2: First 9
        hundreds_plus = int(cell_texts[3])     # Column 3: 100+
        one_forty_plus = int(cell_texts[4])    # Column 4: 140+
        one_eighties = int(cell_texts[5])      # Column 5: 180s
        high_finish = int(cell_texts[6])       # Column 6: High Finish
        
        stats = {
            "player_name": player_name,
            "three_dart_avg": three_dart_avg,
            "legs_played": 5,  # Default or extract if available
            "first_9_avg": first_9_avg,
            "hundreds_plus": hundreds_plus,
            "one_forty_plus": one_forty_plus,
            "one_eighties": one_eighties,
            "high_finish": high_finish
        }
        
        # Validate we have reasonable data
        if stats["three_dart_avg"] > 0:
            return stats
    
    except (ValueError, IndexError) as e:
        logger.debug(f"Error extracting player from row: {e}")
    
    return None
```

### Option B: Custom Table Selector

If you need to target a specific table by class/id:

**Edit `scraper.py` around line 125-140:**

```python
def _parse_standard_table(self, soup: BeautifulSoup) -> List[Dict]:
    """Parse statistics from standard DartConnect table format."""
    players = []
    
    # TODO: CUSTOMIZE THIS SELECTOR
    # Option 1: Find table by class
    table = soup.find('table', class_='stats-table')  # Replace with actual class
    
    # Option 2: Find table by id
    # table = soup.find('table', id='player-stats')
    
    # Option 3: Find all tables and pick one
    # tables = soup.find_all('table')
    # table = tables[0]  # or tables[1], etc.
    
    if not table:
        return players
    
    rows = table.find_all('tr')
    
    for row in rows[1:]:  # Skip header row
        cells = row.find_all(['td', 'th'])
        player_data = self._extract_player_from_row(cells)
        if player_data:
            players.append(player_data)
    
    return players
```

### Option C: Div-Based Layout

If DartConnect uses divs instead of tables:

**Add this method to the `DartConnectScraper` class:**

```python
def _parse_div_layout(self, soup: BeautifulSoup) -> List[Dict]:
    """Parse statistics from div-based layout."""
    players = []
    
    # TODO: CUSTOMIZE THESE SELECTORS
    # Find player containers
    player_divs = soup.find_all('div', class_='player-stats')  # Replace with actual class
    
    for player_div in player_divs:
        try:
            # Extract player name
            name_elem = player_div.find('span', class_='player-name')  # Customize
            player_name = name_elem.get_text(strip=True) if name_elem else None
            
            # Extract stats (customize selectors)
            avg_elem = player_div.find('span', class_='avg')
            three_dart_avg = float(avg_elem.get_text(strip=True)) if avg_elem else 0
            
            # Add more stat extractions...
            
            if player_name and three_dart_avg > 0:
                stats = {
                    "player_name": player_name,
                    "three_dart_avg": three_dart_avg,
                    "legs_played": 5,
                    "first_9_avg": three_dart_avg,
                    "hundreds_plus": 0,
                    "one_forty_plus": 0,
                    "one_eighties": 0,
                    "high_finish": 0
                }
                players.append(stats)
        
        except Exception as e:
            logger.debug(f"Error parsing player div: {e}")
            continue
    
    return players
```

## 🧪 Step 4: Test Your Changes

After modifying the scraper, test it:

```powershell
python scraper_diagnostic.py test https://www.dartconnect.com/game/recap/YOUR_MATCH_ID
```

This will show you:
- ✅ If the scraper successfully extracted player data
- ✅ What data was found
- ❌ Any errors that occurred

## 📝 Step 5: Real-World Testing

Once the diagnostic test works, try adding data through the API:

```powershell
$body = @{
    url = "https://www.dartconnect.com/game/recap/YOUR_MATCH_ID"
    event_id = 1
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/scrape" -Method POST -Body $body -ContentType "application/json"
```

Check the dashboard at <http://localhost:5000> to see if players were added correctly.

## 🐛 Common Issues & Solutions

### Issue 1: "No data found"

**Problem**: Scraper can't find the player stats table/div

**Solutions**:
- Run `inspect` command to see page structure
- Check if page requires login/authentication
- Verify the URL is a Match Recap page (not live game)
- Update table selectors in `_parse_standard_table()`

### Issue 2: "Wrong data extracted"

**Problem**: Player names are stats or vice versa

**Solutions**:
- Check column indices in `_extract_player_from_row()`
- Print `cell_texts` to see what's in each column
- Adjust indices to match your table structure

### Issue 3: "Only some players extracted"

**Problem**: Some rows are skipped

**Solutions**:
- Check if header row is being included (should skip it)
- Verify all rows have enough cells
- Add debug logging to see which rows fail

### Issue 4: "Private/restricted page"

**Problem**: DartConnect page requires authentication

**Solutions**:
- Make sure the match is public/published
- Contact tournament organizer to make recap public
- Manually enter stats using API instead of scraping

## 🎓 Example: Real DartConnect Format

Here's a complete example based on a typical DartConnect format:

**Typical DartConnect Table:**
```html
<table class="table table-bordered">
  <thead>
    <tr>
      <th>Player</th>
      <th>PPD</th>
      <th>MPR</th>
      <th>3DA</th>
      <th>First 9</th>
      <th>Tons</th>
      <th>High Finish</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>John Smith</td>
      <td>25.3</td>
      <td>1.52</td>
      <td>76.0</td>
      <td>78.5</td>
      <td>12 (2x 180, 4x 140+)</td>
      <td>121</td>
    </tr>
  </tbody>
</table>
```

**Corresponding scraper code:**

```python
def _extract_player_from_row(self, cells: List) -> Optional[Dict]:
    try:
        if cells[0].name == 'th':
            return None
        
        cell_texts = [cell.get_text(strip=True) for cell in cells]
        
        # Based on the table above:
        player_name = cell_texts[0]           # "John Smith"
        three_dart_avg = float(cell_texts[3]) # 76.0
        first_9_avg = float(cell_texts[4])    # 78.5
        high_finish = int(cell_texts[6])      # 121
        
        # Parse tons: "12 (2x 180, 4x 140+)"
        tons_text = cell_texts[5]
        one_eighties = 0
        one_forty_plus = 0
        
        if '180' in tons_text:
            match = re.search(r'(\d+)x?\s*180', tons_text)
            if match:
                one_eighties = int(match.group(1))
        
        if '140' in tons_text:
            match = re.search(r'(\d+)x?\s*140', tons_text)
            if match:
                one_forty_plus = int(match.group(1))
        
        stats = {
            "player_name": player_name,
            "three_dart_avg": three_dart_avg,
            "legs_played": 5,
            "first_9_avg": first_9_avg,
            "hundreds_plus": 0,  # Not provided in this format
            "one_forty_plus": one_forty_plus,
            "one_eighties": one_eighties,
            "high_finish": high_finish
        }
        
        return stats if stats["three_dart_avg"] > 0 else None
    
    except Exception as e:
        return None
```

## 💡 Tips

1. **Start Simple**: Get player names and 3DA working first, then add other stats
2. **Use Logging**: Add `print()` statements to see what's being extracted
3. **Test with Multiple Matches**: Different match formats might need different handling
4. **Handle Missing Data**: Not all stats might be available - use defaults
5. **Regex is Your Friend**: For parsing complex text like "2x 180, 4x 140+"

## 📞 Need Help?

If you're stuck:

1. Run the diagnostic tool and save the output
2. Check the exported HTML file
3. Look at the console logs in `scraper.py`
4. Try the example code above
5. Test with multiple different match URLs

The scraper is designed to be flexible - you just need to identify the right selectors for your specific DartConnect format!
