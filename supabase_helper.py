"""Small server-side client for the Supabase REST API."""

import requests

import config


def is_configured():
    has_url = bool(config.SUPABASE_URL)
    has_key = bool(config.SUPABASE_SERVICE_ROLE_KEY)
    if has_url != has_key:
        raise RuntimeError(
            "Configure both SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY, or remove both."
        )
    return has_url


def request(method, table, *, params=None, payload=None):
    if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "Set both SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to use Supabase storage."
        )

    url = f"{config.SUPABASE_URL.rstrip('/')}/rest/v1/{table}"
    headers = {
        "apikey": config.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {config.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.request(
        method,
        url,
        headers=headers,
        params=params,
        json=payload,
        timeout=15,
    )
    response.raise_for_status()
    if response.content:
        return response.json()
    return []
