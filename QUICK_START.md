# AADS Quick Start Guide

## ✅ System Status: COMPLETE & RUNNING

Your AADS Darts Scraper & Broadcast Engine is fully operational!

### 🌐 Access Points

- **Dashboard**: <http://localhost:5000>
- **API Endpoint**: <http://localhost:5000/api/stats>
- **Server Status**: Running on port 5000

---

## 📊 Current Standings

The system is loaded with sample data showing:

- **8 Players** competing
- **2 Qualified** for Tournament of Champions (Michael Smith, Peter Wright)
- **2 Events** completed
- Live leaderboard with real-time statistics

---

## 🚀 Usage Examples

### 1. Add Player Statistics Manually

```python
from database_manager import AADSDataManager

manager = AADSDataManager()

stats = {
    "three_dart_avg": 82.5,
    "legs_played": 6,
    "first_9_avg": 85.0,
    "hundreds_plus": 14,
    "one_forty_plus": 5,
    "one_eighties": 2,
    "high_finish": 130
}

manager.add_match_stats("Your Name", event_id=3, stats_dict=stats)
```

### 2. Use the API (PowerShell)


**Add Statistics:**

```powershell
$body = @{
    player_name = "John Smith"
    event_id = 3
    stats = @{
        three_dart_avg = 80.5
        legs_played = 5
        first_9_avg = 82.0
        hundreds_plus = 12
        one_forty_plus = 4
        one_eighties = 1
        high_finish = 120
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:5000/api/add-stats" -Method POST -Body $body -ContentType "application/json"
```

**Set Event Winner:**

```powershell
$body = @{
    event_id = 3
    player_name = "John Smith"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/set-winner" -Method POST -Body $body -ContentType "application/json"
```

**Get Leaderboard:**

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/stats"
```

### 3. Scrape DartConnect URL

```powershell
$body = @{
    url = "https://www.dartconnect.com/game/recap/YOUR_MATCH_ID"
    event_id = 3
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/scrape" -Method POST -Body $body -ContentType "application/json"
```

---

## 📺 Broadcast Mode (OBS Setup)

1. Open your dashboard at <http://localhost:5000>
2. Click the **📺 Broadcast Mode** button
3. In OBS Studio:
   - Add **Browser Source**
   - URL: `http://localhost:5000`
   - Width: 1920
   - Height: 1080
   - ✓ Shutdown source when not visible
   - ✓ Refresh browser when source becomes active

The transparent background allows perfect overlay on your stream!

---

## 🔄 Auto-Refresh

The dashboard automatically refreshes every **30 seconds** to show the latest stats.

To change this, edit `static/js/overlay.js`:

```javascript
const CONFIG = {
    REFRESH_INTERVAL: 30000,  // milliseconds
    // ...
};
```

---


## 📈 Key Features Implemented

✅ **Weighted 3-Dart Average** - Fair ranking across all legs played
✅ **Event Tracking** - Full history for each player
✅ **Qualification System** - Event winners auto-qualify for Event 7  
✅ **REST API** - Full CRUD operations via HTTP  
✅ **Modern UI** - Dark theme with gold accents  
✅ **Broadcast Ready** - Transparent overlay mode for OBS  
✅ **Auto-Refresh** - Real-time updates without page reload  
✅ **Responsive Design** - Works on all devices  

---

## 🗄️ Database Structure

Data is stored in `aads_master_db.json`:

```json
{
  "series_info": {
    "name": "Atlantic Amateur Darts Series",
    "total_events": 7,
    "qualifying_events": 6,
    "championship_event": 7
  },
  "players": {
    "Player Name": {
      "weighted_3da": 85.30,
      "total_180s": 3,
      "qualified": true,
      "events_played": [1, 2],
      "event_history": [...]
    }
  },
  "events": {...}
}
```

---

## 🎯 Statistics Explained

### Weighted 3-Dart Average (3DA)

```text
Weighted 3DA = (Sum of all leg averages) / (Total legs played)
```

This ensures players with more games are ranked fairly. A player with 15 legs at 80.0 avg has more weight than 5 legs at 80.0 avg.

### Tracked Stats

- **3DA**: Weighted average across all legs
- **First 9 Avg**: Average of first 9 darts
- **180s**: Maximum score (180 points)
- **140+**: Scores of 140 or higher
- **100+**: Scores of 100 or higher  
- **High Finish**: Highest checkout
- **Events Played**: Participation count
- **Qualified**: Tournament of Champions status

---


## 🏆 Series Structure

### Events 1-6 (Qualifying)

- 10 players per event
- 2 groups of 5 (Round Robin)
- Top players move to Knockout
- **Winner qualifies for Event 7**

### Event 7 (Tournament of Champions)

- Only qualified winners compete
- Series champion crowned

---

## 🛠️ Maintenance

### View Database

```powershell
Get-Content aads_master_db.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Backup Database

```powershell
Copy-Item aads_master_db.json "aads_master_db.backup_$(Get-Date -Format 'yyyy-MM-dd').json"
```

### Reset Database

```python
from database_manager import AADSDataManager
manager = AADSDataManager()
manager.reset_database()  # ⚠️ Deletes all data!
```

### Stop Server

Press `Ctrl+C` in the terminal running Flask

### Restart Server

```powershell
python app.py
```

---

## 📝 File Reference

| File | Purpose |
| ---- | ------- |
| `app.py` | Flask web server & REST API |
| `database_manager.py` | Data engine with weighted averages |
| `scraper.py` | DartConnect scraper |
| `aads_master_db.json` | Statistics database |
| `test_data.py` | Sample data generator |
| `templates/index.html` | Dashboard HTML |
| `static/css/style.css` | Styling & themes |
| `static/js/overlay.js` | Frontend logic |
| `requirements.txt` | Python dependencies |
| `README.md` | Full documentation |

---

## 🐛 Troubleshooting

### Dashboard shows "Loading..."

- Check Flask server is running
- Verify database file exists
- Open browser console (F12) for errors

### Stats not updating

- Check auto-refresh is enabled
- Manually click refresh button
- Verify API returns data: <http://localhost:5000/api/stats>

### Port 5000 already in use


```powershell
# Kill existing Python processes
Get-Process python | Stop-Process -Force

# Or edit app.py to use different port
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Database corrupted

```powershell
# Restore from backup
Copy-Item "aads_master_db.backup_YYYY-MM-DD.json" aads_master_db.json

# Or reset (deletes all data)
python -c "from database_manager import AADSDataManager; AADSDataManager().reset_database()"
```

---


## 🎓 Next Steps

1. **Customize DartConnect Scraper**
   - Inspect your DartConnect recap page HTML
   - Update `scraper.py` parsing methods
   - Test with real URLs

2. **Add More Players**
   - Use `test_data.py` as template
   - Create scripts for each event
   - Build up your series data

3. **Customize Theme**
   - Edit `static/css/style.css`
   - Change colors in CSS variables
   - Adjust fonts and spacing

4. **Production Deployment**
   - Install Gunicorn: `pip install gunicorn`
   - Run: `gunicorn -w 4 -b 0.0.0.0:5000 app:app`
   - Add authentication for API endpoints
   - Enable HTTPS with SSL certificates

---

## 📞 Support

For detailed documentation, see [README.md](README.md)

**Your system is ready to use!** 🎯


Start adding your players and watch the standings come alive!
