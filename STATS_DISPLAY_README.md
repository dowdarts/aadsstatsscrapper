# AADS Professional Stats Display

## 🎯 Official Statistics Display for Atlantic Amateur Darts Series

This is the professional, read-only statistics display page designed for public viewing and website embedding.

## 📍 Live URLs

- **Stats Display**: https://dowdarts.github.io/aadsstatsscrapper/stats-display.html
- **Embed Example**: https://dowdarts.github.io/aadsstatsscrapper/embed-example.html
- **Admin Interface**: https://dowdarts.github.io/aadsstatsscrapper/

## ✨ Features

### Professional Design
- 📺 Broadcast-quality sports statistics presentation
- 🎨 Dark theme with gold accents matching AADS branding
- 📱 Fully responsive for all devices
- ⚡ Smooth animations and transitions
- 🔄 Auto-refreshes every 5 minutes

### Statistics Sections
1. **STANDINGS** - Overall player rankings with key stats
2. **EVENTS** - Complete event cards with champions and results
3. **CHAMPIONS** - Showcase of all event winners
4. **STATISTICS** - Top performers in each category
5. **PLAYERS** - Complete player directory

### Read-Only Features
- ✅ No user inputs or controls
- ✅ No data modification capabilities
- ✅ Pure display and presentation
- ✅ Optimized for public viewing
- ✅ Safe for embedding on external websites

## 🌐 How to Embed

### Basic Embed
```html
<iframe 
    src="https://dowdarts.github.io/aadsstatsscrapper/stats-display.html" 
    width="100%" 
    height="800px" 
    frameborder="0"
    style="border-radius: 8px;">
</iframe>
```

### Responsive Embed (Recommended)
```html
<div style="position: relative; padding-bottom: 75%; height: 0; overflow: hidden;">
    <iframe 
        src="https://dowdarts.github.io/aadsstatsscrapper/stats-display.html" 
        style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;">
    </iframe>
</div>
```

### WordPress Shortcode
```
[iframe src="https://dowdarts.github.io/aadsstatsscrapper/stats-display.html" width="100%" height="800px"]
```

## 🎨 Customization

The page automatically detects when it's embedded (via iframe) and adjusts:
- Header positioning becomes relative (non-sticky)
- Navigation bar becomes relative
- Background becomes transparent
- Optimized for seamless embedding

## 📊 Data Source

All statistics are pulled in real-time from Supabase:
- **Leaderboards** - Aggregated player statistics
- **Events** - Complete event information
- **Championships** - Winner records
- **Player Profiles** - Individual performance data

Data refreshes automatically every 5 minutes to show latest results.

## 🔐 Security

- Read-only access via Supabase anonymous key
- No write operations possible
- No sensitive data exposure
- Safe for public embedding

## 🖥️ Browser Compatibility

Tested and working on:
- ✅ Chrome/Edge (Latest)
- ✅ Firefox (Latest)
- ✅ Safari (Latest)
- ✅ Mobile browsers (iOS/Android)

## 📋 Comparison with Admin Interface

| Feature | Admin Interface | Stats Display |
|---------|----------------|---------------|
| **Purpose** | Internal management | Public viewing |
| **Access** | Full control | Read-only |
| **Features** | Scraping, editing, filtering | Display only |
| **Design** | Functional dashboard | Broadcast-style |
| **Embedding** | Not recommended | Optimized for it |
| **Audience** | AADS organizers | Public/fans |

## 🚀 Deployment

Files are automatically deployed via GitHub Actions:
- Pushes to `main` branch trigger deployment
- Deploys from `/docs` folder
- Available on GitHub Pages within 1-2 minutes

## 📱 Mobile Optimization

The stats display is fully responsive:
- Stacked layouts on mobile
- Touch-friendly navigation
- Optimized font sizes
- Horizontal scrolling for wide tables

## 🎯 Use Cases

1. **Website Embedding** - Add to official AADS website
2. **Social Media Sharing** - Direct link to stats
3. **Event Displays** - Show on screens during tournaments
4. **League Pages** - Embed in league information pages
5. **Streaming Overlays** - Use as statistics reference

## 📞 Support

For issues or customization requests, contact AADS administrators.

## 📄 License

© Atlantic Amateur Darts Series. All rights reserved.
