# Frontend - Anomaly Detection Dashboard

React 18 + TypeScript + Vite SPA for visualizing anomalies with interactive charts and filtering.

## Setup

### Prerequisites

- Node.js v24.13+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Running the Development Server

```bash
npm run dev
```

Server will start at `http://localhost:5173`

### Building for Production

```bash
npm run build
```

Output will be in `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/           # React components
│   │   └── Layout.tsx       # Main layout wrapper
│   ├── pages/               # Page components
│   │   └── Dashboard.tsx    # Dashboard page
│   ├── hooks/               # Custom React hooks
│   ├── services/            # API client services
│   ├── types/               # TypeScript type definitions
│   ├── utils/               # Utility functions
│   ├── __tests__/           # Test files
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
├── public/                  # Static assets
├── index.html               # HTML entry point
├── package.json             # Dependencies
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript configuration
├── vitest.config.ts         # Vitest configuration
├── tailwind.config.js       # Tailwind CSS configuration
└── README.md                # This file
```

## Development

### Code Quality

Format code with Prettier:
```bash
npm run format
```

Lint with ESLint:
```bash
npm run lint
npm run lint:fix
```

Type checking:
```bash
npm run type-check
```

### Testing

Run tests:
```bash
npm run test
```

Run tests with UI:
```bash
npm run test:ui
```

Generate coverage report:
```bash
npm run test:coverage
```

## Features

### Phase 3 - US1: Real-Time Anomaly Alerts (P1)
- Anomaly list with pagination
- Severity badge indicators
- Brief explanation tooltips

### Phase 4 - US2: Time Series Charts (P1)
- Interactive Recharts visualization
- Category selection
- Date range controls
- Anomaly highlighting on charts

### Phase 5 - US3: Explainable Insights (P1)
- Detailed anomaly panel
- Base explanation (statistical + ML scores)
- Cause classification
- Actionable advice

### Phase 6 - US4: Advanced Filtering (P2)
- Date range picker
- Category multi-select
- Severity filter
- Anomaly type filter
- Real-time list & chart updates

## API Integration

The frontend proxies API requests to `http://localhost:8000/api` in development.

Configure the API base URL in `vite.config.ts`:
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  }
}
```

For production, update the API URL in environment configuration.

## Environment Variables

Create `.env` file (if needed):
```
VITE_API_BASE_URL=http://localhost:8000/api
```

## Browser Support

Modern browsers with ES2020 support:
- Chrome/Chromium (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Performance

- Bundle size target: <500KB gzipped
- Initial load: <3 seconds on 4G
- Chart render: <2 seconds for 365+ data points
- Filter updates: <1 second (no page reload)

## License

MIT
