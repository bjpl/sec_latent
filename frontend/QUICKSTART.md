# Quick Start Guide

## Prerequisites
- Node.js 18+ installed
- Backend API running on http://localhost:8000

## Installation (3 steps)

```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Create environment file
cp .env.example .env

# 3. Start development server
npm run dev
```

Open http://localhost:3000 in your browser.

## What You'll See

### Dashboard (http://localhost:3000/dashboard)
- Real-time signal feed (right panel)
- Interactive heat map (left panel)
- Risk matrix chart (bottom)

### Mobile View
- 3 stat cards (Active, Alerts, Pending)
- Recent signals list
- Active alerts feed

### Navigation
- Click **Dashboard** - Signal monitoring
- Click **Predictions** - Prediction timeline
- Click **Alerts** - Alert management
- Click **Analysis** - Custom reports

## Testing Real-time Updates

The frontend will automatically connect to WebSocket at `ws://localhost:8000/ws` and listen for:

```json
// Signal update
{
  "type": "signal",
  "payload": {
    "id": "sig_123",
    "ticker": "AAPL",
    "signal_type": "buy",
    "confidence": 0.85,
    "strength": 0.72,
    "timeframe": "1h",
    "timestamp": "2025-10-19T03:00:00Z"
  }
}

// Prediction update
{
  "type": "prediction",
  "payload": {
    "id": "pred_456",
    "ticker": "GOOGL",
    "predicted_value": 150.5,
    "confidence": 0.78,
    "status": "pending"
  }
}

// Alert notification
{
  "type": "alert",
  "payload": {
    "id": "alert_789",
    "ticker": "TSLA",
    "severity": "high",
    "message": "Strong buy signal detected"
  }
}
```

## Common Issues

### Port Already in Use
```bash
# Kill process on port 3000
npx kill-port 3000
npm run dev
```

### WebSocket Connection Failed
- Ensure backend is running on port 8000
- Check `.env` has correct `NEXT_PUBLIC_WS_URL`
- Verify backend WebSocket endpoint is `/ws`

### Missing Dependencies
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

### TypeScript Errors
```bash
# Check for errors
npm run lint
npx tsc --noEmit
```

## Production Build

```bash
# Build optimized production bundle
npm run build

# Start production server
npm start
```

## Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard
# NEXT_PUBLIC_API_URL=https://your-api.com
# NEXT_PUBLIC_WS_URL=wss://your-api.com/ws
```

## File Structure Quick Reference

```
frontend/
├── app/                    # Pages (App Router)
│   ├── dashboard/         # Main monitoring
│   ├── predictions/       # Prediction tracking
│   ├── alerts/           # Alert management
│   └── analysis/         # Custom analysis
├── components/            # React components
│   ├── ui/              # Base components
│   └── *.tsx            # Feature components
├── stores/               # Zustand state
├── hooks/               # Custom hooks
├── lib/                 # Utilities
└── public/             # Static assets
```

## Development Tips

### Adding a New Page
```bash
mkdir -p app/newpage
touch app/newpage/page.tsx
```

### Creating a Component
```bash
touch components/MyComponent.tsx
```

### Adding a Store
```bash
touch stores/myStore.ts
```

### Testing WebSocket
```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8000/ws')
ws.onmessage = (e) => console.log('Received:', e.data)
ws.send(JSON.stringify({ type: 'signal', payload: {...} }))
```

## Next Steps

1. ✅ Start frontend dev server
2. ✅ Verify backend connection
3. ✅ Test WebSocket real-time updates
4. ✅ Check mobile responsive design
5. ✅ Test PWA installation
6. ✅ Run production build
7. ✅ Deploy to Vercel

## Support

- Check `README.md` for detailed documentation
- Review `IMPLEMENTATION_SUMMARY.md` for architecture
- See backend API docs for endpoint details

---

**Ready to go!** Run `npm run dev` and open http://localhost:3000
