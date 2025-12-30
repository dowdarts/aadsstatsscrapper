# AADS Official Statistics System

Professional serverless statistics display and administration system for the Atlantic Amateur Darts Series.

## 📁 Project Structure

```
aads-stats-system/
├── public/              # Public-facing statistics display
│   └── index.html      # Main stats display page (GitHub Pages ready)
│
├── admin/              # Administrative interface (password protected)
│   └── index.html     # Stats input and management page
│
├── assets/
│   └── logos/         # All sponsor and brand logos
│
├── supabase/          # Database schema and migrations
│   └── migrations/    # SQL migration files
│
└── README.md          # This file
```

## 🚀 Quick Start

### Public Display
The public statistics display is hosted at:
- **GitHub Pages**: https://dowdarts.github.io/aadsstatsscrapper/
- **Local**: Open `public/index.html` in any modern web browser

### Admin Panel
The admin interface for entering tournament data:
- Open `admin/index.html` in a web browser
- Requires Supabase credentials (configured in the HTML file)

## 🔧 Technology Stack

- **Frontend**: Pure HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Supabase (PostgreSQL database)
- **Architecture**: Fully serverless
- **Hosting**: GitHub Pages (public display)

## 📊 Features

### Public Display (`public/index.html`)
- **STANDINGS**: Overall AADS player rankings with career statistics
- **EVENTS**: Browse tournament events with:
  - Series and event filtering
  - Round robin results
  - Knockout bracket visualization
  - Match-by-match details
- **CHAMPIONS**: Hall of fame with event winners
- **HEAD TO HEAD**: Player comparison tool
- **PLAYERS**: Individual player profiles
- Auto-refresh every 30 seconds
- Broadcast mode optimization for 1920x1080 displays

### Admin Panel (`admin/index.html`)
- Manual tournament data entry
- Match result recording
- Player statistics management
- Draft and publish workflow
- Direct Supabase integration

## 🗄️ Database Schema

The system uses Supabase with the following key tables:
- `series`: Tournament series information
- `events`: Individual tournament events
- `players`: Player profiles and information
- `matches`: Match records
- `match_stats`: Detailed match statistics
- `player_career_stats`: Aggregated career statistics (view)

See `supabase/migrations/` for complete schema.

## 🌐 Deployment

### GitHub Pages (Public Display)
1. Commit changes to the `main` branch
2. GitHub Pages automatically deploys from `/docs` folder
3. Access at: https://dowdarts.github.io/aadsstatsscrapper/

### Local Development
No build process required - just open the HTML files directly in a browser.

## 🔐 Configuration

### Supabase Connection
Both HTML files contain Supabase configuration:
```javascript
const SUPABASE_URL = 'https://nelkwitsvxufhyvfgdjq.supabase.co';
const SUPABASE_ANON_KEY = 'your-anon-key-here';
```

## 📋 Requirements

- Modern web browser (Chrome, Firefox, Safari, Edge)
- Active internet connection (for Supabase CDN)
- Supabase project with proper schema

## 🎨 Branding

All logos and brand assets are stored in `assets/logos/`:
- Official AADS Logo
- Partner and sponsor logos (CGC, CGC TV, CGC Darts, MD Studios)

## 📝 Version History

- **v1.0.8** (December 2025): Initial serverless release
  - Removed all scraping functionality
  - Migrated to Supabase backend
  - Removed Flask server dependency
  - Implemented manual stats input system

## 🤝 Contributing

This is a private system for AADS tournament management. For questions or support, contact the AADS administration.

## 📄 License

© 2025 Atlantic Amateur Darts Series. All rights reserved.
