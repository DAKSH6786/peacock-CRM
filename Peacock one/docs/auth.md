# Authentication

## Supported now

- Email/password register + login
- JWT access tokens with `sub`, `org`, `ws`, `roles`
- `/auth/me` for session bootstrap

## Prepared

- Google OAuth (`GOOGLE_OAUTH_*`, `/auth/oauth/google/start`)
- Microsoft OAuth (`MICROSOFT_OAUTH_*`, `/auth/oauth/microsoft/start`)
- `/auth/oauth/providers` reports enabled providers

## Security notes

- Passwords hashed with bcrypt (passlib)
- Secrets only from environment
- Audit events on register/login
- Org membership required for authenticated routes
