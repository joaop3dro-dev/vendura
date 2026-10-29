# Vendura API

Vendura is a RESTful e-commerce backend built with Django and Django REST Framework. It provides the core workflows required by a product catalog: customer registration, authentication, addresses, carts, checkout, inventory reservation, orders, coupons, and PIX payments through Mercado Pago.

The repository is intentionally backend-only. It exposes a documented HTTP API that can be consumed by any web, mobile, or other client.

> **Project status:** Core e-commerce workflows are implemented. Production deployment, webhook exposure, scheduled order expiry, and environment-specific security configuration remain the responsibility of the deployer.

## Features

- Email-based customer registration and cookie-based JWT authentication.
- Refresh-token rotation and token blacklisting.
- Public product catalog with category and price filtering.
- Permission-controlled product, category, and user administration endpoints.
- Customer-owned addresses, carts, cart items, and orders.
- Cart and direct-item checkout flows.
- Atomic stock reservation during checkout, with restoration on cancellation or expiry.
- Coupon validation for activation, expiry, minimum order amount, maximum discount, and usage limits.
- PIX payment creation and status retrieval through Mercado Pago.
- Mercado Pago webhook processing that confirms accredited payments against provider data.
- OpenAPI schema, Swagger UI, and ReDoc.

## Stack

| Area | Technology |
| --- | --- |
| Language | Python 3.12 |
| Framework | Django 6.0 |
| API | Django REST Framework |
| Authentication | Simple JWT |
| Database | SQLite by default; PostgreSQL 16 in Docker Compose |
| Payment provider | Mercado Pago Orders API (PIX) |
| API documentation | drf-spectacular |
| Code quality | Ruff |

## Architecture

The application is organised by domain. Views and serializers define the HTTP boundary; services coordinate business transactions; repositories centralise persistence operations used by those workflows.

| App | Responsibility |
| --- | --- |
| `apps.users` | Custom user model, registration, authentication, and staff user management |
| `apps.customers` | Customer profiles and customer-owned delivery addresses |
| `apps.products` | Product catalogue, categories, filtering, visibility, and stock |
| `apps.carts` | One cart per customer and cart-item management |
| `apps.coupons` | Coupon data and checkout validation rules |
| `apps.orders` | Checkout, stock reservation, order history, cancellation, and expiry |
| `apps.payment` | PIX payment lifecycle and Mercado Pago integration |
| `apps.core` | Shared permissions and management commands |
| `config` | Django settings, routing, pagination, and exception handling |

Checkout, cancellation, payment confirmation, and order expiry use database transactions. Product rows are locked during checkout where the selected database supports row-level locking.

## Requirements

- Python 3.12 (matches the Docker image)
- pip
- PostgreSQL 16 only when using Docker Compose or a PostgreSQL `DATABASE_URL`
- A Mercado Pago access token only when exercising PIX payments

## Local setup

Create and activate a virtual environment from the repository root:

```bash
cd backend
python -m venv .venv

# PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create `backend/.env`:

```env
SECRET_KEY=replace-with-a-long-random-secret
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Optional locally. Omit this variable to use backend/db.sqlite3.
# DATABASE_URL=postgresql://vendura:vendura@localhost:5432/vendura

# Required to create PIX payments.
# MERCADO_PAGO_ACCESS_TOKEN=APP_USR-your-access-token
```

Apply migrations and optionally create a staff account:

```bash
python manage.py migrate
python manage.py seed_groups
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/api/`.

## Environment variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `SECRET_KEY` | Yes | — | Django secret key. Never commit it. |
| `DEBUG` | No | `False` | Set to `True` only for local development. |
| `ALLOWED_HOSTS` | No | `localhost` | Comma-separated Django host allowlist. |
| `DATABASE_URL` | No | SQLite database at `backend/db.sqlite3` | Database connection URL. |
| `MERCADO_PAGO_ACCESS_TOKEN` | For PIX | — | Mercado Pago access token. |
| `MERCADO_PAGO_API_BASE_URL` | No | `https://api.mercadopago.com` | Mercado Pago API base URL. |
| `MERCADO_PAGO_TIMEOUT_SECONDS` | No | `10` | Timeout for provider HTTP calls. |
| `MERCADO_PAGO_PIX_EXPIRATION_MINUTES` | No | `30` | PIX expiry communicated to Mercado Pago. |
| `MERCADO_PAGO_PIX_EXPIRATION_SAFETY_MARGIN_SECONDS` | No | `60` | Minimum safety margin before a PIX can be created. |

## Docker Compose

`docker-compose.yml` starts PostgreSQL and the Django backend. The backend container runs migrations before starting Gunicorn.

Create a root `.env` for the PostgreSQL container:

```env
POSTGRES_DB=vendura
POSTGRES_USER=vendura
POSTGRES_PASSWORD=choose-a-strong-password
```

Then create `backend/.env` with the Django variables and a database URL that uses the Compose service name:

```env
SECRET_KEY=replace-with-a-long-random-secret
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://vendura:choose-a-strong-password@db:5432/vendura
MERCADO_PAGO_ACCESS_TOKEN=APP_USR-your-access-token
```

Build and run the services:

```bash
docker compose up --build
```

The API will listen on port `8000`, and PostgreSQL on port `5432`.

## API overview

All API paths below are relative to `/api/`.

| Area | Method | Endpoint | Access |
| --- | --- | --- | --- |
| Authentication | `POST` | `users/auth/register/` | Public |
| Authentication | `POST` | `users/auth/login/` | Public |
| Authentication | `POST` | `users/auth/refresh/` | Refresh-token cookie |
| Authentication | `POST` | `users/auth/logout/` | Refresh-token cookie |
| Public catalogue | `GET` | `products/`, `products/{id}/` | Public |
| Staff products | CRUD | `staff/products/`, `staff/products/{id}/` | Django model permissions |
| Staff categories | CRUD | `staff/category/`, `staff/category/{id}/` | Admin user |
| Addresses | `GET`, `POST` | `customers/addresses/` | Authenticated customer |
| Addresses | `GET`, `PUT`, `PATCH`, `DELETE` | `customers/addresses/{id}/` | Address owner |
| Cart | `GET` | `cart/` | Authenticated customer |
| Cart item | `POST` | `cart/item/` | Authenticated customer |
| Cart item | `GET`, `PUT`, `PATCH`, `DELETE` | `cart/item/{id}` | Item owner |
| Orders | `POST` | `orders/finalize-cart/` | Authenticated customer |
| Orders | `POST` | `orders/finalize-direct/` | Authenticated customer |
| Orders | `GET` | `orders/` | Authenticated customer |
| Order cancellation | `POST` | `orders/{id}/cancel/` | Order owner |
| PIX payment | `POST`, `GET` | `payment/orders/{order_id}/pix/` | Order owner |
| Payment webhook | `POST` | `payment/webhooks/mercado-pago/` | Mercado Pago notification endpoint |

The public product list accepts `category`, `min_price`, `max_price`, and `cursor` query parameters. Only products marked `public=True` are returned.

For the complete request and response schemas, use the interactive documentation described below.

## Authentication

Vendura authenticates users with the custom email-based user model. A successful login sets the following HTTP-only cookies rather than returning JWTs in the response body:

| Cookie | Lifetime | Purpose |
| --- | --- | --- |
| `access_token` | 15 minutes | Authenticates API requests |
| `refresh_token` | 7 days | Renews the access token; rotation and blacklisting are enabled |

Resources require authentication by default. The public catalogue and registration/login endpoints explicitly allow anonymous access. Customer resources use owner-scoped querysets, while staff endpoints use Django permissions or admin checks.

## Checkout and payment flow

1. A customer registers, logs in, and creates an address.
2. The customer adds public products to a cart or submits a direct-item checkout request.
3. Checkout validates the address, selected products, stock, and optional coupon. It creates a pending order, snapshots the delivery address and unit prices, deducts stock, and clears the selected cart items.
4. The client requests `POST payment/orders/{order_id}/pix/` to obtain the PIX copy-and-paste value and payment ticket URL.
5. Mercado Pago calls `POST payment/webhooks/mercado-pago/`. The API retrieves the provider order, verifies the local amount, external reference, and payment method, then marks the payment and order as approved when the PIX is accredited.

Pending orders expire after 35 minutes. To release their reserved stock, schedule the following command in your runtime environment:

```bash
python manage.py expire_orders
```

The command is not scheduled by the application itself.

## Error responses

Domain errors are returned in a predictable format:

```json
{
  "error": "Insufficient stock for Example product",
  "code": "InsufficientStockError"
}
```

Relevant business errors map to appropriate HTTP status codes, such as `400` for invalid checkout input, `404` for inaccessible resources, `409` for stock or payment-state conflicts, `502` for invalid provider responses, and `503` when Mercado Pago is unavailable.

## API documentation

With the server running, open:

| Resource | URL |
| --- | --- |
| OpenAPI schema | `http://127.0.0.1:8000/api/schema/` |
| Swagger UI | `http://127.0.0.1:8000/api/docs/` |
| ReDoc | `http://127.0.0.1:8000/api/redoc/` |

## Tests and code quality

Run the Django test suite from `backend/`:

```bash
python manage.py test
```

The current suite contains service and API tests for direct and cart checkout, selected cart items, coupon use, stock restoration, ownership checks, and expected checkout failures.

Check and format code with Ruff:

```bash
ruff check .
ruff format --check .
```

## Production notes

- Use PostgreSQL or another database with reliable row-level locking; SQLite is intended for local development only.
- Set `DEBUG=False`, provide a secure `SECRET_KEY`, and configure `ALLOWED_HOSTS` for the deployed hostnames.
- Serve the API over HTTPS. Authentication cookies are marked `Secure` when debug mode is off.
- Expose the Mercado Pago webhook at a public HTTPS URL and configure it in Mercado Pago.
- The webhook handler verifies payment details with Mercado Pago, but does not yet validate webhook signatures; add signature validation before exposing it publicly.
- Run `expire_orders` on a schedule so unpaid orders release reserved inventory.
- Configure backup, observability, media storage, CSRF/cross-origin policy, and secret management for the target environment.

## License

Vendura is distributed under the [MIT License](LICENSE).
