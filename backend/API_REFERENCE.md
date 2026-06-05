# API Reference

This project uses a single central API route definition for easy discovery.

## Main route files
- `erp_sales/urls.py` - project root URL configuration and API router definitions

## API base path
- `/api/` - includes all DRF viewset routes, inventory endpoints, and payment endpoints

## Registered API resources
- `GET/POST/PUT/PATCH/DELETE /api/sales/` - sales operations
- `POST /api/sales/create_sale/` - create a new sale with items, payment, and receipt
- `GET/POST/PUT/PATCH/DELETE /api/products/` - product operations
- `GET /api/products/{id}/suggestion/` - get ordering suggestion for one product
- `GET /api/products/all_suggestions/` - get low-stock and restock suggestions for all active products
- `PATCH /api/products/{id}/update_notes/` - update store keeper notes for a product
- `GET /api/products/low_stock/` - list active products with stock at or below reorder level
- `GET/POST/PUT/PATCH/DELETE /api/customers/` - customer operations
- `POST /api/auth/login/` - authenticate and get JWT tokens
- `POST /api/auth/verify_2fa/` - verify two-factor login
- `POST /api/auth/logout/` - log out and blacklist tokens
- `POST /api/auth/refresh/` - refresh JWT token
- `GET /api/auth/me/` - current authenticated user info
- `POST /api/auth/setup_2fa/` - generate 2FA QR and backup codes
- `POST /api/auth/enable_2fa/` - enable 2FA for the user
- `POST /api/auth/disable_2fa/` - disable 2FA for the user
- `GET /api/auth/twofa_status/` - 2FA status for the user
- `GET/POST/PUT/PATCH/DELETE /api/returns/` - return operations
- `POST /api/returns/process/` - process a customer or supplier return
- `POST /api/payments/mpesa/` - initiate M-Pesa STK Push payment
- `POST /api/payments/callback/` - receive M-Pesa callback responses
- `GET/POST/PUT/PATCH/DELETE /api/inventory/` - supplier operations
- `GET/POST/PUT/PATCH/DELETE /api/inventory/batches/` - inventory batch operations

## Implementation locations
- `sales/views.py` - `SaleViewSet`
- `products/views.py` - `ProductViewSet`
- `customers/views.py` - `CustomerViewSet`
- `users/views.py` - `AuthViewSet`
- `returns/views.py` - `ReturnViewSet`
- `payments/views.py` - `lipa_na_mpesa` and `MpesaCallbackView`
- `inventory/views.py` - `SupplierViewSet` and `BatchViewSet`
- `inventory/serializers.py` - `SupplierSerializer` and `BatchSerializer`

## Notes
- DRF viewsets automatically create standard REST routes.
- The root URL config only needs to include `erp_sales.api_urls` under `/api/`.
- Use `API_REFERENCE.md` as the quick lookup for the API surface.
