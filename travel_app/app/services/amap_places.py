"""Nearby attraction lookup through the AMap Web Service POI API."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from app.private_config import AMAP_WEB_KEY


def search_nearby_attractions(longitude: float, latitude: float, city: str, limit: int = 10) -> list[dict]:
    if not AMAP_WEB_KEY or not AMAP_WEB_KEY.strip():
        raise RuntimeError("未配置高德 Web 服务 POI Key。")
    params = {
        "key": AMAP_WEB_KEY.strip(),
        "location": f"{longitude:.6f},{latitude:.6f}",
        "keywords": "景点",
        "city": city,
        "citylimit": "true",
        "radius": "10000",
        "sortrule": "distance",
        "offset": str(max(1, min(int(limit), 25))),
        "page": "1",
        "extensions": "all",
        "output": "JSON",
    }
    url = "https://restapi.amap.com/v3/place/around?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise RuntimeError("连接高德 POI 服务失败，请检查网络后重试。") from exc
    if data.get("status") != "1" or data.get("infocode") != "10000":
        info = str(data.get("info") or "查询失败")
        raise RuntimeError(f"高德 POI 查询失败：{info}")

    attractions = []
    for poi in data.get("pois") or []:
        photos = []
        for photo in poi.get("photos") or []:
            image_url = str(photo.get("url") or "").strip()
            if image_url.startswith("https://") or image_url.startswith("http://"):
                photos.append({"url": image_url, "title": str(photo.get("title") or "")})
        attractions.append({
            "name": str(poi.get("name") or ""),
            "address": str(poi.get("address") or ""),
            "distance": str(poi.get("distance") or ""),
            "location": str(poi.get("location") or ""),
            "photos": photos,
        })
    return attractions
