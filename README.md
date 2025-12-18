# AADS Darts Scraper & Broadcast Engine

**Atlantic Amateur Darts Series** - Professional statistics tracking and live broadcast overlay system.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green)
![Status](https://img.shields.io/badge/Status-Production-success)

## 📋 Overview

A comprehensive Python-based system that scrapes DartConnect Match Recap logs, aggregates player statistics across a 7-event series, and outputs a professional HTML/CSS leaderboard perfect for live stream overlays and website embedding.

### Key Features

- 🎯 **Automated Scraping**: Extract player stats from DartConnect Match Recap pages
- 📊 **Weighted Averages**: Fair ranking system using weighted 3-dart averages across all legs
- 🏆 **Qualification Tracking**: Automatic tracking of event winners and Tournament of Champions qualification
- 📺 **Broadcast Mode**: Clean overlay mode for OBS/streaming software (transparent background, chroma-key ready)
- 🔄 **Auto-Refresh**: Real-time updates with 30-second auto-refresh
- 🎨 **Modern UI**: Professional dark theme with gold accents
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile

## 🏗️ System Architecture

```text
aadsstatsscrapper/
├── app.py                    # Flask web server & API
├── database_manager.py       # Data persistence & statistics logic
├── scraper.py               # DartConnect scraper
├── requirements.txt         # Python dependencies
├── aads_master_db.json      # Statistics database (auto-generated)
├── templates/
│   └── index.html          # Main dashboard template
└── static/
    ├── css/
    │   └── style.css       # Professional styling
    └── js/
        └── overlay.js      # Frontend logic & auto-refresh
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone or download this repository**

2. **Install dependencies**:

   ```powershell
   pip install -r requirements.txt
   ```

3. **Run the server**:

   ```powershell
   python app.py
   ```

4. **Open your browser**:
   Navigate to `http://localhost:5000`

## 📖 Usage Guide

### Adding Player Statistics

#### Method 1: Scrape DartConnect URL (Automated)

Use the API to automatically scrape a DartConnect Match Recap page:

```powershell
# Using PowerShell
$body = @{
    url = "https://www.dartconnect.com/game/recap/MATCH_ID"
    event_id = 1
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/scrape" -Method POST -Body $body -ContentType "application/json"
```

#### Method 2: Manual Entry via API


Add statistics manually through the API:

```powershell
$body = @{
    player_name = "John Doe"
    event_id = 1
    stats = @{
        three_dart_avg = 75.5
        legs_played = 5
        first_9_avg = 80.2
        hundreds_plus = 12
        one_forty_plus = 4
        one_eighties = 2
        high_finish = 120
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/add-stats" -Method POST -Body $body -ContentType "application/json"
```

#### Method 3: Python Script


```python
from database_manager import AADSDataManager

manager = AADSDataManager()

stats = {
    "three_dart_avg": 75.5,
    "legs_played": 5,
    "first_9_avg": 80.2,
    "hundreds_plus": 12,
    "one_forty_plus": 4,
    "one_eighties": 2,
    "high_finish": 120
}

manager.add_match_stats("John Doe", event_id=1, stats_dict=stats)
```

### Setting Event Winners


Mark a player as the winner of an event (grants qualification for events 1-6):

```powershell
$body = @{
    event_id = 1
    player_name = "John Doe"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/set-winner" -Method POST -Body $body -ContentType "application/json"
```

### Using Broadcast Mode


The dashboard includes a **Broadcast Mode** designed for live streaming:

1. Click the **📺 Broadcast Mode** button in the dashboard
2. The interface becomes transparent and removes unnecessary controls
3. In OBS Studio:
   - Add a **Browser Source**
   - URL: `http://localhost:5000`
   - Width: 1920, Height: 1080 (or your stream resolution)
   - Check **Shutdown source when not visible**
   - Refresh browser when source becomes active: ✓

The transparent background allows you to overlay the leaderboard on your stream.

## 🔌 API Reference

### GET Endpoints

#### Get Leaderboard

```http
GET /api/stats
Query Parameters:
  - sort_by (optional): weighted_3da, total_180s, total_140s, highest_finish
  - player (optional): Get specific player stats

Response:
{
  "success": true,
  "series_info": {...},
  "leaderboard": [...],
  "total_players": 10,
  "last_updated": "2025-12-18T10:30:00"
}
```

#### Get Qualified Players

```http
GET /api/qualified

Response:
{
  "success": true,
  "qualified_players": [...],
  "total_qualified": 6
}
```

#### Get Event Information

```http
GET /api/events?event_id=1

Response:
{
  "success": true,
  "event": {
    "event_id": 1,
    "participants": [...],
    "winner": "John Doe",
    "completed": true
  }
}
```

### POST Endpoints

#### Scrape DartConnect URL

```http
POST /api/scrape
Content-Type: application/json

Body:
{
  "url": "https://www.dartconnect.com/game/recap/MATCH_ID",
  "event_id": 1
}
```

#### Add Statistics Manually

```http
POST /api/add-stats
Content-Type: application/json

Body:
{
  "player_name": "John Doe",
  "event_id": 1,
  "stats": {
    "three_dart_avg": 75.5,
    "legs_played": 5,
    "first_9_avg": 80.2,
    "hundreds_plus": 12,
    "one_forty_plus": 4,
    "one_eighties": 2,
    "high_finish": 120
  }
}
```

#### Set Event Winner

```http
POST /api/set-winner
Content-Type: application/json

Body:
{
  "event_id": 1,
  "player_name": "John Doe"
}
```

## 📊 Statistics Explained

### Weighted 3-Dart Average (3DA)

The system uses a **weighted average** to ensure fair rankings:

```text
Weighted 3DA = (Sum of all leg averages) / (Total legs played)
```

This means:

- Players who compete in more events have more data points
- A player with 15 legs at 75.0 avg ranks higher than a player with 5 legs at 75.0 avg
- Reflects consistency and participation

### Tracked Statistics

- **3-Dart Average (3DA)**: Weighted average across all legs
- **First 9 Average**: Average of the first 9 darts in each leg
- **180s**: Maximum 3-dart score (180 points)
- **140+**: Scores of 140 or higher
- **100+**: Scores of 100 or higher
- **High Finish**: Highest checkout scored
- **Events Played**: Number of events participated in
- **Qualified**: Whether the player won a qualifying event

## 🏆 Series Structure

### Event Format

- **Total Events**: 7
- **Events 1-6**: Qualifying tournaments
  - Winner earns qualification to Event 7
  - 10 players per event (2 groups of 5)
  - Round Robin → Knockout format
- **Event 7**: Tournament of Champions
  - Only qualified winners compete

### Qualification Rules

- Win any of Events 1-6 to qualify for Event 7
- A player can compete in multiple qualifying events
- Each event win counts toward their overall statistics
- Event 7 winner becomes the Series Champion

## 🎨 Customization

### Modifying the Theme

Edit [static/css/style.css](static/css/style.css) and adjust the CSS variables:

```css
:root {
    --primary-bg: #0a0e1a;       /* Main background */
    --gold: #ffd700;              /* Accent color */
    --text-primary: #ffffff;      /* Primary text */
    /* ... more variables ... */
}
```

### Adjusting Auto-Refresh Rate


Edit [static/js/overlay.js](static/js/overlay.js):

```javascript
const CONFIG = {
    API_ENDPOINT: '/api/stats',
    REFRESH_INTERVAL: 30000,  // Change to desired milliseconds
    SORT_BY_DEFAULT: 'weighted_3da'
};
```

### Customizing the Scraper


The scraper in [scraper.py](scraper.py) uses two parsing methods:

1. **Standard Table Format**: Parses HTML tables
2. **Alternative Format**: Uses regex patterns for div-based layouts

To adapt to your specific DartConnect format:

1. Inspect the DartConnect Recap page HTML structure
2. Modify `_parse_standard_table()` or `_parse_alternative_format()` methods
3. Test with actual URLs and verify extracted data

## 🐛 Troubleshooting


### Server Won't Start

**Error**: `Address already in use`

**Solution**: Another process is using port 5000

```powershell
# Find and kill the process using port 5000
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force

# Or run on a different port
python app.py --port 5001
```

### Scraper Returns No Data

**Possible Causes**:

1. DartConnect page is private/restricted
2. HTML structure changed
3. Invalid URL format

**Solution**:

- Check the URL is accessible in a browser
- Review scraper logs for specific errors
- Test with the example scraper script:

  ```python
  from scraper import DartConnectScraper
  scraper = DartConnectScraper()
  stats = scraper.scrape_match_recap("YOUR_URL")
  print(stats)
  ```

### Database Corruption

**Error**: `JSON decode error`

**Solution**:

```python
from database_manager import AADSDataManager
manager = AADSDataManager()
manager.reset_database()  # Caution: Deletes all data
```

Or manually delete `aads_master_db.json` and restart the server.

### Styles Not Loading

**Error**: 404 errors for CSS/JS files

**Solution**: Ensure directory structure is correct:

```text
aadsstatsscrapper/
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── overlay.js
└── templates/
    └── index.html
```

## 🔒 Security Considerations

### Production Deployment

For production use:

1. **Disable Debug Mode**: Change `app.run(debug=True)` to `debug=False`
2. **Use a Production Server**: Deploy with Gunicorn or uWSGI
3. **Add Authentication**: Protect POST endpoints with API keys
4. **Enable HTTPS**: Use SSL certificates for secure connections
5. **Rate Limiting**: Add rate limiting to prevent abuse

Example with Gunicorn:

```powershell
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📝 License

This project is provided as-is for the Atlantic Amateur Darts Series. Modify and use as needed for your events.

## 🤝 Contributing

To contribute or suggest improvements:

1. Test your changes thoroughly
2. Document any new features
3. Ensure backward compatibility with existing database format

## 📞 Support

For issues specific to:

- **DartConnect scraping**: Check [scraper.py](scraper.py) logs
- **Database issues**: Review [database_manager.py](database_manager.py)
- **Display problems**: Inspect browser console for JavaScript errors
- **API issues**: Check Flask server logs

## 🎯 Roadmap

Future enhancements:

- [ ] Player profile pages with detailed match history
- [ ] Head-to-head comparison tool
- [ ] Export to PDF/CSV
- [ ] Mobile app
- [ ] Real-time match scoring integration
- [ ] Tournament bracket visualization
- [ ] Player performance analytics and trends

## 📚 Additional Resources



- [DartConnect Website](https://www.dartconnect.com)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [OBS Studio](https://obsproject.com/)

---

**Built for the Atlantic Amateur Darts Series** 🎯

*Professional darts statistics tracking made simple.*
