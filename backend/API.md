# NutriScan AI Backend API Reference

This document provides a human-readable summary of the endpoints available in the NutriScan AI backend. For interactive documentation with request/response schemas and live testing, start the server and visit `/docs` (e.g., `http://localhost:8000/docs`).

---

## 🔍 Scan Endpoints

### `POST /scan/analyse`
- **Purpose**: Analyze a raw list of ingredients for allergens, additives, and calculate a personalized health score.
- **Auth Required**: No *(but if authenticated, the scan is personalized against allergies/conditions and automatically saved to history).*
- **Body**: `{"ingredients": ["water", "salt", "sugar"]}`

### `POST /scan/barcode`
- **Purpose**: Look up a product by barcode in Open Food Facts, extract its ingredients, and calculate a personalized health score.
- **Auth Required**: No *(but if authenticated, the scan is personalized against allergies/conditions and automatically saved to history).*
- **Body**: `{"barcode": "3017620422003"}`

---

## 👤 User Profile Endpoints

### `GET /users/me`
- **Purpose**: Retrieve the current user's profile (allergies, conditions, goals). Auto-creates an empty profile on first access.
- **Auth Required**: **Yes** (Firebase Bearer Token)

### `PATCH /users/me`
- **Purpose**: Partially update the current user's profile (e.g., adding an allergy or goal).
- **Auth Required**: **Yes** (Firebase Bearer Token)
- **Body**: `{"allergies": ["peanuts"], "goals": ["weight loss"]}` *(all fields optional)*

### `DELETE /users/me`
- **Purpose**: Permanently delete the user's profile and cascade delete all their scan history.
- **Auth Required**: **Yes** (Firebase Bearer Token)

---

## 📖 Scan History Endpoints

### `GET /history`
- **Purpose**: List the current user's scan history, paginated and ordered newest-first.
- **Auth Required**: **Yes** (Firebase Bearer Token)
- **Query Params**: `limit` (default: 20), `offset` (default: 0)

### `GET /history/{id}`
- **Purpose**: Retrieve a single past scan by its ID.
- **Auth Required**: **Yes** (Firebase Bearer Token)

### `DELETE /history/{id}`
- **Purpose**: Delete a specific scan from the user's history.
- **Auth Required**: **Yes** (Firebase Bearer Token)

### `DELETE /history`
- **Purpose**: Clear all scan history for the current user.
- **Auth Required**: **Yes** (Firebase Bearer Token)

---

## 🛠️ System Endpoints

### `GET /health`
- **Purpose**: Check the health status of the API, PostgreSQL Database, and Redis cache. Useful for orchestration readiness probes.
- **Auth Required**: No
