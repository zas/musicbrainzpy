"""Submit a rating using OAuth2 authentication.

On first run, opens the authorization URL and asks for the code.
Paste the access token if you already have one, or follow the OAuth flow.
"""

from __future__ import annotations

import asyncio
import webbrowser

from musicbrainzpy import MusicBrainzClient, OAuthHandler, build_authorization_url

CLIENT_ID = "your-client-id"
CLIENT_SECRET = "your-client-secret"
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"


async def main() -> None:
    oauth = OAuthHandler(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

    token = input("Access token (leave empty to authorize): ").strip()
    if token:
        oauth.set_token(token)
    else:
        url = build_authorization_url(CLIENT_ID, REDIRECT_URI, ["rating"], access_type="offline")
        print(f"\nOpen this URL to authorize:\n{url}\n")
        webbrowser.open(url)
        code = input("Paste the authorization code: ").strip()
        token_obj = await oauth.exchange_code(code)
        print(f"Got access token: {token_obj.access_token[:8]}...")

    async with MusicBrainzClient(
        "musicbrainzpy-examples",
        "0.1.0",
        "you@example.com",
        oauth=oauth,
    ) as mb:
        # Rate "In the Rectory of the Bizarre Reverend" 5 stars
        await mb.submit_ratings(
            "musicbrainzpy-examples-0.1.0",
            {"release-group": {"2775d734-1ede-4e2b-a20e-e754bb98eb09": 100}},
        )
        print("Rating submitted!")


if __name__ == "__main__":
    asyncio.run(main())
