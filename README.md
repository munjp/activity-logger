# Daily Activity Logger - Vercel Ready

A complete daily activity tracking system with location-based check-in and Slack integration.

## 🚀 Quick Deploy to Vercel

### 1. Upload to GitHub
- Upload all files to your GitHub repository
- Make sure `vercel.json` is in the root directory

### 2. Connect to Vercel
- Go to vercel.com
- Import your GitHub repository
- Vercel will auto-detect the Python project

### 3. Set Environment Variables
In Vercel project settings, add:
```
SECRET_KEY=your-secret-key-here
SLACK_WEBHOOK_URL=your-slack-webhook-url
```

### 4. Deploy
- Vercel will automatically deploy
- Your app will be available at: `https://your-app.vercel.app`

## ✅ Features

### Check-in System
- 22 dealership locations
- GPS location verification
- Test Site accessible from anywhere
- Automatic timestamp capture (Eastern Time)

### Activity Logging
- 8-hour daily activity tracking
- Productivity scoring system
- Star ratings (1-5 stars per hour)

### Slack Integration
- Automatic submission to Slack
- Rich message formatting
- Location and time information included

### Workflow
1. Check in → Select dealership → Verify location
2. Log activities → Fill 8-hour form
3. Submit → Auto-send to Slack → Auto-checkout → Redirect to check-in

## 🔧 Scoring Matrix

| Activity | Points |
|----------|--------|
| Cars Sold | 10 |
| Cars Delivered | 8 |
| In-Person Appointments | 4 |
| Phone Appointments | 3 |
| Appointments Generated | 2 |
| Quote Calls | 1 |
| Advertisements Posted | 1 |

## 📱 URLs

- **Main/Check-in**: `/` or `/checkin.html`
- **Activity Logging**: `/index.html`
- **API Health**: `/health`

## 🛠️ Technical Details

- **Framework**: Flask + Python
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Deployment**: Vercel Serverless
- **Session Management**: Flask sessions
- **Timezone**: Eastern Time (Toronto)

## 🔒 Security

- Environment variables for secrets
- No hardcoded credentials
- CORS enabled for API access
- Session-based authentication

Ready for production deployment! 🎯

