# NutriScan AI — Web App

A React + TypeScript + Vite web application for the NutriScan AI platform.  
Mirrors the visual design and feature set of the Flutter mobile app.

---

## Tech Stack

| Layer      | Technology |
|------------|-----------|
| Framework  | React 19 + TypeScript |
| Bundler    | Vite 8 |
| Styling    | Tailwind CSS v4 (`@tailwindcss/vite` plugin) |
| Routing    | React Router v7 |
| State      | Zustand |
| HTTP       | Axios |
| Auth       | Firebase JS SDK v11 (Google sign-in, email link) |

---

## Local Development

### 1. Install dependencies

```bash
cd web
npm install
```

### 2. Configure environment variables

```bash
cp .env.example .env.local
```

Edit `.env.local` and fill in the required values:

| Variable | Description |
|---|---|
| `VITE_API_URL` | FastAPI backend base URL (e.g. `http://localhost:8000`) |
| `VITE_FIREBASE_API_KEY` | Firebase Web SDK API key |
| `VITE_FIREBASE_AUTH_DOMAIN` | `your-project-id.firebaseapp.com` |
| `VITE_FIREBASE_PROJECT_ID` | Firebase project ID |
| `VITE_FIREBASE_STORAGE_BUCKET` | `your-project-id.appspot.com` |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | Firebase Sender ID |
| `VITE_FIREBASE_APP_ID` | Firebase Web App ID |

See [`mobile/lib/firebase_options.dart.example`](../mobile/lib/firebase_options.dart.example) for the matching Flutter config.

### 3. Start the dev server

```bash
npm run dev
```

The app starts at **http://localhost:5173**.

> **Note**: You'll also need the FastAPI backend running. See [`backend/README.md`](../backend/) or use `docker-compose up` from the repo root.

---

## Production Build

```bash
npm run build
```

Output is written to `web/dist/`. The build is a standard static SPA — serve `dist/` from any static host (Vercel, Netlify, Firebase Hosting, NGINX, etc.).

> **Important**: `VITE_API_URL` and all `VITE_FIREBASE_*` values are **baked into the bundle at build time** by Vite's `import.meta.env` replacement. There are **no runtime-configurable env vars**. Set the correct production values in your CI/CD environment before running `npm run build`.

To verify no localhost URLs leaked into the bundle:

```bash
npm run build
grep -r "localhost" dist/
# Should return nothing (or only in source maps if you generate them)
```

---

## Routes

| Path | Page | Auth |
|---|---|---|
| `/login` | Login (Google, email link, guest) | Public |
| `/` | Home dashboard | Protected |
| `/history` | Scan history (paginated) | Protected |
| `/profile` | Health profile editor | Protected |
| `/scan` | Manual scan (barcode / ingredients) | Protected |
| `/results/:id` | Scan results detail | Protected |

Protected routes allow both authenticated users **and** guests (guest mode is local-only — no backend sync).

---

## Feature Notes

- **Guest mode**: Scans work but are not saved to the backend. History/profile are empty. Persisted in `localStorage`.
- **Barcode scan**: Calls `POST /scan/barcode` which uses the Open Food Facts database. Works with EAN-8, EAN-13, UPC-A.
- **Ingredient scan**: Calls `POST /scan/analyse` with a text list. **No OCR on web** — users paste the text manually.
- **Auto-save**: Authenticated scans are automatically saved to history by the backend (no separate POST needed).
- **Stats**: Total/safe/flagged counts are computed client-side from the history response (no `/stats` endpoint).
