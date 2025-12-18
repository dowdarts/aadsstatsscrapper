# AADS - Atlantic Amateur Darts Series 🎯

[![Deploy to GitHub Pages](https://github.com/dowdarts/aadsstatsscrapper/actions/workflows/deploy.yml/badge.svg)](https://github.com/dowdarts/aadsstatsscrapper/actions/workflows/deploy.yml)

A cloud-based statistics tracking and leaderboard system for the Atlantic Amateur Darts Series, featuring real-time data scraping, analytics, and broadcasting capabilities.

## 🌐 **Live Application**

**Web Interface**: https://dowdarts.github.io/aadsstatsscrapper/

## ✨ **Features**

### 📊 **Live Leaderboard**
- Real-time player rankings with qualification tracking
- Weighted 3-dart averages across multiple events
- 180s, high finishes, and leg counts
- Auto-refresh every 30 seconds

### 🎯 **Data Collection**
- **Single Match Scraping**: Add individual DartConnect match URLs
- **Event Batch Scraping**: Automatically process entire tournament events
- **Weighted Statistics**: Proper average calculations across events
- **Data Validation**: Error handling and retry mechanisms

### 🏆 **Tournament Management**
- 7-event series structure (6 qualifying + 1 championship)
- Qualification point tracking
- Event winner management
- Series progression monitoring

### 📺 **Broadcasting Integration**
- OBS-ready broadcast mode with transparent background
- Clean, professional overlay design
- Real-time updates during live streams
- Mobile-responsive design

## 🛠 **Technology Stack**

### **Backend (Supabase)**
- **Database**: PostgreSQL with real-time subscriptions
- **API**: Supabase Edge Functions (Deno/TypeScript)
- **Authentication**: Supabase Auth (when needed)
- **Hosting**: Supabase infrastructure

### **Frontend (GitHub Pages)**
- **Framework**: Vanilla JavaScript + HTML5/CSS3
- **Hosting**: GitHub Pages (static)
- **CI/CD**: GitHub Actions
- **Responsive**: Mobile-first design

### **Integrations**
- **DartConnect**: Web scraping with Inertia.js parser
- **GitHub**: Version control and automated deployment
- **OBS**: Broadcast mode for live streaming

## 📁 **Project Structure**

```
aadsstatsscrapper/
├── docs/                    # GitHub Pages frontend
│   └── index.html          # Main application
├── .github/workflows/       # GitHub Actions
│   └── deploy.yml          # Auto-deployment workflow
├── database_manager.py      # Local development (legacy)
├── scraper.py              # Local development (legacy)
├── app.py                  # Local development (legacy)
└── supabase/               # Edge Functions
    ├── scrape-match/       # Single match scraping
    ├── scrape-event/       # Event batch scraping
    └── aads-api/           # Statistics API
```

## 🚀 **Getting Started**

### **For Users**
1. **Access the application**: https://dowdarts.github.io/aadsstatsscrapper/
2. **View leaderboard**: Live rankings and statistics
3. **Add match data**: Use the Management tab to input DartConnect URLs
4. **Monitor events**: Track series progression and qualification

### **For Administrators**
1. **Single Match**: Paste individual match URLs for immediate processing
2. **Event Batch**: Use event page URLs to scrape entire tournaments
3. **Data Management**: Export data, refresh statistics, toggle broadcast mode
4. **Broadcasting**: Enable broadcast mode for OBS integration

## 🔗 **API Endpoints**

### **Supabase Edge Functions**
```
POST /functions/v1/scrape-match     # Single match scraping
POST /functions/v1/scrape-event     # Event batch scraping
GET  /functions/v1/aads-api/stats   # Player leaderboard
GET  /functions/v1/aads-api/qualified # Qualified players
GET  /functions/v1/aads-api/events  # Events overview
GET  /functions/v1/aads-api/health  # Health check
```

### **Example Usage**
```javascript
// Scrape a single match
const response = await fetch('/functions/v1/scrape-match', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    url: 'https://recap.dartconnect.com/matches/688e209bf4fc02e124e72676' 
  })
});

// Get leaderboard
const stats = await fetch('/functions/v1/aads-api/stats');
const data = await stats.json();
```

## 🗃️ **Database Schema**

### **Core Tables**
- **`aads_players`**: Player information and aggregated statistics
- **`events`**: Tournament events and metadata
- **`matches`**: Individual match records
- **`player_performances`**: Per-match player statistics
- **`event_winners`**: Tournament winners and points

### **Views**
- **`aads_leaderboard`**: Ranked player standings
- **`aads_qualified_players`**: Top 8 + event winners
- **`aads_event_summary`**: Event progress and winners
- **`aads_player_performance_summary`**: Detailed player analytics

## 🧮 **Statistics Calculation**

### **Weighted 3-Dart Average**
```
Weighted Average = (Sum of all leg averages) / (Total legs played)
```

### **Qualification System**
- **Regular Events**: Points based on placement
- **Championship**: Final qualification spots
- **Auto-Qualify**: Event winners get automatic qualification

## 🎯 **DartConnect Integration**

### **Supported Formats**
- **Match Recap Pages**: Individual match statistics
- **Event Pages**: Batch tournament scraping
- **Inertia.js Parser**: Modern DartConnect format support

### **Data Extraction**
- Player names and averages
- Leg counts and high finishes
- PPR to 3-dart average conversion
- Match date and venue information

## 📱 **Mobile Support**

The application is fully responsive and optimized for:
- **Desktop**: Full management interface
- **Tablet**: Touch-friendly controls
- **Mobile**: Essential viewing and basic management
- **OBS**: Broadcast overlays

## 🔧 **Development**

### **Local Development** (Legacy)
```bash
# Clone repository
git clone https://github.com/dowdarts/aadsstatsscrapper.git
cd aadsstatsscrapper

# Install dependencies
pip install -r requirements.txt

# Run Flask development server
python app.py
```

### **Cloud Development**
1. **Supabase**: Deploy Edge Functions
2. **GitHub Pages**: Automatic deployment on push
3. **Database**: Supabase PostgreSQL
4. **Monitoring**: Supabase Dashboard

### **Contributing**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📈 **Performance**

### **Scalability**
- **Supabase**: Handles thousands of concurrent users
- **Edge Functions**: Global distribution
- **GitHub Pages**: CDN-delivered static assets
- **Real-time**: Instant data synchronization

### **Monitoring**
- **Health Checks**: Automatic endpoint monitoring
- **Error Tracking**: Comprehensive error logging
- **Performance**: Sub-second response times
- **Uptime**: 99.9% availability target

## 🔒 **Security**

### **Data Protection**
- **HTTPS**: All connections encrypted
- **CORS**: Proper cross-origin controls
- **Input Validation**: SQL injection prevention
- **Rate Limiting**: API abuse protection

### **Privacy**
- **Public Data**: Only tournament statistics stored
- **No PII**: No personal information collected
- **Transparent**: Open source codebase

## 📞 **Support**

### **Documentation**
- **User Guide**: In-app help and tooltips
- **API Documentation**: Endpoint specifications
- **Troubleshooting**: Common issues and solutions

### **Contact**
- **Repository**: https://github.com/dowdarts/aadsstatsscrapper
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions

## 🎉 **Acknowledgments**

- **DartConnect**: Match data platform
- **Supabase**: Backend infrastructure
- **GitHub**: Hosting and CI/CD
- **Atlantic Amateur Darts Series**: Tournament organization

## 📜 **License**

This project is open source and available under the [MIT License](LICENSE).

---

**Built with ❤️ for the Atlantic Amateur Darts Series community** 🎯