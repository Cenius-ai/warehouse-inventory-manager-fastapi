# Usage

## Accessing the application

Start the server (see [INSTALL.md](INSTALL.md)) and open `http://127.0.0.1:8000` in a browser.

## Login

The seed data creates two users:

- **Admin**: `admin@example.com` / password = value of `ADMIN_PASSWORD` env variable
- **Demo**: `demo@example.com` / password = value of `DEMO_PASSWORD` env variable

Use the login form at `/auth/login` (or the root `/` when not authenticated).

## Dashboard (Overview)

After login you are redirected to `/` which shows the overview dashboard:
- Total number of products and categories
- Lists of low‑stock items (current stock ≤ reorder point) and out‑of‑stock items
- Breakdown of products by category

## Managing Categories

- **List**: `/categories` – view all categories
- **Create**: `/categories/create` – add a new category (name, description)
- **Edit**: `/categories/{category_id}/edit` – modify a category
- **Delete**: POST to `/categories/{category_id}/delete` (button on the list or edit page)

## Managing Products

- **List**: `/products` – search by name/SKU, filter by category
- **Create**: `/products/create` – enter SKU, name, description, category, stock levels, unit
- **View detail**: `/products/{product_id}` – shows product info and current stock
- **Edit**: `/products/{product_id}/edit`
- **Delete**: POST to `/products/{product_id}/delete`

## Stock Movements

- **List**: `/movements` – view all stock‑in/stock‑out records
- **Create**: `/movements/create` – record a stock‑in or stock‑out for a product, adjusting the current stock automatically

## Health Check Endpoint

`GET /health` returns a JSON status:
```json
{"status": "ok"}
```

## Programmatic Authentication (curl)

To use the application from a script:

```bash
# Log in and save the session cookie
curl -X POST http://localhost:8000/auth/login \
  -d "email=admin@example.com&password=$ADMIN_PASSWORD" \
  -c cookies.txt

# Access a protected page using the cookie
curl -b cookies.txt http://localhost:8000/categories/
```

All form‑based endpoints require a CSRF token (`csrf_token`). Full API access using sessions is possible, but for external automation you would need to extract the token from a prior response.