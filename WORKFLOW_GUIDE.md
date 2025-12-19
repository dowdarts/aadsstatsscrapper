# AADS System Workflow

## 📊 Complete Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    AADS SYSTEM WORKFLOW                      │
└─────────────────────────────────────────────────────────────┘

STEP 1: DATA INPUT (Admin Interface)
┌──────────────────────────────────────┐
│  https://dowdarts.github.io/         │
│  aadsstatsscrapper/index.html        │
│                                       │
│  1. Go to "Event Manager" tab        │
│  2. Enter event URL                  │
│  3. Enter event number (1-7)         │
│  4. Click "Extract & Scrape"         │
└──────────────┬───────────────────────┘
               │
               ▼
        ┌──────────────┐
        │   SCRAPING    │
        │   PROCESS     │
        │               │
        │ • Extract IDs │
        │ • Parse HTML  │
        │ • Get Stats   │
        └──────┬────────┘
               │
               ▼
        ┌──────────────────┐
        │    SUPABASE      │
        │    DATABASE      │
        │                  │
        │ • events         │
        │ • matches        │
        │ • performances   │
        │ • winners        │
        └────────┬─────────┘
                 │
                 │ (Auto-sync in seconds)
                 │
                 ▼
STEP 2: PUBLIC DISPLAY (Stats Display)
┌──────────────────────────────────────┐
│  https://dowdarts.github.io/         │
│  aadsstatsscrapper/stats-display.html│
│                                       │
│  Automatically shows:                 │
│  • Latest standings                   │
│  • Event results                      │
│  • Champions                          │
│  • Player stats                       │
│                                       │
│  Updates: Every 5 minutes or refresh  │
└──────────────────────────────────────┘
```

## 🔄 System Components

### 1. Admin Interface (index.html)
**Purpose**: Internal management for AADS organizers
**Access**: Private/organizers only
**Features**:
- ✏️ Event URL input
- 🔄 Scraping controls
- 📊 Detailed analytics
- 🎯 Head-to-head comparisons
- 👤 Player analysis tools
- 📈 Form tracking

**URL**: https://dowdarts.github.io/aadsstatsscrapper/

---

### 2. Supabase Database
**Purpose**: Central data storage
**Type**: PostgreSQL cloud database
**Tables**:
- `events` - Event information and dates
- `matches` - Individual match records
- `player_performances` - Match-by-match player stats
- `event_winners` - Champions and runner-ups

**Connection**: Both interfaces connect via Supabase API

---

### 3. Stats Display (stats-display.html)
**Purpose**: Public-facing statistics display
**Access**: Public/embeddable
**Features**:
- 👁️ Read-only viewing
- 📺 Broadcast-style design
- 🏆 Live standings
- 📅 Event results
- 🥇 Champions showcase

**URL**: https://dowdarts.github.io/aadsstatsscrapper/stats-display.html

---

## 🎯 Typical Workflow

### After Each Event:

1. **Organizer logs into Admin Interface**
   - URL: https://dowdarts.github.io/aadsstatsscrapper/

2. **Navigate to "Event Manager" tab**

3. **Input Event Details**
   ```
   Event URL: https://tv.dartconnect.com/event/mt_joe6163l_4
   Event Number: 4
   ```

4. **Click "Extract & Scrape Event"**
   - System extracts all match IDs
   - Scrapes each match for player stats
   - Saves to Supabase database
   - Takes 1-2 minutes for ~27 matches

5. **Success Message Appears**
   - Shows: Matches scraped, players updated
   - Includes link to public display

6. **Public Stats Update Automatically**
   - Stats Display reads from same database
   - Updates within seconds
   - No additional action needed
   - Fans/public see latest results immediately

---

## 🌐 Embedding on External Websites

The stats display can be embedded on any website:

```html
<iframe 
    src="https://dowdarts.github.io/aadsstatsscrapper/stats-display.html" 
    width="100%" 
    height="800px"
    frameborder="0">
</iframe>
```

**Websites where this can be embedded**:
- Official AADS website
- Tournament venue websites
- Social media pages
- League information portals
- Sponsor websites

---

## 🔐 Security & Access

### Admin Interface
- For AADS organizers only
- Can scrape and manage data
- Should not be publicly shared
- Protected by GitHub account access

### Stats Display
- Fully public
- Read-only (no data modification)
- Safe to embed anywhere
- No authentication required
- Uses public Supabase key (read-only)

---

## 📱 Data Sync

### Real-Time Connection:
```
Admin Interface → Supabase → Stats Display
     (Write)                    (Read)
```

- **Write Speed**: 1-2 minutes to scrape full event
- **Sync Speed**: Instant (same database)
- **Display Refresh**: 5 minutes auto, or manual refresh
- **Data Consistency**: 100% synchronized

---

## 🎨 Visual Differences

| Feature | Admin Interface | Stats Display |
|---------|----------------|---------------|
| Design | Dashboard/Tools | Broadcast/Professional |
| Colors | Gold/Dark | Gold/Black Sports Theme |
| Navigation | 8 Tabs | 5 Sections |
| Inputs | Yes (URL, filters) | None |
| Controls | Many buttons | None |
| Purpose | Manage data | Display data |

---

## 📊 Data Updates

### When does the public display update?

1. **Automatic**: Every 5 minutes
2. **Manual**: Page refresh
3. **On Embed**: When iframe reloads
4. **After Scrape**: Within seconds

### What data is shown?

- ✅ Overall player standings (ranked by average)
- ✅ Individual event results
- ✅ Event champions and runner-ups
- ✅ Top performers in each category
- ✅ Complete player statistics
- ✅ 180s, high finishes, averages
- ✅ Match counts and leg totals

---

## 🚀 Quick Start Guide

### For Organizers (After Event):

1. Open: https://dowdarts.github.io/aadsstatsscrapper/
2. Click: "Event Manager" tab
3. Enter: Event URL from DartConnect
4. Enter: Event number (1-7)
5. Click: "Extract & Scrape Event"
6. Wait: 1-2 minutes
7. Done: Stats are live!

### For Fans/Public:

1. Visit: https://dowdarts.github.io/aadsstatsscrapper/stats-display.html
2. View: Latest standings and results
3. Navigate: Click tabs to see different stats
4. Refresh: Page auto-updates every 5 minutes

---

## 🔧 Technical Details

### Technology Stack:
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Database**: Supabase (PostgreSQL)
- **Hosting**: GitHub Pages
- **Deployment**: GitHub Actions (Auto-deploy)
- **APIs**: Supabase REST API, DartConnect scraping

### Browser Support:
- ✅ Chrome/Edge (Latest)
- ✅ Firefox (Latest)
- ✅ Safari (Latest)
- ✅ Mobile browsers

### Performance:
- Page Load: < 2 seconds
- Data Fetch: < 1 second
- Scrape Time: 1-2 minutes per event
- Auto-refresh: Every 5 minutes

---

## 📞 Support

For technical issues or questions:
- Check GitHub repository: https://github.com/dowdarts/aadsstatsscrapper
- Review documentation files
- Contact AADS technical team

---

## 🎯 Summary

**One Interface to Manage** → **One Interface to Display**

Simple workflow:
1. Admin scrapes event → Data goes to database
2. Public display reads database → Everyone sees results
3. Both stay in perfect sync automatically
4. No manual data transfer needed

The system is designed to be:
- **Simple**: One-click scraping
- **Fast**: Results in seconds
- **Reliable**: Auto-syncing
- **Professional**: Broadcast-quality display
- **Public**: Easy to share and embed
