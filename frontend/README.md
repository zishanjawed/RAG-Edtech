# RAG Edtech Frontend

Modern React + TypeScript frontend for the RAG Edtech platform.

## Quick Start

### Prerequisites
- Node.js 18+
- Backend services running at http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Configure environment
echo "VITE_API_BASE_URL=http://localhost:8000" > .env

# Start development server
npm run dev
```

Access at: http://localhost:3000

## Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript compiler
```

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.3 | UI library |
| TypeScript | 5.9 | Type safety |
| Vite | 7.1 | Build tool |
| TailwindCSS | 4.1 | Styling |
| Zustand | 5.0 | State management |
| React Query | 5.90 | Server state |
| Framer Motion | 12.23 | Animations |
| React Router | 7.9 | Routing |
| Axios | Latest | HTTP client |

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API services and client
│   ├── features/         # Feature modules (auth, chat, documents, etc.)
│   ├── components/       # Reusable UI components
│   ├── layouts/          # Page layouts
│   ├── pages/            # Route pages
│   ├── hooks/            # Custom hooks
│   ├── styles/           # Global styles
│   ├── lib/              # Library configurations
│   ├── App.tsx           # Main router
│   └── main.tsx          # Entry point
├── public/               # Static assets
└── package.json          # Dependencies
```

## Key Features

- **Authentication:** Login, register, JWT token management
- **Document Upload:** Drag-and-drop with validation
- **Chat Interface:** Streaming AI responses with markdown
- **Role-Based Routing:** Different dashboards for students/teachers
- **Analytics Dashboard:** Student engagement metrics
- **Teacher Dashboard:** Class overview and student monitoring

## Environment Configuration

Create `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_ENV=development
VITE_ENABLE_ANALYTICS=false
```

## Building for Production

```bash
# Build
npm run build

# Output will be in dist/
# Deploy dist/ folder to your hosting service
```

## Development Workflow

1. **Make Changes:** Edit files in `src/`
2. **Hot Reload:** Changes appear instantly
3. **Type Check:** Run `npm run type-check`
4. **Lint:** Run `npm run lint`
5. **Build:** Run `npm run build`

## Common Tasks

### Add New Page

1. Create page component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add navigation link if needed

### Add New API Service

1. Create service file in `src/api/`
2. Define TypeScript types in `src/api/types.ts`
3. Use Axios client from `src/api/client.ts`

### Add New Component

1. Create component in appropriate directory
2. Define TypeScript props interface
3. Export from directory index
4. Import and use in pages

## Authentication Flow

1. User logs in via `LoginPage`
2. JWT tokens stored in localStorage
3. Axios interceptor adds token to requests
4. On 401, token auto-refreshes
5. Auth state managed by Zustand store

## Troubleshooting

**Can't connect to backend:**
- Check backend is running: `curl http://localhost:8000/health`
- Verify VITE_API_BASE_URL in .env
- Check CORS configuration on backend

**Build fails:**
- Run `npm install` to ensure all dependencies installed
- Check for TypeScript errors: `npm run type-check`
- Clear cache: `rm -rf node_modules dist && npm install`

**Hot reload not working:**
- Restart dev server
- Check file permissions
- Update Vite: `npm update vite`

## Testing

Manual E2E testing:
1. Register new user
2. Login and verify dashboard redirect
3. Upload document
4. Ask questions in chat
5. Check analytics page

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers

## Documentation

For complete documentation including architecture, API integration, and troubleshooting, see [PROJECT_MASTER.md](../PROJECT_MASTER.md).

## License

MIT
