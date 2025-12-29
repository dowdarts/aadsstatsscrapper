# AADS v2.0 - Deployment Guide

## Prerequisites
- Python 3.8+
- Supabase account with project URL and keys
- Git installed

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Set Environment Variables

Create a `.env` file in the project root:

```
SUPABASE_URL=https://nelkwitsvxufhyvfgdjq.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5lbGt3aXRzdnh1Zmh5dmZnZGpxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzE5NDc5MzIsImV4cCI6MjA0NzUyMzkzMn0.eiRjrJiOHY8R5qBKg3l8PSmq-z5mLNYgz_ZCMuKEo32TM
SUPABASE_SERVICE_KEY=your_service_role_key_here
```

**IMPORTANT**: Get your service_role key from Supabase dashboard > Project Settings > API > service_role key

## Step 3: Run Database Migration (One-Time)

This transfers existing data from `aads_master_db.json` to Supabase:

```bash
python migrate_json_to_supabase.py
```

Expected output:
- ✓ Players migrated
- ✓ Events migrated  
- ✓ Matches and stats migrated
- ✓ Version initialized

## Step 4: Start Flask Server

```bash
python app.py
```

Server runs on: http://localhost:5000

## Step 5: Test Admin Interface

1. Navigate to http://localhost:5000/stats-input
2. Fill in tournament details:
   - Series name
   - Event number (1-7)
   - Date
3. Add 10 players with photos
4. Click "Generate Round Robin" to create 5-player groups
5. Enter match results and stats
6. Click "Save as Draft" to save without publishing
7. Click "Save & Publish" to make live

## Step 6: Test Display App

1. Navigate to http://localhost:5000/docs/official_stats_display.html
2. Verify tabs work: Stats, Roster, Player Profile
3. Test navigation filters (Series, Event, View)
4. Click on a player card to view profile
5. Wait 10 seconds - verify auto-refresh polling works

## Step 7: Test API Endpoints

```bash
# Get current version
curl http://localhost:5000/api/stats-version

# Get all-time standings
curl http://localhost:5000/api/all-time-standings

# Get all players
curl http://localhost:5000/api/players

# Get events list (published only)
curl http://localhost:5000/api/events-list?status=published

# Get specific player
curl http://localhost:5000/api/player/1

# Get series list
curl http://localhost:5000/api/series
```

## Step 8: Deploy to GitHub Pages

The display app is already in the `docs/` folder for GitHub Pages:

1. Push changes to GitHub:
```bash
git add -A
git commit -m "Deploy v2.0 - Manual Input System"
git push origin main
```

2. Enable GitHub Pages:
   - Go to repository Settings > Pages
   - Source: Deploy from a branch
   - Branch: main
   - Folder: /docs
   - Click Save

3. Wait 1-2 minutes for deployment

4. Access display at: https://dowdarts.github.io/aadsstatsscrapper/official_stats_display.html

## Step 9: Running in Production

For production deployment, consider:

### Option A: PythonAnywhere (Free tier available)
1. Upload code to PythonAnywhere
2. Set environment variables in `.env` or web app config
3. Configure WSGI file to point to `app.py`
4. Set Flask app as web app

### Option B: Heroku
```bash
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Add to requirements.txt
echo "gunicorn==21.2.0" >> requirements.txt

# Deploy
heroku create aads-stats
heroku config:set SUPABASE_URL=your_url
heroku config:set SUPABASE_ANON_KEY=your_anon_key
heroku config:set SUPABASE_SERVICE_KEY=your_service_key
git push heroku main
```

### Option C: Railway
1. Connect GitHub repo to Railway
2. Add environment variables in dashboard
3. Deploy automatically on push

## Troubleshooting

### Migration fails with "permission denied"
- Make sure `SUPABASE_SERVICE_KEY` is set correctly
- Verify RLS policies are created from `supabase/migrations/create_tournament_schema.sql`

### Flask server won't start
- Check if port 5000 is already in use
- Verify all dependencies are installed: `pip install -r requirements.txt`

### Display app shows "Loading..." forever
- Check Flask server is running
- Verify API endpoints return data (use curl or browser)
- Check browser console for errors (F12)

### Auto-refresh not working
- Make sure `/api/stats-version` endpoint returns valid JSON
- Check browser console for network errors
- Verify version increments when you publish tournaments

### Photos not showing
- Ensure photos are uploaded as base64 in admin interface
- Check image data starts with `data:image/...`
- Verify player records have `photo_base64` field populated

## Backup and Restore

### Backup Database
Visit: http://localhost:5000/admin/backup-data

Downloads timestamped JSON file: `aads_backup_YYYYMMDD_HHMMSS.json`

### Restore from Backup
1. Go to admin interface: http://localhost:5000/stats-input
2. Click "Restore Backup" button
3. Select backup JSON file
4. Confirm restore

## Updating the Display App

The display app fetches data from Flask API routes, so to update stats:
1. Enter new tournament data in admin interface
2. Click "Save & Publish"
3. Display app auto-refreshes within 10 seconds
4. Users see updated stats without page reload

## Next Steps

- Set up regular backups (weekly recommended)
- Add user authentication for admin interface
- Configure CORS if hosting Flask and display on different domains
- Set up monitoring for API endpoints
- Consider adding email notifications for new tournament publications

## Support

For issues, check:
1. Flask server logs
2. Browser console (F12)
3. Supabase dashboard > Table Editor
4. GitHub repository issues

---

**Version**: 2.0.0 - Manual Input System  
**Last Updated**: 2024  
**Repository**: https://github.com/dowdarts/aadsstatsscrapper
