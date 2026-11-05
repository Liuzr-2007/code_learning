"""VariFlight MCP read-only flight lookup."""

from __future__ import annotations

import json
import os
import shutil
import ssl
import subprocess
import tempfile
import urllib.request
import urllib.error

from app.private_config import VARIFLIGHT_MCP_KEY, VARIFLIGHT_MCP_URL


CITY_AIRPORTS = {
    "北京": "PEK,PKX", "上海": "PVG,SHA", "广州": "CAN", "深圳": "SZX",
    "长沙": "CSX", "成都": "CTU,TFU", "杭州": "HGH", "武汉": "WUH",
    "西安": "XIY", "重庆": "CKG", "南京": "NKG", "厦门": "XMN",
    "昆明": "KMG", "哈尔滨": "HRB", "沈阳": "SHE", "青岛": "TAO",
    "天津": "TSN", "郑州": "CGO", "长春": "CGQ", "福州": "FOC",
    "南昌": "KHN", "贵阳": "KWE", "南宁": "NNG", "海口": "HAK",
    "三亚": "SYX", "乌鲁木齐": "URC", "拉萨": "LXA", "宁波": "NGB",
    "温州": "WNZ", "济南": "TNA", "合肥": "HFE", "太原": "TYN",
    "石家庄": "SJW", "兰州": "LHW", "银川": "INC", "呼和浩特": "HET",
    "珠海": "ZUH", "无锡": "WUX", "常州": "CZX", "烟台": "YNT",
    "桂林": "KWL", "丽江": "LJG", "大连": "DLC", "香港": "HKG",
    "澳门": "MFM", "台北": "TPE",
}


def city_code(name: str) -> str | None:
    city = (name or "").strip().rsplit(".", 1)[-1]
    return CITY_AIRPORTS.get(city)


def _post_with_windows_curl(payload: dict, session_id: str | None, method: str) -> tuple[dict, str | None]:
    """Windows fallback for networks where Python TLS fails revocation-related handshakes.

    curl still validates the certificate chain and hostname; only its revocation
    lookup is skipped because some networks block the required CRL/OCSP hosts.
    """
    curl = shutil.which("curl.exe")
    if not curl:
        raise RuntimeError("Python TLS 握手失败，且系统中未找到 curl.exe，无法重试飞常准请求。")

    headers = [
        "Content-Type: application/json",
        "Accept: application/json, text/event-stream",
        "Authorization: Bearer " + VARIFLIGHT_MCP_KEY.strip(),
    ]
    if session_id:
        headers.extend([
            "Mcp-Session-Id: " + session_id,
            "Mcp-Protocol-Version: 2025-03-26",
        ])

    body_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", delete=False) as body_file:
            body_file.write(json.dumps(payload, ensure_ascii=True))
            body_path = body_file.name

        def quote_config(value: str) -> str:
            return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "").replace("\n", "") + '"'

        config = [
            "url = " + quote_config(VARIFLIGHT_MCP_URL),
            'request = "POST"',
            "data-binary = " + quote_config("@" + os.path.abspath(body_path)),
            'include', 'silent', 'show-error', 'ssl-no-revoke',
            'max-time = 35',
        ]
        config.extend("header = " + quote_config(header) for header in headers)
        completed = subprocess.run(
            [curl, "--config", "-"], input="\n".join(config),
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=40,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"飞常准 curl 重试超时（{method}）。") from exc
    finally:
        if body_path and os.path.exists(body_path):
            os.unlink(body_path)

    if completed.returncode:
        detail = completed.stderr.strip() or f"curl 退出码 {completed.returncode}"
        raise RuntimeError(f"飞常准 curl 重试失败（{method}）：{detail[:800]}")

    raw_response = completed.stdout
    split_at = raw_response.find("\r\n\r\n")
    separator_size = 4
    if split_at < 0:
        split_at = raw_response.find("\n\n")
        separator_size = 2
    if split_at < 0:
        raise RuntimeError(f"飞常准 curl 重试返回无法识别的 HTTP 响应（{method}）。")
    response_headers = raw_response[:split_at].splitlines()
    raw = raw_response[split_at + separator_size:]
    status_line = response_headers[0] if response_headers else ""
    try:
        status_code = int(status_line.split()[1])
    except (IndexError, ValueError):
        raise RuntimeError(f"飞常准 curl 重试返回无法识别的状态码（{method}）。")
    for line in response_headers[1:]:
        name, separator, value = line.partition(":")
        if separator and name.strip().lower() == "mcp-session-id":
            session_id = value.strip()
    if status_code >= 400:
        raise RuntimeError(f"飞常准 {method} 返回 HTTP {status_code}: {raw[:1200]}")
    try:
        return _decode_mcp_response(raw, method), session_id
    except RuntimeError:
        raise


def _decode_mcp_response(raw: str, method: str) -> dict:
    if not raw.strip():
        if method.startswith("notifications/"):
            return {}
        raise RuntimeError(f"飞常准 {method} 返回空响应。")
    raw = raw.lstrip("\ufeff \r\n\t")
    if raw.lstrip().startswith(("event:", "data:", "id:")):
        data_lines = [line[5:].strip() for line in raw.splitlines()
                      if line.startswith("data:") and line[5:].strip()]
        for data in reversed(data_lines):
            if data != "[DONE]":
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    continue
        raise RuntimeError(f"飞常准 {method} 返回无法识别的 SSE 响应：{raw[:1000]}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"飞常准 {method} 返回非 JSON 内容：{raw[:1000]}") from exc


def _post_mcp(payload: dict, session_id: str | None = None) -> tuple[dict, str | None]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": "Bearer " + VARIFLIGHT_MCP_KEY.strip(),
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
        headers["Mcp-Protocol-Version"] = "2025-03-26"
    request = urllib.request.Request(
        VARIFLIGHT_MCP_URL, data=json.dumps(payload).encode("utf-8"),
        headers=headers, method="POST",
    )
    method = payload.get("method", "unknown")
    try:
        # Keep certificate validation enabled and allow Python/OpenSSL to
        # negotiate the best protocol version supported by the gateway.
        tls_context = ssl.create_default_context()
        tls_context.minimum_version = ssl.TLSVersion.TLSv1_2
        with urllib.request.urlopen(request, timeout=35, context=tls_context) as response:
            raw = response.read().decode("utf-8")
            session_id = response.headers.get("Mcp-Session-Id", session_id)
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"飞常准 {method} 返回 HTTP {exc.code}: {details[:1200]}") from exc
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLError) and "UNEXPECTED_EOF" in str(exc.reason):
            return _post_with_windows_curl(payload, session_id, method)
        raise
    return _decode_mcp_response(raw, method), session_id


def search_flights(origin: str, destination: str, date: str) -> str:
    dep, arr = city_code(origin), city_code(destination)
    if not dep or not arr:
        raise ValueError("暂不支持该城市的航班查询，请检查城市名称或补充机场代码映射。")
    if not VARIFLIGHT_MCP_KEY:
        raise ValueError("尚未配置 VariFlight MCP Key。")
    initialized, session_id = _post_mcp({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                   "clientInfo": {"name": "travel_app", "version": "0.1.0"}},
    })
    protocol_version = initialized.get("result", {}).get("protocolVersion")
    if protocol_version and protocol_version != "2025-03-26":
        # The server may negotiate an older supported protocol version.
        pass
    _post_mcp({"jsonrpc": "2.0", "method": "notifications/initialized"}, session_id)
    payload = {
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "getFlightList", "arguments": {
            "date": date, "dep": dep, "arr": arr,
        }},
    }
    result, session_id = _post_mcp(payload, session_id)
    tool_result = result.get("result", {})
    if tool_result.get("isError"):
        message = "\n".join(c.get("text", "") for c in tool_result.get("content", []))
        raise RuntimeError(message or "飞常准航班工具调用失败。")

    contents = list(tool_result.get("content", []))
    expanded = []
    for item in contents:
        if item.get("type") == "resource_link":
            uri = item.get("uri") or item.get("resource", {}).get("uri")
            if uri:
                resource_result, session_id = _post_mcp({
                    "jsonrpc": "2.0", "id": 3, "method": "resources/read",
                    "params": {"uri": uri},
                }, session_id)
                expanded.extend(resource_result.get("result", {}).get("contents", []))
        elif item.get("type") == "resource":
            expanded.append(item.get("resource", item))
        else:
            expanded.append(item)
    structured = tool_result.get("structuredContent")
    return json.dumps({"content": expanded, "structuredContent": structured},
                      ensure_ascii=False)
