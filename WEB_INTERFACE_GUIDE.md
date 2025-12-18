# 🎯 AADS Web Interface - Complete User Guide

## 🌟 Overview

You now have a **complete web-based interface** for managing your Atlantic Amateur Darts Series data! The system includes:

- **Live Dashboard** with auto-refreshing leaderboard
- **Single Match Scraping** via web forms
- **Event Batch Scraping** from DartConnect event pages
- **Event Management** (set winners, manage qualifications)
- **Database Management** tools
- **Broadcast Mode** for OBS integration

## 🚀 Accessing the Interface

**Primary URL**: <http://localhost:5000>
**Network Access**: <http://10.0.0.90:5000> (if available on network)

## 📱 Interface Features

### 1. Main Dashboard
- **Real-time leaderboard** with current standings
- **Series information** (events played, qualifications, etc.)
- **Auto-refresh** every 30 seconds
- **Broadcast mode toggle** for streaming

### 2. Management Panel
Click the **"⚙️ Manage"** button to access:

#### 📊 Single Match Scraping
- **Input**: Match recap URL from DartConnect
- **Select**: Event number (1-7)
- **Action**: Scrapes and adds player statistics immediately
- **Example**: `https://recap.dartconnect.com/matches/688e00ccf4fc02e124e7131c`

#### 🏆 Event Batch Scraping
- **Input**: Event page URL from DartConnect
- **Select**: Event number (1-7)
- **Action**: Automatically finds and scrapes ALL matches from the event
- **Example**: `https://tv.dartconnect.com/event/mt_joe6163l_1/matches`

#### ⚙️ Event Management
- **Set Winners**: Choose event and player to set as winner
- **Qualification**: Winners of Events 1-6 automatically qualify for TOC
- **Player Selection**: Dropdown populated with current players and averages

#### ⚠️ Database Management
- **Reset Database**: Complete data wipe (requires confirmation)
- **Use carefully**: This action cannot be undone

### 3. Status Messages
- **Real-time feedback** for all operations
- **Color-coded messages**: Success (green), Error (red), Info (blue), Warning (yellow)
- **Auto-dismiss** after 5 seconds
- **Scroll area** for multiple messages

## 🔧 How to Use

### Adding Match Data

#### Option A: Single Match
1. Click **"⚙️ Manage"** to open management panel
2. In **"📊 Scrape Match"** section:
   - Paste DartConnect match recap URL
   - Select event number (1-7)
   - Click **"Scrape Match"**
3. Watch status messages for progress
4. Leaderboard updates automatically

#### Option B: Entire Event
1. Open management panel
2. In **"🏆 Scrape Event"** section:
   - Paste DartConnect event page URL
   - Select event number (1-7)
   - Click **"Scrape All Matches"**
3. System automatically:
   - Extracts all match URLs from event page
   - Scrapes each match individually
   - Adds all player statistics
   - Reports success/failure counts

### Managing Events
1. Open management panel
2. In **"⚙️ Event Management"** section:
   - Select event (1-6 for qualifying events)
   - Choose winner from dropdown
   - Click **"Set Winner"**
3. Winner automatically qualifies for Tournament of Champions

### Viewing Data
- **Main dashboard** shows live leaderboard
- **Sort by**: 3-dart average (default), events played, 180s, etc.
- **Qualification status**: Green "QUALIFIED" badge for qualified players
- **Event history**: Hover over player names for details

## 🎥 Broadcast Mode

For live streaming/OBS integration:

1. Click **"📺 Broadcast Mode"** toggle
2. Interface becomes transparent and optimized for overlay
3. Add as **Browser Source** in OBS
4. Use URL: `http://localhost:5000`

## 📊 API Endpoints

The web interface uses these REST API endpoints (also available for custom integrations):

- `GET /api/stats` - Current leaderboard
- `GET /api/qualified` - Qualified players list
- `GET /api/events` - Event information
- `POST /api/scrape` - Single match scraping
- `POST /api/scrape-event` - Event batch scraping
- `POST /api/set-winner` - Set event winner
- `POST /api/reset-database` - Reset all data

## 🔐 Security Notes

- Interface runs on **local network only**
- **No authentication** required (local use)
- **Database reset** requires confirmation dialog
- All operations are **logged** for troubleshooting

## 🚨 Troubleshooting

### Common Issues

1. **"No match URLs found"**
   - Check event page URL is correct
   - Ensure event has completed matches
   - Try individual match URLs instead

2. **"Failed to fetch"**
   - Check DartConnect URL is accessible
   - Verify internet connection
   - Some matches may be private

3. **"Player not found"**
   - Ensure players have been added via scraping first
   - Check spelling in winner selection

### Error Recovery
- All operations show **detailed error messages**
- Failed scrapes **don't affect** existing data
- Use **status messages** to diagnose issues
- **Refresh page** if interface becomes unresponsive

## ✅ Production Ready

Your AADS system is now **production-ready** with:

- ✅ **Full web interface** for data management
- ✅ **Automated scraping** from DartConnect
- ✅ **Real-time dashboard** with live updates
- ✅ **Event management** and qualification tracking
- ✅ **OBS integration** for live streaming
- ✅ **Error handling** and user feedback
- ✅ **Mobile-responsive** design

## 🎉 Success!

You can now manage your entire Atlantic Amateur Darts Series through the web interface. Simply navigate to <http://localhost:5000> and start adding your tournament data!