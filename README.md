# Vendura Backend

> **Development status:** Vendura is under active development. The current version implements the core API and transactional workflows described below, while deployment infrastructure and broader coverage continue to evolve.

Vendura is an e-commerce backend API built with Django and Django REST Framework. It provides account registration, product catalog access, customer addresses, shopping carts, coupon-aware checkout, inventory control, and customer-scoped order management.

The project emphasizes clear domain boundaries, transactional consistency, ownership enforcement, and efficient ORM usage.

## Highlights

- Email-based registration and cookie-based JWT authentication with token rotation and blacklisting.
- Public product catalog with filtering and cursor pagination.
- Permission-controlled product, category, and user management.
- Customer-scoped addresses, carts, cart items, and orders.
- Direct-product and cart checkout with atomic stock deduction and restoration.
- Coupon activation, expiration, minimum-value, discount-cap, and usage-limit validation.
- Immutable order snapshots and domain-specific checkout errors.
- OpenAPI schema with Swagger UI and ReDoc.
- Automated service and API tests for critical order workflows.

## Technology stack

| Area | Technology |
| --- | --- |
| Runtime | Python; tooling targets Python 3.13 |
| Framework | Django 6.0.6 |
| REST API | Django REST Framework 3.17.1 |
| Authentication | Simple JWT 5.5.1 |
| Schema | drf-spectacular 0.30.0 |
| Filtering | django-filter 25.2 |
| Database | SQLite |
| Cache backend | Redis through django-redis |
| Validation and media | django-phonenumber-field, phonenumbers, Pillow |
| Development tooling | Django test framework, factory_boy, Faker, Ruff |

Pinned versions are available in [`backend/requirements.txt`](backend/requirements.txt).

## Architecture

Vendura is divided into domain-focused Django applications. Views and serializers handle HTTP input and output, services coordinate multi-step business workflows, and repositories centralize selected persistence operations.

| Module | Responsibility |
| --- | --- |
| `apps.users` | Custom user model, registration, cookie JWT authentication, and user management |
| `apps.customers` | Customer profiles, addresses, ownership, and delivery snapshots |
| `apps.products` | Categories, catalog visibility, filtering, and stock persistence |
| `apps.carts` | Customer carts, cart items, and selected-item queries |
| `apps.coupons` | Coupon rules and conditional usage updates |
| `apps.orders` | Checkout, totals, order items, listing, and cancellation |
| `apps.core` | Shared permissions and permission-group seeding |
| `config` | Settings, root routing, pagination, and exception handling |

The most consistency-sensitive workflows—checkout and cancellation—run inside database transactions.

## API overview

The local API base URL is `http://127.0.0.1:8000/api/`.

| Domain | Method | Path | Access |
| --- | --- | --- | --- |
| Authentication | `POST` | `/api/users/auth/register/`, `/api/users/auth/login/` | Public |
| Authentication | `POST` | `/api/users/auth/refresh/`, `/api/users/auth/logout/` | Refresh cookie |
| Users | `GET` | `/api/users/` | Model permission |
| Users | `PATCH` | `/api/users/{id}/` | Model permission |
| Products | `GET` | `/api/products/`, `/api/products/{id}/` | Public |
| Products | CRUD | `/api/staff/products/` and `/api/staff/products/{id}/` | Model permissions |
| Categories | CRUD | `/api/staff/category/` and `/api/staff/category/{id}/` | Admin user |
| Addresses | `GET`, `POST` | `/api/customers/addresses/` | Authenticated customer |
| Addresses | `GET`, `PUT`, `PATCH`, `DELETE` | `/api/customers/addresses/{id}/` | Owner |
| Cart | `GET` | `/api/cart/` | Authenticated customer |
| Cart items | `POST` | `/api/cart/item/` | Authenticated customer |
| Cart items | `GET`, `PUT`, `PATCH`, `DELETE` | `/api/cart/item/{id}` | Owner |
| Orders | `POST` | `/api/orders/finalize-cart/`, `/api/orders/finalize-direct/` | Authenticated customer |
| Orders | `GET` | `/api/orders/` | Authenticated customer |
| Orders | `POST` | `/api/orders/{id}/cancel/` | Owner |

### Catalog filters

`GET /api/products/` accepts `category`, `min_price`, `max_price`, and `cursor` query parameters.

Only products with `public=True` are available through public catalog, cart creation, and checkout operations.

### Checkout input

Cart checkout accepts `address_id` and an optional `coupon_code`. Direct checkout also accepts an `item` object containing `product` and a positive `quantity`.

Expected domain errors use a consistent shape:

```json
{
  "error": "Human-readable message",
  "code": "ExceptionClassName"
}
```

## Authentication and authorization

Vendura uses a custom user model with unique email authentication and no username field. Registration validates the password and creates the associated customer profile atomically.

Successful login responses place tokens in cookies instead of returning them in the response body:

| Cookie | Lifetime | Purpose |
| --- | --- | --- |
| `access_token` | 15 minutes | Authenticates API requests |
| `refresh_token` | 7 days | Rotates and renews authentication tokens |

Both cookies are HTTP-only. They are marked secure when `DEBUG=False`. Refresh-token rotation and blacklisting are enabled.

Django REST Framework requires authentication by default. Public endpoints explicitly relax that rule, staff resources use either Django model permissions or admin-user checks, and customer resources are restricted through ownership-filtered querysets and repositories.

## Data model and business rules

### Customers and addresses

- Each user has one customer profile and each customer can have multiple addresses.
- Address access is restricted to the authenticated owner.
- Checkout verifies ownership of `address_id` and copies street, number, neighborhood, city, state, and ZIP code into the order.
- Historical orders therefore do not depend on a mutable address record.

### Products and carts

- Products belong to protected categories and enforce positive prices and non-negative stock.
- Each customer has at most one cart.
- A product can appear only once per cart; adding it again increases its quantity.
- Cart quantities must be positive.
- Cart checkout processes and removes only items marked `selected`.

### Coupons and orders

- Coupons support percentage discounts, optional maximum discounts, optional minimum order values, activation, expiration, and usage limits.
- Coupon usage is incremented through a conditional database update.
- Order items preserve the unit price used at checkout.
- Checkout validates product visibility and inventory before completing the order.
- Orders may be cancelled while `pending` or `paid`; cancellation restores product stock.
- Customers cannot list or cancel another customer's orders.

## Transaction and query behavior

- Checkout and cancellation use `transaction.atomic()`.
- Checkout requests product rows with `select_for_update()` before stock changes.
- Order cancellation locks the owned order before changing status and restoring inventory.
- Stock and coupon counters use database-side `F()` expressions.
- Product queries use `select_related("category")`.
- Cart and order responses combine `prefetch_related()` with targeted `select_related()` queries.
- Products use cursor pagination with a page size of 20.
- Orders use page-number pagination with a page size of 10.
- Frequently queried order-status and cart-selection fields are indexed.

SQLite is used for local development. A database with full row-level locking support is required to provide the intended `SELECT ... FOR UPDATE` behavior under concurrent production workloads.

## Security considerations

Passwords use Django's hashing and validation system. Authentication cookies are HTTP-only and become secure outside debug mode, while refresh tokens are rotated and blacklisted.

API access is authenticated by default, customer-owned resources are filtered by ownership, and `SECRET_KEY` is loaded from the environment. Django security, CSRF, authentication, and clickjacking middleware are enabled.

Deployment-specific host, TLS, cross-origin, cookie/CSRF, secret-management, and static/media policies are not configured in this repository.

## Project structure

```text
backend/
|-- manage.py
|-- requirements.txt
|-- pyproject.toml
|-- config/                 # Settings, routing, pagination, exceptions
`-- apps/
    |-- users/
    |-- customers/
    |-- products/
    |-- carts/
    |-- coupons/
    |-- orders/
    |   |-- services.py
    |   |-- repositories.py
    |   `-- tests/
    `-- core/
        `-- management/commands/seed_groups.py

docker-compose.yml  # Redis development service
```

## Environment variables

Django loads variables from `backend/.env` with `python-dotenv`:

```env
SECRET_KEY=<your-secret-key>
DEBUG=True
```

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `SECRET_KEY` | Yes | None | Django signing key |
| `DEBUG` | No | `False` | Enabled only when set exactly to `True` |

The `.env` file is ignored by Git. SQLite and Redis locations are currently defined directly in `config/settings.py`.

## Local installation

From the repository root:

```bash
cd backend
python -m venv venv
```

Activate it with the command for your shell:

```text
PowerShell:  .\venv\Scripts\Activate.ps1
POSIX:       source venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create `backend/.env` using the variables above.

## Database migrations

Apply migrations from `backend/`:

```bash
python manage.py migrate
```

Optionally seed the initial permission groups and create a development superuser:

```bash
python manage.py seed_groups
python manage.py createsuperuser
```

## Running the development server

```bash
python manage.py runserver
```

The default address is `http://127.0.0.1:8000/`.

## Running tests

```bash
python manage.py test
```

The current suite contains 14 service and API tests covering direct and cart checkout, coupon application, authentication, selected cart items, ownership, cancellation, stock restoration, and expected checkout failures. Django creates and destroys an isolated SQLite test database for the run.

## Docker and Redis

The root `docker-compose.yml` provides Redis 7 Alpine on port `6379`, matching the configured cache location `redis://127.0.0.1:6379/1`.

Start or stop Redis from the repository root:

```bash
docker compose up -d redis
docker compose down
```

The Django application currently runs outside Docker; Compose is used only for the configured Redis service.

## API documentation

With the server running:

| Resource | URL |
| --- | --- |
| OpenAPI schema | `http://127.0.0.1:8000/api/schema/` |
| Swagger UI | `http://127.0.0.1:8000/api/docs/` |
| ReDoc | `http://127.0.0.1:8000/api/redoc/` |

## Current development scope

The implemented portfolio scope centers on catalog, cart, checkout, inventory, and customer order workflows. SQLite is intended for local development, and production database and deployment configuration are not included. Automated tests currently focus on the critical order and checkout workflows; other domains can receive broader coverage as development continues.
