# OAuth2 Authentication

MusicBrainzPy supports OAuth2 for user-scoped operations (tags, ratings, collections, ISRCs, barcodes).

See the [MusicBrainz OAuth2 docs](https://musicbrainz.org/doc/Development/OAuth2) for the full spec.

## Prerequisites

1. [Register your application](https://musicbrainz.org/account/applications) on MusicBrainz
2. Note your **Client ID** and **Client Secret**
3. Set a **Redirect URI** (use `urn:ietf:wg:oauth:2.0:oob` for CLI/desktop apps)

## Available Scopes

| Scope | Description |
|---|---|
| `profile` | View public profile (username, age, country, homepage) |
| `email` | View email address |
| `tag` | View and modify private tags |
| `rating` | View and modify private ratings |
| `collection` | View and modify private collections |
| `submit_isrc` | Submit ISRCs |
| `submit_barcode` | Submit barcodes |

## Web Application Flow

```python
import asyncio
from musicbrainzpy import (
    MusicBrainzClient,
    OAuthHandler,
    OAuthScope,
    build_authorization_url,
    generate_pkce,
)

CLIENT_ID = "your-client-id"
CLIENT_SECRET = "your-client-secret"
REDIRECT_URI = "http://localhost:8080/callback"

# Step 1: Generate PKCE pair (recommended)
code_verifier, code_challenge = generate_pkce()

# Step 2: Build authorization URL and redirect user
auth_url = build_authorization_url(
    client_id=CLIENT_ID,
    redirect_uri=REDIRECT_URI,
    scopes=[OAuthScope.TAG, OAuthScope.RATING, OAuthScope.COLLECTION],
    code_challenge=code_challenge,
    access_type="offline",  # get a refresh token
    state="my-csrf-token",
)
print(f"Open in browser: {auth_url}")

# Step 3: After user authorizes, exchange the code
async def main():
    oauth = OAuthHandler(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

    # Exchange authorization code for tokens
    authorization_code = input("Enter the authorization code: ")
    token = await oauth.exchange_code(authorization_code, code_verifier=code_verifier)
    print(f"Access token: {token.access_token}")
    print(f"Refresh token: {token.refresh_token}")
    print(f"Expires in: {token.expires_in}s")

    # Step 4: Use with the client
    async with MusicBrainzClient("myapp", "1.0", "me@example.com", oauth=oauth) as client:
        # Submit tags (requires 'tag' scope)
        await client.submit_tags({
            "artist": {"65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab": ["metal", "thrash"]}
        })

asyncio.run(main())
```

## Desktop / CLI Application Flow (OOB)

```python
import asyncio
from musicbrainzpy import (
    MusicBrainzClient,
    OAuthHandler,
    OAuthScope,
    build_authorization_url,
    generate_pkce,
)
from musicbrainzpy.auth import OOB_REDIRECT_URI

CLIENT_ID = "your-client-id"
CLIENT_SECRET = "your-client-secret"

code_verifier, code_challenge = generate_pkce()

# User copies the code manually with OOB
auth_url = build_authorization_url(
    client_id=CLIENT_ID,
    redirect_uri=OOB_REDIRECT_URI,
    scopes=[OAuthScope.TAG, OAuthScope.RATING],
    code_challenge=code_challenge,
    access_type="offline",
)
print(f"Open this URL in your browser:\n{auth_url}\n")

async def main():
    oauth = OAuthHandler(CLIENT_ID, CLIENT_SECRET, OOB_REDIRECT_URI)
    code = input("Paste the authorization code here: ")
    token = await oauth.exchange_code(code, code_verifier=code_verifier)

    # Save tokens for later (you'd persist these to disk)
    print(f"Save these for next time:")
    print(f"  access_token: {token.access_token}")
    print(f"  refresh_token: {token.refresh_token}")

    async with MusicBrainzClient("myapp", "1.0", "me@example.com", oauth=oauth) as client:
        await client.submit_ratings({
            "recording": {"ba5d0553-032f-4127-aed7-4d2e0d18f3f9": 80}
        })

asyncio.run(main())
```

## Restoring a Saved Token

```python
from musicbrainzpy import OAuthHandler, MusicBrainzClient

oauth = OAuthHandler("your-client-id", "your-client-secret", "http://localhost:8080/callback")

# Load from your storage (database, file, keyring, etc.)
oauth.set_token(
    access_token="saved-access-token",
    refresh_token="saved-refresh-token",
    expires_in=3600,
)

# The client will auto-refresh if the token is expired
async with MusicBrainzClient("myapp", "1.0", "me@example.com", oauth=oauth) as client:
    await client.submit_tags({"artist": {"some-mbid": ["jazz"]}})
```

## Token Refresh

Tokens auto-refresh when expired (if a refresh token is available).
You can also refresh manually:

```python
new_token = await oauth.refresh()
# Save the new token to your storage
```

## Token Revocation

When the user logs out or uninstalls your app:

```python
await oauth.revoke()  # revokes refresh token (and its grant)
```
