from fastapi import Request
from typing import Optional
import requests

from app.core.config import settings


def _extract_ip(request: Request) -> Optional[str]:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _parse_user_agent(user_agent: Optional[str]) -> dict:
    if not user_agent:
        return {"device": None, "browser": None, "operating_system": None, "device_type": None}
    device_type = "desktop"
    lowered = user_agent.lower()
    if "mobile" in lowered:
        device_type = "mobile"
    elif "tablet" in lowered:
        device_type = "tablet"

    return {
        "device": user_agent[:255],
        "browser": user_agent[:255],
        "operating_system": user_agent[:255],
        "device_type": device_type,
    }


def _geoip_lookup(ip_address: Optional[str]) -> dict:
    if not ip_address or not settings.geoip_lookup_enabled:
        return {"country": None, "city": None, "region": None, "isp": None}
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=3)
        payload = response.json()
        return {
            "country": payload.get("country"),
            "city": payload.get("city"),
            "region": payload.get("regionName"),
            "isp": payload.get("isp"),
        }
    except Exception:
        return {"country": None, "city": None, "region": None, "isp": None}


def collect_tracking_data(request: Request, source_application: Optional[str] = None) -> dict:
    ip_address = _extract_ip(request)
    ua_data = _parse_user_agent(request.headers.get("user-agent"))
    geo_data = _geoip_lookup(ip_address)
    return {
        "public_ip": ip_address,
        "country": geo_data["country"],
        "city": geo_data["city"],
        "region": geo_data["region"],
        "isp": geo_data["isp"],
        "device": ua_data["device"],
        "browser": ua_data["browser"],
        "operating_system": ua_data["operating_system"],
        "device_type": ua_data["device_type"],
        "source_application": source_application,
    }
