# AADS Event Scraping Guide

## You now have a complete toolkit to scrape DartConnect matches

### ✅ What's Working

The scraper has been **successfully customized** for DartConnect's Inertia.js format:

- **Tested with**: `https://recap.dartconnect.com/matches/688e00ccf4fc02e124e7131c`
- **Results**: Gerry Johnston (63.98 avg), Steve Rushton (61.23 avg)

### 🛠️ Available Tools

1. **Individual Match Scraping**

   ```bash
   python test_real_scrape.py
   ```

2. **Batch Event Scraping** (Interactive)

   ```bash
   python batch_scrape_event.py
   ```

3. **Match URL Extraction** (From event pages)

   ```bash
   python extract_match_urls.py
   ```

4. **API Integration** (Via Flask server)

   ```bash
   # Start server
   python app.py
   
   # Then POST to http://localhost:5000/api/scrape
   # Body: {"url": "https://recap.dartconnect.com/matches/...", "event_id": 1}
   ```

### 📋 Recommended Workflow

#### Option 1: Manual Batch Import

1. Collect match recap URLs from your tournament
2. Run `python batch_scrape_event.py`
3. Enter event number (1-7)
4. Paste URLs one by one
5. View results at `http://localhost:5000`

#### Option 2: Semi-Automated

1. Run `python extract_match_urls.py` on event page
2. Copy URLs from `match_urls.txt`
3. Use batch scraper with the URLs

#### Option 3: API Integration

- Use the `/api/scrape` endpoint for programmatic access
- Integrate with external tools/scripts

### 🔧 Next Steps

1. **Clear Test Data** (when ready for production):

   ```python
   from database_manager import AADSDataManager
   db = AADSDataManager()
   # db.reset_database()  # Uncomment to clear all data
   ```

2. **Import Your Tournament**:

   - Use batch scraper for each event
   - Set event winners via dashboard or API
   - Monitor qualification status

3. **Setup OBS Stream**:

   - Visit `http://localhost:5000`
   - Click "Broadcast Mode"
   - Add as Browser Source in OBS

### 📊 Current Database Status

- **8 test players** loaded
- **Events 1-2** completed  
- **2 players qualified** for Tournament of Champions
- **Test data** ready to be replaced with real tournament data

### 🌐 Dashboard Access

- **Local**: <http://localhost:5000>
- **Network**: <http://10.0.0.90:5000> (if accessible)
- **Auto-refresh**: Every 30 seconds
- **Broadcast mode**: Transparent background for OBS

---

## 🚀 Ready to Import Your Tournament

The system is production-ready. Choose your preferred method above and start importing your Atlantic Amateur Darts Series matches.