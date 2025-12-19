# 📍 WHERE TO SCRAPE EVENTS - Quick Guide

## 🎯 Finding the Event Manager (Scraping Interface)

### Step 1: Open the Admin Interface
Go to: **https://dowdarts.github.io/aadsstatsscrapper/**

### Step 2: Look at the Top Navigation Bar
You'll see these tabs:
```
┌─────────────────────────────────────────────────────────────┐
│ Leaderboard | 🔄 Event Manager (Scrape Here) | Event Details │
│ Achievements | All Stats | Head-to-Head | Player Analysis    │
│ Current Form                                                  │
└─────────────────────────────────────────────────────────────┘
```

### Step 3: Click "🔄 Event Manager (Scrape Here)"
This tab is **highlighted in gold** and **pulsing** to make it easy to find!

### Step 4: You'll See Two Input Fields
```
┌────────────────────────────────────────────┐
│ 📅 Event Manager                           │
├────────────────────────────────────────────┤
│                                            │
│ Event URL:                                 │
│ ┌────────────────────────────────────────┐ │
│ │ [Enter URL here]                       │ │
│ └────────────────────────────────────────┘ │
│                                            │
│ Event Number:                              │
│ ┌────────────────────────────────────────┐ │
│ │ [Enter number 1-7]                     │ │
│ └────────────────────────────────────────┘ │
│                                            │
│    [🔄 Extract & Scrape Event]            │
│                                            │
└────────────────────────────────────────────┘
```

## 📝 Complete Example

### Input This:
```
Event URL: https://tv.dartconnect.com/event/mt_joe6163l_1
Event Number: 1
```

### Then Click:
```
[🔄 Extract & Scrape Event]
```

### Wait 1-2 Minutes
You'll see:
```
⏳ Scraping event... This may take 1-2 minutes...
```

### Success!
```
✅ Event Scraped Successfully!
Total Matches: 27
Successfully Scraped: 27
Failed: 0
Players Updated: 12

📺 Stats are now live on the public display!
[View Public Stats →]
```

## 🚀 Alternative: Quick Start Banner

If you're on the **Leaderboard** tab (the default view), you'll see a **GOLD BANNER** that says:

```
┌────────────────────────────────────────────────────────┐
│  🎯 Need to Upload Event Stats?                       │
│                                                        │
│  Click the "Event Manager (Scrape Here)" tab above    │
│  to enter your event URL and scrape match statistics. │
│  Data will automatically appear here and on the        │
│  public stats display!                                │
│                                                        │
│       [🔄 Go to Event Manager →]                      │
└────────────────────────────────────────────────────────┘
```

Click that button and it takes you directly to the Event Manager!

## 🔍 Can't Find It?

### Make Sure You're on the Right Page:
- ✅ **Admin Interface**: https://dowdarts.github.io/aadsstatsscrapper/
- ❌ **Stats Display**: https://dowdarts.github.io/aadsstatsscrapper/stats-display.html (This is read-only, no inputs!)

### Visual Clues:
1. **Gold pulsing tab** in navigation called "🔄 Event Manager (Scrape Here)"
2. **Gold banner** on Leaderboard with "Go to Event Manager" button
3. **Blue info box** at top of Event Manager explaining the process

## 📊 After Scraping

Once you scrape an event, the data flows automatically:

```
Admin Interface
(You input URL here)
        ↓
   Supabase Database
   (Stores everything)
        ↓
  Stats Display Page
  (Public sees results)
```

No manual export needed - it's automatic! ✨

## 🎯 Summary

**WHERE**: Admin page → Click "🔄 Event Manager (Scrape Here)" tab
**WHAT**: Enter event URL and number
**HOW**: Click "Extract & Scrape Event" button
**WHEN**: Wait 1-2 minutes
**RESULT**: Stats appear everywhere automatically!

---

**Still can't find it?** 
Refresh the page: https://dowdarts.github.io/aadsstatsscrapper/
The gold pulsing "Event Manager" tab should be obvious!
