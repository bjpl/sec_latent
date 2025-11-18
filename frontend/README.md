# SEC-LATENT Frontend

Next.js 14 application for real-time signal monitoring and prediction tracking.

## Features

- **Real-time Signal Monitoring**: WebSocket-based live signal updates
- **Interactive Dashboards**: Heat maps, risk matrices, and timeline visualizations
- **Mobile-First Design**: Responsive layout optimized for mobile devices
- **PWA Support**: Installable with offline capabilities and push notifications
- **State Management**: Zustand for efficient state handling
- **Modern UI**: shadcn/ui components with Tailwind CSS

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix UI)
- **State Management**: Zustand
- **Charts**: Recharts
- **Real-time**: WebSocket client

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Update .env with your backend URL
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## Project Structure

```
frontend/
├── app/                    # Next.js app router pages
│   ├── dashboard/         # Signal monitoring dashboard
│   ├── predictions/       # Prediction tracking
│   ├── alerts/           # Alert management
│   └── analysis/         # Custom analysis
├── components/            # React components
│   ├── ui/              # Base UI components (shadcn/ui)
│   ├── Navigation.tsx    # Main navigation
│   ├── SignalHeatMap.tsx # Heat map visualization
│   ├── RealtimeSignals.tsx # Live signal feed
│   ├── PredictionTimeline.tsx # Timeline view
│   ├── RiskMatrix.tsx    # Risk matrix chart
│   └── MobileDashboard.tsx # Mobile-optimized view
├── stores/               # Zustand state stores
│   ├── signalStore.ts   # Signal state
│   ├── predictionStore.ts # Prediction state
│   └── alertStore.ts    # Alert state
├── hooks/               # Custom React hooks
│   ├── useWebSocket.ts  # WebSocket connection
│   └── use-toast.ts     # Toast notifications
├── lib/                 # Utility functions
│   ├── api.ts          # API client
│   └── utils.ts        # Helper functions
└── public/             # Static assets
    ├── manifest.json   # PWA manifest
    └── sw.js          # Service worker
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Pages

### Dashboard (`/dashboard`)
- Real-time signal monitoring
- Interactive heat map
- Risk matrix visualization
- Mobile-optimized cards

### Predictions (`/predictions`)
- Prediction timeline
- Status tracking (pending/validated/failed)
- Accuracy metrics
- Confidence scores

### Alerts (`/alerts`)
- Active alert management
- Severity-based filtering
- Resolution tracking
- Push notification support

### Analysis (`/analysis`)
- Custom ticker selection
- Historical signal analysis
- Report generation
- Data export

## API Integration

The frontend connects to the backend API using:

- REST API for data fetching (`/api/v1/*`)
- WebSocket for real-time updates (`/ws`)

### API Client Usage

```typescript
import { apiClient } from '@/lib/api'

// Fetch signals
const signals = await apiClient.getSignals(100)

// Create prediction
const prediction = await apiClient.createPrediction(data)

// Resolve alert
await apiClient.resolveAlert(alertId)
```

## State Management

Zustand stores provide reactive state:

```typescript
import { useSignalStore } from '@/stores/signalStore'

const { signals, addSignal } = useSignalStore()
```

## WebSocket Connection

Real-time updates via WebSocket:

```typescript
import { useWebSocket } from '@/hooks/useWebSocket'

// Automatically connects and updates stores
useWebSocket()
```

## PWA Features

### Service Worker
- Offline caching
- Background sync
- Push notifications

### Installation
Users can install the app on:
- Mobile devices (Android/iOS)
- Desktop (Chrome, Edge, Safari)

## Deployment

### Vercel (Recommended)

```bash
# Deploy to Vercel
vercel

# Or connect GitHub repo for automatic deployments
```

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Variables

Production environment variables:
```env
NEXT_PUBLIC_API_URL=https://api.yourapp.com
NEXT_PUBLIC_WS_URL=wss://api.yourapp.com/ws
NEXT_PUBLIC_VAPID_PUBLIC_KEY=your-production-vapid-key
```

## Mobile Optimization

- Responsive design with Tailwind breakpoints
- Touch-optimized interactions
- Mobile-specific dashboard layout
- Reduced data transfer for mobile

## Performance

- Code splitting with Next.js App Router
- Image optimization
- Service worker caching
- Lazy loading of components

## Contributing

1. Follow TypeScript strict mode
2. Use shadcn/ui components when possible
3. Maintain mobile-first approach
4. Add unit tests for utilities
5. Update this README for new features

## License

MIT
