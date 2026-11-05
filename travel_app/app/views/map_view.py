"""高德地图视图。

用 QWebEngineView 加载内嵌的高德地图 JS API 页面，同时显示「出发地」与「目的地」
两个位置：分别地理编码后打标记，并用虚线连线，自动适配视野以包含两点。
"""

from __future__ import annotations

import json

from PyQt5.QtCore import QUrl, Qt, QObject, pyqtSignal, pyqtSlot, QRunnable, QThreadPool
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWidgets import QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView

from app import i18n
from app.private_config import AMAP_KEY, AMAP_SECURITY_CODE
from app.services.variflight import search_flights
from app.services.amap_places import search_nearby_attractions


class _FlightSignals(QObject):
    finished = pyqtSignal(int, str, str)


class _MapBridge(QObject):
    refreshFlightsRequested = pyqtSignal()
    attractionsRequested = pyqtSignal(float, float, str)
    externalUrlRequested = pyqtSignal(str)

    @pyqtSlot()
    def refreshFlights(self):
        self.refreshFlightsRequested.emit()

    @pyqtSlot(float, float, str)
    def loadAttractions(self, longitude: float, latitude: float, city: str):
        self.attractionsRequested.emit(longitude, latitude, city)

    @pyqtSlot(str)
    def openExternal(self, url: str):
        self.externalUrlRequested.emit(url)


class _FlightLookup(QRunnable):
    def __init__(self, request_id: int, direction: str, origin: str, destination: str, date: str):
        super().__init__()
        self.request_id, self.direction = request_id, direction
        self.origin, self.destination, self.date = origin, destination, date
        self.signals = _FlightSignals()

    def run(self):
        try:
            result = search_flights(self.origin, self.destination, self.date)
        except Exception as exc:
            result = f"航班查询失败：{exc}"
        self.signals.finished.emit(self.request_id, self.direction, result)


class _AttractionSignals(QObject):
    finished = pyqtSignal(int, str)


class _AttractionLookup(QRunnable):
    def __init__(self, request_id: int, longitude: float, latitude: float, city: str):
        super().__init__()
        self.request_id, self.longitude, self.latitude, self.city = request_id, longitude, latitude, city
        self.signals = _AttractionSignals()

    def run(self):
        try:
            result = {"items": search_nearby_attractions(self.longitude, self.latitude, self.city)}
        except Exception as exc:
            result = {"error": str(exc)}
        self.signals.finished.emit(self.request_id, json.dumps(result, ensure_ascii=False))

# 地图页面模板：占位符 {AMAP_KEY}、__ORIGIN__、__DEST__、__ORIGIN_LABEL__、__DEST_LABEL__
# 运行时替换。模板内其余花括号均为 JS 对象字面量，使用字符串替换而非 format 以保留原样。
_MAP_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>html,body{width:100%;height:100%;margin:0;padding:0;font-family:Arial,sans-serif}#layout{display:flex;width:100%;height:100%}#container{flex:1;min-width:0}#routes,#flights{position:relative;width:300px;box-sizing:border-box;background:#fff;border-left:1px solid #ddd}#routes{padding:16px 16px 76px;overflow:auto}#flights{padding:0;overflow:hidden}#flight-content{height:100%;box-sizing:border-box;padding:16px 16px 76px;overflow-y:auto}#routes h3,#flights h3{margin:0 0 12px;font-size:17px}#cities-toggle{display:block;margin:0 0 12px;font-size:14px;color:#374151}.route,.flight-card{padding:12px;margin:8px 0;border:1px solid #ddd;border-radius:8px;cursor:pointer}.route.active,.flight-card.active{border:2px solid #2563eb;background:#eff6ff}.route-title,.flight-title{font-weight:600}.route-meta,.flight-meta{margin-top:6px;color:#666;font-size:13px}.route-status,.flight-status{margin-top:6px;color:#888;font-size:12px}.flight-section{border-top:1px solid #eee;padding-top:10px;margin-top:12px}.flight-section h4{margin:4px 0;font-size:14px}.flight-time-filter{padding:8px 10px;margin:0 0 10px;border:1px solid #e2e8f0;border-radius:8px;background:#f8fafc}.flight-range-toggle{display:flex;width:100%;align-items:center;justify-content:space-between;padding:4px 0;border:0;background:transparent;color:#334155;font-weight:600;text-align:left;cursor:pointer}.flight-filter-summary{margin-left:auto;margin-right:8px;color:#64748b;font-size:12px;font-weight:400}.flight-time-controls{display:flex;align-items:center;gap:5px;margin-top:8px}.flight-time-controls input{width:78px;min-width:0;padding:5px;border:1px solid #cbd5e1;border-radius:5px}.flight-time-controls button{padding:6px 8px;border:0;border-radius:5px;background:#2563eb;color:#fff;cursor:pointer}.flight-time-hint{margin-top:6px;color:#64748b;font-size:11px}.flight-toggle{display:block;margin:8px auto 12px;padding:6px 14px;border:1px solid #cbd5e1;border-radius:16px;background:#fff;color:#2563eb;font-size:13px;cursor:pointer}.flight-toggle:hover{background:#eff6ff}#refresh-routes,#refresh-flights{position:absolute;right:18px;bottom:18px;width:46px;height:46px;border:0;border-radius:50%;background:#2563eb;color:#fff;font-size:24px;cursor:pointer;box-shadow:0 2px 8px #0003}#refresh-routes:hover,#refresh-flights:hover{background:#1d4ed8}</style>
<script>window._AMapSecurityConfig = { securityJsCode: "{AMAP_SECURITY_CODE}" };</script>
<script src="https://webapi.amap.com/maps?v=2.0&key={AMAP_KEY}&plugin=AMap.Geocoder,AMap.Driving"></script>
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
</head>
<body>
<div id="layout"><div id="container"></div><aside id="routes" style="display:__ROUTES_DISPLAY__"><h3>驾车路线</h3><label id="cities-toggle"><input type="checkbox" id="show-cities" onchange="toggleCities(this.checked)"> 显示沿途的城市</label><div id="route-list"></div><button id="refresh-routes" title="刷新路线" onclick="refreshRoutes()">↻</button></aside><aside id="flights" style="display:__FLIGHTS_DISPLAY__"><div id="flight-content"><h3>往返航班</h3><div class="flight-time-filter"><button id="flight-range-toggle" class="flight-range-toggle" onclick="toggleFlightTimeFilter()"><span>起飞时间筛选</span><span id="flight-filter-summary" class="flight-filter-summary">00:00–23:59</span><span id="flight-filter-arrow">展开⌄</span></button><div id="flight-filter-controls" style="display:none"><div class="flight-time-controls"><input id="flight-time-start" type="time" value="00:00" step="60" aria-label="起飞开始时间"><span>至</span><input id="flight-time-end" type="time" value="23:59" step="60" aria-label="起飞结束时间"><button onclick="applyFlightTimeFilter()">筛选</button></div><div id="flight-time-hint" class="flight-time-hint">可滚轮调整或直接输入，时间段至少 1 小时</div></div></div><section class="flight-section"><h4 id="outbound-heading">去程航班</h4><div id="outbound-flights" class="flight-status">航班选项将在这里显示</div><button id="outbound-toggle" class="flight-toggle" style="display:none" onclick="toggleFlights('outbound')">显示全部</button></section><section class="flight-section"><h4 id="return-heading">返程航班</h4><div id="return-flights" class="flight-status">航班选项将在这里显示</div><button id="return-toggle" class="flight-toggle" style="display:none" onclick="toggleFlights('return')">显示全部</button></section></div><button id="refresh-flights" title="刷新航班" onclick="refreshFlights()">↻</button></aside></div>
<script>
var map = new AMap.Map("container", {zoom:11, center:[116.397428,39.90923]});
var geocoder = new AMap.Geocoder();
var requestId = 0;
var currentTransport = "car";
var flightQueryDates = {outbound:"", return:""};
var flightResultsRaw = {outbound:null, return:null};
var flightTimeRange = {start:0, end:1439};
var drivingColors = ["#2563eb", "#16a34a", "#ea580c"];
var drivingNames = ["最快", "避开收费", "避开高速"];
var routeResults = [null, null, null], routeRenderers = [null, null, null], selectedRoute = 0;
var routeLines = [];
var cityMarkers = [], attractionMarkers = [], showCities = false;
var routeStart = null, routeEnd = null, retryCount = 0, retryTimer = null, routeRequestToken = 0;
function finalize(points) {
  if (points.length === 0) return;
  if (points.length >= 2) {
    new AMap.Polyline({path: points, map: map, strokeColor: "#2563eb",
                       strokeWeight: 3, strokeStyle: "dashed"});
    map.setFitView();
  } else if (points.length === 1) {
    map.setCenter(points[0]);
    map.setZoom(12);
  }
}
window.updatePlaces = function(origin, destination, originLabel, destLabel, transport, startDate, endDate) {
  transport = String(transport || "car").toLowerCase();
  var isPlane = ["plane", "flight", "air", "airplane", "飞机"].indexOf(transport) >= 0;
  var isCar = ["car", "drive", "driving", "自驾", "汽车"].indexOf(transport) >= 0;
  currentTransport = isPlane ? "plane" : (isCar ? "car" : "rail");
  flightQueryDates = {outbound:startDate || "", return:endDate || ""};
  map.clearMap();
  attractionMarkers = [];
  if (retryTimer) clearTimeout(retryTimer); retryTimer = null; retryCount = 0;
  cityMarkers = [];
  routeResults = [null, null, null]; routeRenderers = [null, null, null]; selectedRoute = 0;
  routeLines.forEach(function(line) { line.setMap(null); }); routeLines = [];
  document.getElementById("route-list").innerHTML = "";
  document.getElementById("routes").style.display = isCar ? "block" : "none";
  document.getElementById("flights").style.display = isPlane ? "block" : "none";
  document.getElementById("attractions").style.display = "none";
  document.getElementById("outbound-flights").textContent = isPlane ? "正在查询去程航班…" : "";
  document.getElementById("return-flights").textContent = isPlane ? "正在查询返程航班…" : "";
  document.getElementById("outbound-heading").textContent = "去程航班 · " + (startDate || "未设置日期");
  document.getElementById("return-heading").textContent = "返程航班 · " + (endDate || "未设置日期");
  if (isCar) showRouteCards("等待地点定位…");
  var currentRequest = ++requestId;
  var points = {origin:null, destination:null};
  var pending = (origin ? 1 : 0) + (destination ? 1 : 0);
  if (!pending) return;
  function done() {
    pending--;
    if (pending === 0 && currentRequest === requestId) {
      var pair = [points.origin, points.destination].filter(Boolean);
      if (isCar && points.origin && points.destination) {
        routeStart = points.origin; routeEnd = points.destination;
        routeByCar(routeStart, routeEnd, currentRequest);
      } else finalize(pair);
    }
  }
  locate(origin, originLabel, "origin", currentRequest, points, done);
  locate(destination, destLabel, "destination", currentRequest, points, done);
};
window.setFlightResults = function(direction, text) {
  var node = document.getElementById(direction === "outbound" ? "outbound-flights" : "return-flights");
  var toggle = document.getElementById(direction === "outbound" ? "outbound-toggle" : "return-toggle");
  if (!node) return;
  flightResultsRaw[direction] = text;
  if (toggle) toggle.style.display = "none";
  var data;
  try { data = JSON.parse(text); } catch (_) { node.textContent = text; return; }
  var flights = [];
  function collect(value) {
    if (typeof value === "string") {
      try { collect(JSON.parse(value)); } catch (_) {}
      return;
    }
    if (Array.isArray(value)) { value.forEach(collect); return; }
    if (!value || typeof value !== "object") return;
    var keys = Object.keys(value).map(function(k) { return k.toLowerCase(); });
    if (keys.some(function(k) { return ["flightno","flight_num","flightnumber","flight_number","fnum","flightcode"].indexOf(k) >= 0; })) flights.push(value);
    Object.keys(value).forEach(function(k) { collect(value[k]); });
  }
  collect(data);
  var unique = {}, deduped = [];
  flights.forEach(function(f) { var k = JSON.stringify(f); if (!unique[k]) { unique[k] = true; deduped.push(f); } });
  flights = deduped;
  if (!flights.length) { node.textContent = text; return; }
  var queryDateMatch = String(flightQueryDates[direction] || "").match(/([0-9]{4})[-/.年]([0-9]{1,2})[-/.月]([0-9]{1,2})/);
  var queryDateKey = queryDateMatch ? queryDateMatch[1] + "-" + String(queryDateMatch[2]).padStart(2, "0") + "-" + String(queryDateMatch[3]).padStart(2, "0") : null;
  var cards = flights.map(function(f, originalIndex) {
    function val(aliases, kind) {
      var wanted = aliases.map(function(k) { return k.toLowerCase().replace(/[^a-z\u4e00-\u9fff]/g, ""); });
      function normalized(k) { return k.toLowerCase().replace(/[^a-z\u4e00-\u9fff]/g, ""); }
      function search(obj, depth, path, heuristic) {
        if (!obj || typeof obj !== "object" || depth > 8) return null;
        var keys = Object.keys(obj);
        for (var i = 0; i < keys.length; i++) {
          var k = keys[i];
          var value = obj[k];
          var keyName = normalized(k), fullPath = path.concat([keyName]).join("_");
          var exact = wanted.indexOf(keyName) >= 0;
          var pathParts = path.concat([keyName]);
          var hasTime = pathParts.some(function(part) { return /(?:time|date|datetime|时|时间|时刻|起飞|出发|到达|落地)$/.test(part) || /^(std|sta)$/.test(part); });
          var hasDirection = pathParts.some(function(part) { return kind === "dep"
            ? /^(dep|depart|departure|takeoff|std)(?:[a-z]|$)/.test(part) || /^(起飞|出发)/.test(part)
            : /^(arr|arrive|arrival|landing|land|sta)(?:[a-z]|$)/.test(part) || /^(到达|落地)/.test(part); });
          var contextTime = /(^|_)(time|date|datetime|std|sta|时|时间|时刻)$/.test(keyName) && hasDirection;
          if ((exact || (heuristic && hasTime && hasDirection)) && value != null && typeof value !== "object" && String(value).trim()) {
            return value;
          }
          if (value && typeof value === "object") {
            var nested = search(value, depth + 1, path.concat([keyName]), heuristic);
            if (nested != null) return nested;
          }
          if (heuristic && contextTime && value != null && typeof value !== "object" && String(value).trim()) return value;
        }
        return null;
      }
      var found = search(f, 0, [], false);
      if (found == null && kind) found = search(f, 0, [], true);
      return found == null ? "—" : String(found);
    }
    function parseFlightTime(value) {
      if (value == null || value === "—") return null;
      var text = String(value).trim();
      var compact = text.match(/^([0-9]{4})([0-9]{2})([0-9]{2})([0-9]{2})([0-9]{2})([0-9]{2})$/);
      if (compact) return {date: compact[1] + "-" + compact[2] + "-" + compact[3], time: compact[4] + ":" + compact[5] + ":" + compact[6]};
      if (/^([0-9]{3,4}|[0-9]{6})$/.test(text)) {
        var compactHour, compactMinute, compactSecond = 0;
        if (text.length === 3) { compactHour = Number(text.slice(0, 1)); compactMinute = Number(text.slice(1, 3)); }
        else if (text.length === 4) { compactHour = Number(text.slice(0, 2)); compactMinute = Number(text.slice(2, 4)); }
        else { compactHour = Number(text.slice(0, 2)); compactMinute = Number(text.slice(2, 4)); compactSecond = Number(text.slice(4, 6)); }
        if (compactHour <= 23 && compactMinute <= 59 && compactSecond <= 59) {
          return {date: null, time: String(compactHour).padStart(2, "0") + ":" + String(compactMinute).padStart(2, "0") + ":" + String(compactSecond).padStart(2, "0")};
        }
      }
      var numericTime = /^[0-9]{10,13}$/.test(text) ? Number(text) : NaN;
      if (isFinite(numericTime)) {
        var epochDate = new Date(text.length === 10 ? numericTime * 1000 : numericTime);
        return {date: epochDate.getFullYear() + "-" + String(epochDate.getMonth() + 1).padStart(2, "0") + "-" + String(epochDate.getDate()).padStart(2, "0"),
          time: String(epochDate.getHours()).padStart(2, "0") + ":" + String(epochDate.getMinutes()).padStart(2, "0") + ":" + String(epochDate.getSeconds()).padStart(2, "0")};
      }
      var dateMatch = text.match(/([0-9]{4})[-/.年]([0-9]{1,2})[-/.月]([0-9]{1,2})(?:日)?/);
      var timeMatch = text.match(/(?:T|\\s|^)([0-9]{1,2})[:：]([0-9]{2})(?:[:：]([0-9]{2}))?/);
      if (!timeMatch) timeMatch = text.match(/([0-9]{1,2})时([0-9]{1,2})分(?:([0-9]{1,2})秒)?/);
      if (!timeMatch) return null;
      var clock = String(timeMatch[1]).padStart(2, "0") + ":" + String(timeMatch[2]).padStart(2, "0") + ":" + String(timeMatch[3] || "00").padStart(2, "0");
      var dateKey = dateMatch ? dateMatch[1] + "-" + String(dateMatch[2]).padStart(2, "0") + "-" + String(dateMatch[3]).padStart(2, "0") : null;
      return {date: dateKey, time: clock};
    }
    var departureRaw = val(["depTime","departureTime","departure_time","departTime","departurePlanTime","departureEstimateTime","departureActualTime","scheduledDeparture","scheduledDepartureTime","scheduledDepTime","depDateTime","departureDateTime","departureTimeLocal","depTimeLocal","takeoffTime","takeOffTime","stdTime","std","expectedTakeoffTime","预计起飞时间","计划起飞时间","起飞时间","出发时间"], "dep");
    var arrivalRaw = val(["arrTime","arrivalTime","arrival_time","arriveTime","arrivalPlanTime","arrivalEstimateTime","arrivalActualTime","scheduledArrival","scheduledArrivalTime","scheduledArrTime","arrDateTime","arrivalDateTime","arrivalTimeLocal","arrTimeLocal","landingTime","staTime","sta","expectedArrivalTime","预计到达时间","计划到达时间","落地时间","到达时间"], "arr");
    var departure = parseFlightTime(departureRaw), arrival = parseFlightTime(arrivalRaw);
    if (departure && flightTimeRange) {
      var departureParts = departure.time.split(":");
      var departureMinutes = Number(departureParts[0]) * 60 + Number(departureParts[1]);
      var startMinutes = flightTimeRange.start, endMinutes = flightTimeRange.end;
      var inSelectedRange = startMinutes === endMinutes || (startMinutes < endMinutes
        ? departureMinutes >= startMinutes && departureMinutes <= endMinutes
        : departureMinutes >= startMinutes || departureMinutes <= endMinutes);
      if (!inSelectedRange) return null;
    }
    if (arrival) {
      var today = new Date();
      var fallbackDate = queryDateKey
        ? queryDateKey
        : today.getFullYear() + "-" + String(today.getMonth() + 1).padStart(2, "0") + "-" + String(today.getDate()).padStart(2, "0");
      var arrivalDate = arrival.date || (departure && departure.date) || fallbackDate;
      var arrivalDateTime = new Date(arrivalDate + "T" + arrival.time);
      if (!arrival.date && departure && departure.time > arrival.time) arrivalDateTime.setDate(arrivalDateTime.getDate() + 1);
      if (!isNaN(arrivalDateTime.getTime()) && arrivalDateTime.getTime() < Date.now()) return null;
    }
    var differentDays = departure && arrival && departure.date && arrival.date && departure.date !== arrival.date;
    var departureDisplay = departure ? (differentDays ? departure.date.slice(5) + " " : "") + departure.time : (departureRaw === "—" ? "—" : departureRaw);
    var arrivalDisplay = arrival ? (differentDays ? arrival.date.slice(5) + " " : "") + arrival.time : (arrivalRaw === "—" ? "—" : arrivalRaw);
    function airportTerminal(airportAliases, terminalAliases) {
      var airport = val(airportAliases), terminal = val(terminalAliases);
      if (terminal !== "—" && (/[0-9]{4}[-/.年][0-9]{1,2}[-/.月][0-9]{1,2}/.test(terminal) || /[0-9]{1,2}[:：][0-9]{2}(:[0-9]{2})?/.test(terminal))) terminal = "—";
      var airportNames = {
        PEK:"北京首都国际机场", PKX:"北京大兴国际机场", PVG:"上海浦东国际机场", SHA:"上海虹桥国际机场",
        CAN:"广州白云国际机场", SZX:"深圳宝安国际机场", CSX:"长沙黄花国际机场", CTU:"成都双流国际机场",
        TFU:"成都天府国际机场", HGH:"杭州萧山国际机场", WUH:"武汉天河国际机场", XIY:"西安咸阳国际机场",
        CKG:"重庆江北国际机场", NKG:"南京禄口国际机场", XMN:"厦门高崎国际机场", KMG:"昆明长水国际机场",
        HRB:"哈尔滨太平国际机场", SHE:"沈阳桃仙国际机场", TAO:"青岛胶东国际机场", TSN:"天津滨海国际机场",
        CGO:"郑州新郑国际机场", CGQ:"长春龙嘉国际机场", FOC:"福州长乐国际机场", KHN:"南昌昌北国际机场",
        KWE:"贵阳龙洞堡国际机场", NNG:"南宁吴圩国际机场", HAK:"海口美兰国际机场", SYX:"三亚凤凰国际机场",
        URC:"乌鲁木齐天山国际机场", LXA:"拉萨贡嘎国际机场", NGB:"宁波栎社国际机场", WNZ:"温州龙湾国际机场",
        TNA:"济南遥墙国际机场", HFE:"合肥新桥国际机场", TYN:"太原武宿国际机场", SJW:"石家庄正定国际机场",
        LHW:"兰州中川国际机场", INC:"银川河东国际机场", HET:"呼和浩特白塔国际机场", ZUH:"珠海金湾机场",
        WUX:"无锡硕放机场", CZX:"常州奔牛机场", YNT:"烟台蓬莱国际机场", KWL:"桂林两江国际机场",
        LJG:"丽江三义机场", DLC:"大连周水子国际机场", HKG:"香港国际机场", MFM:"澳门国际机场", TPE:"桃园国际机场"
      };
      if (airport !== "—") {
        var code = airport.trim().toUpperCase();
        if (airportNames[code]) airport = airportNames[code];
      }
      if (airport === "—" && terminal === "—") return "—";
      if (airport === "—") return "机场信息未提供" + (terminal === "—" ? "" : " · " + terminal);
      if (terminal === "—" || airport.toLowerCase().indexOf(terminal.toLowerCase()) >= 0) return airport;
      return airport + " · " + terminal;
    }
    var fields = [
      ["出发时间", departureDisplay],
      ["到达时间", arrivalDisplay],
      ["出发机场/航站楼", airportTerminal(["depAirportName","departureAirportName","departureAirport","depAirport","depAirportCn","depPortName","departureAirportCode","depAirportCode","出发机场","出发机场名称"], ["depTerminal","departureTerminal","departTerminal","出发航站楼"])],
      ["到达机场/航站楼", airportTerminal(["arrAirportName","arrivalAirportName","arrivalAirport","arrAirport","arrAirportCn","arrPortName","arrivalAirportCode","arrAirportCode","到达机场","到达机场名称"], ["arrTerminal","arrivalTerminal","arriveTerminal","到达航站楼"])],
      ["登机口", val(["boardingGate","gate","gateNo","登机口"])],
    ];
    var sortDate = departure && departure.date ? departure.date : queryDateKey;
    var sortKey = departure ? (sortDate || "9999-99-99") + "T" + departure.time : "9999-99-99T99:99:99";
    return {sortKey:sortKey, originalIndex:originalIndex, html:'<article class="flight-card">' + fields.map(function(pair) {
      return '<div class="flight-meta"><strong>' + pair[0] + '：</strong>' + escapeHtml(pair[1]) + '</div>';
    }).join("") + '</article>'};
  }).filter(Boolean);
  if (!cards.length) {
    node.textContent = "当前时间段没有符合条件的航班";
    return;
  }
  cards.sort(function(a, b) { return a.sortKey.localeCompare(b.sortKey) || a.originalIndex - b.originalIndex; });
  node.innerHTML = cards.map(function(card) { return card.html; }).join("");
  var cardNodes = node.querySelectorAll(".flight-card");
  if (cardNodes.length > 3 && toggle) {
    for (var i = 3; i < cardNodes.length; i++) cardNodes[i].style.display = "none";
    toggle.textContent = "显示全部（" + cardNodes.length + "）";
    toggle.setAttribute("data-expanded", "false");
    toggle.style.display = "block";
  }
};
window.applyFlightTimeFilter = function() {
  var startText = document.getElementById("flight-time-start").value;
  var endText = document.getElementById("flight-time-end").value;
  var hint = document.getElementById("flight-time-hint");
  if (!startText || !endText) {
    hint.textContent = "请选择完整的开始和结束时间";
    hint.style.color = "#dc2626";
    return;
  }
  var start = startText.split(":").map(Number), end = endText.split(":").map(Number);
  var startMinutes = start[0] * 60 + start[1], endMinutes = end[0] * 60 + end[1];
  var duration = endMinutes - startMinutes;
  if (duration <= 0) duration += 24 * 60;
  if (duration < 60) {
    hint.textContent = "时间段间隔必须至少 1 小时";
    hint.style.color = "#dc2626";
    return;
  }
  flightTimeRange = {start:startMinutes, end:endMinutes};
  document.getElementById("flight-filter-summary").textContent = startText + "–" + endText;
  hint.textContent = "已按起飞时间筛选：" + startText + " 至 " + endText;
  hint.style.color = "#15803d";
  ["outbound", "return"].forEach(function(direction) {
    if (flightResultsRaw[direction] != null) window.setFlightResults(direction, flightResultsRaw[direction]);
  });
};
window.toggleFlightTimeFilter = function() {
  var controls = document.getElementById("flight-filter-controls");
  var arrow = document.getElementById("flight-filter-arrow");
  var expanded = controls.style.display === "none";
  controls.style.display = expanded ? "block" : "none";
  arrow.textContent = expanded ? "收起⌃" : "展开⌄";
};
window.toggleFlights = function(direction) {
  var node = document.getElementById(direction === "outbound" ? "outbound-flights" : "return-flights");
  var toggle = document.getElementById(direction === "outbound" ? "outbound-toggle" : "return-toggle");
  if (!node || !toggle) return;
  var cards = node.querySelectorAll(".flight-card");
  var expanded = toggle.getAttribute("data-expanded") === "true";
  for (var i = 3; i < cards.length; i++) cards[i].style.display = expanded ? "none" : "";
  toggle.setAttribute("data-expanded", expanded ? "false" : "true");
  toggle.textContent = expanded ? "显示全部（" + cards.length + "）" : "收起";
};
window.refreshFlights = function() {
  document.getElementById("outbound-flights").textContent = "正在刷新去程航班…";
  document.getElementById("return-flights").textContent = "正在刷新返程航班…";
  document.getElementById("outbound-toggle").style.display = "none";
  document.getElementById("return-toggle").style.display = "none";
  if (window.mapBridge) window.mapBridge.refreshFlights();
};
window.setFlightStatus = function(message) {
  document.getElementById("outbound-flights").textContent = message;
  document.getElementById("return-flights").textContent = message;
};
window.openAttractions = function(city, longitude, latitude) {
  attractionMarkers.forEach(function(marker) { marker.setMap(null); });
  attractionMarkers = [];
  document.getElementById("routes").style.display = "none";
  document.getElementById("flights").style.display = "none";
  document.getElementById("attractions").style.display = "block";
  setTimeout(function() {
    map.resize();
    map.setZoomAndCenter(14, [longitude, latitude]);
  }, 100);
  document.getElementById("attraction-status").textContent = "正在查询附近景点…";
  if (window.mapBridge) window.mapBridge.loadAttractions(longitude, latitude, city);
};
window.closeAttractions = function() {
  document.getElementById("attractions").style.display = "none";
  document.getElementById("routes").style.display = currentTransport === "car" ? "block" : "none";
  document.getElementById("flights").style.display = currentTransport === "plane" ? "block" : "none";
};
window.setAttractionResults = function(text) {
  var status = document.getElementById("attraction-status");
  var list = document.getElementById("attraction-list");
  var data;
  try { data = JSON.parse(text); } catch (_) { status.textContent = "景点数据解析失败"; return; }
  if (data.error) { status.textContent = data.error; return; }
  var items = data.items || [];
  if (!items.length) { status.textContent = "附近暂未找到景点"; return; }
  status.textContent = "附近景点（" + items.length + "）";
  items.forEach(function(item) {
    var coordinates = String(item.location || "").split(",");
    var longitude = Number(coordinates[0]), latitude = Number(coordinates[1]);
    if (!isFinite(longitude) || !isFinite(latitude)) return;
    var marker = new AMap.Marker({position:[longitude, latitude], map:map, title:item.name || "景点",
      label:{content:escapeHtml(item.name || "景点"), direction:"top"}, zIndex:120});
    marker.on("click", function() { map.setCenter([longitude, latitude]); });
    attractionMarkers.push(marker);
  });
  list.innerHTML = items.map(function(item) {
    var photos = item.photos || [];
    var photo = photos.length ? '<img class="attraction-photo" src="' + escapeHtml(photos[0].url) + '" alt="景点照片" loading="lazy">' : '<div class="attraction-photo-placeholder">暂无照片</div>';
    var detail = escapeHtml(item.address || "附近景点");
    if (item.distance) detail += " · " + escapeHtml(item.distance) + " 米";
    var searchUrl = "https://www.xiaohongshu.com/search_result?keyword=" + encodeURIComponent(item.name || "");
    return '<article class="attraction-card">' + photo + '<div class="attraction-name">' + escapeHtml(item.name || "未命名景点") + '</div><div class="attraction-detail">' + detail + '</div><button class="xhs-search" data-url="' + escapeHtml(searchUrl) + '" onclick="window.openXhsSearch(this)">在小红书搜索攻略</button></article>';
  }).join("");
};
window.openXhsSearch = function(button) {
  if (window.mapBridge) window.mapBridge.openExternal(button.getAttribute("data-url"));
};
if (typeof qt !== "undefined" && typeof QWebChannel !== "undefined") {
  new QWebChannel(qt.webChannelTransport, function(channel) { window.mapBridge = channel.objects.mapBridge; });
}
function escapeHtml(s) { return String(s).replace(/[&<>"']/g, function(c) { return ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]; }); }
function routeByCar(start, end, currentRequest) {
  var policies = [AMap.DrivingPolicy.LEAST_TIME, AMap.DrivingPolicy.LEAST_FEE, AMap.DrivingPolicy.AVOID_HIGHWAYS];
  showRouteCards("正在规划…");
  requestMissingRoutes(policies, currentRequest, [0, 1, 2]);
}
function requestMissingRoutes(policies, currentRequest, indices) {
  var token = ++routeRequestToken;
  var remaining = indices.length, failures = [];
  if (!remaining) return;
  indices.forEach(function(index) {
    var policy = policies[index];
    var driving = new AMap.Driving({policy: policy,
      showTraffic: false, hideMarkers: true,
      polylineOptions: {strokeColor: drivingColors[index], strokeWeight: 6, strokeOpacity: 0.75}});
    routeRenderers[index] = driving;
    driving.search(routeStart, routeEnd, function(status, result) {
      if (currentRequest !== requestId || token !== routeRequestToken) return;
      if (status === "complete" && result.routes && result.routes.length) {
        routeResults[index] = result.routes[0];
        var card = document.getElementById("route-" + index);
        card.querySelector(".route-meta").textContent = formatDuration(result.routes[0].time) + " · " + formatDistance(result.routes[0].distance);
        card.querySelector(".route-status").textContent = index === 0 ? "最快路线" : "点击查看路线";
        selectRoute(index === 0 ? 0 : selectedRoute);
      } else {
        failures.push(index);
        var card = document.getElementById("route-" + index);
        if (card) card.querySelector(".route-meta").textContent = "路线失败：" + String(result || status || "未知错误");
        console.error("驾车路线失败:", drivingNames[index], status, result);
      }
      remaining--;
      if (remaining === 0) finishRouteBatch(failures, policies, currentRequest);
    });
  });
}
function finishRouteBatch(failures, policies, currentRequest) {
  if (!failures.length) {
    if (retryTimer) clearTimeout(retryTimer); retryTimer = null;
    return;
  }
  if (retryCount >= 5) {
    failures.forEach(function(i) {
      var card = document.getElementById("route-" + i);
      if (card) card.querySelector(".route-status").textContent = "自动重试已停止，请手动刷新试试。";
    });
    return;
  }
  retryCount++;
  failures.forEach(function(i) {
    var card = document.getElementById("route-" + i);
    if (card) card.querySelector(".route-status").textContent = "5 秒后自动重试（" + retryCount + "/5）";
  });
  retryTimer = setTimeout(function() {
    if (currentRequest === requestId) requestMissingRoutes(policies, currentRequest, failures);
  }, 5000);
}
window.refreshRoutes = function() {
  if (!routeStart || !routeEnd) return;
  if (retryTimer) clearTimeout(retryTimer); retryTimer = null;
  retryCount = 0;
  routeResults = [null, null, null];
  routeByCar(routeStart, routeEnd, requestId);
};
function showRouteCards(message) {
  document.getElementById("route-list").innerHTML = drivingNames.map(function(name, i) {
    return '<div class="route" id="route-' + i + '" onclick="selectRoute(' + i + ')"><div class="route-title">' + name + '</div><div class="route-meta">' + message + '</div><div class="route-status"></div></div>';
  }).join("");
}
function formatDuration(seconds) { var mins = Math.round(seconds / 60); return mins >= 60 ? Math.floor(mins / 60) + "小时" + (mins % 60) + "分" : mins + "分钟"; }
function formatDistance(meters) { return meters >= 1000 ? (meters / 1000).toFixed(1) + "公里" : meters + "米"; }
window.selectRoute = function(index) {
  if (!routeResults[index]) return;
  selectedRoute = index;
  routeRenderers.forEach(function(r) { if (r) r.clear(); });
  routeLines.forEach(function(line) { line.setMap(null); });
  routeLines = [];
  routeResults.forEach(function(route, routeIndex) {
    if (!route) return;
    var path = route.steps.reduce(function(all, step) { return all.concat(step.path || []); }, []);
    var active = routeIndex === index;
    routeLines.push(new AMap.Polyline({path:path,map:map,strokeColor:drivingColors[routeIndex],
      strokeWeight:active ? 7 : 4,strokeOpacity:active ? 0.95 : 0.2,
      zIndex:active ? 100 : 10}));
  });
  clearCityMarkers();
  if (showCities) markCitiesOnRoute(routeResults[index]);
  map.setFitView();
  document.querySelectorAll(".route").forEach(function(el, i) { el.classList.toggle("active", i === index); });
};
window.toggleCities = function(enabled) {
  showCities = enabled;
  clearCityMarkers();
  if (enabled && routeResults[selectedRoute]) markCitiesOnRoute(routeResults[selectedRoute]);
};
function clearCityMarkers() {
  cityMarkers.forEach(function(marker) { marker.setMap(null); });
  cityMarkers = [];
}
function markCitiesOnRoute(route) {
  if (!route) return;
  var path = route.steps.reduce(function(all, step) { return all.concat(step.path || []); }, []);
  if (path.length < 3) return;
  var samples = Math.min(8, Math.max(2, Math.floor(path.length / 40)));
  var seen = {};
  for (var i = 1; i <= samples; i++) {
    (function(point) {
      geocoder.getAddress(point, function(status, result) {
        if (!showCities || status !== "complete" || !result.regeocode) return;
        var component = result.regeocode.addressComponent || {};
        var city = component.city || component.province;
        if (!city || seen[city]) return;
        seen[city] = true;
        var marker = new AMap.Marker({position:point, map:map,
          label:{content:city, direction:"top"}, title:city});
        cityMarkers.push(marker);
      });
    })(path[Math.floor(i * (path.length - 1) / (samples + 1))]);
  }
}
function locate(city, label, role, currentRequest, points, done) {
  if (!city) return;
  geocoder.getLocation(city, function(status, result){
    if (currentRequest !== requestId) return;
    if (status === "complete" && result.info === "OK" && result.geocodes && result.geocodes.length) {
      var ll = result.geocodes[0].location;
      points[role] = ll;
      var marker = new AMap.Marker({position: ll, map: map, title: label,
                       label: {content: label, direction: "top"}});
      if (role === "destination") {
        marker.on("click", function() { window.openAttractions(city, ll.getLng(), ll.getLat()); });
      }
    } else {
      var errorCard = document.getElementById("route-" + (role === "origin" ? 0 : 1));
      if (errorCard) errorCard.querySelector(".route-meta").textContent = "地点定位失败：" + String(result || status || "未知错误");
      console.error("AMap geocoding failed:", city, status, result && result.info, result && result.infocode);
    }
    done();
  });
}
window.updatePlaces(__ORIGIN__, __DEST__, __ORIGIN_LABEL__, __DEST_LABEL__, __TRANSPORT__, __START_DATE__, __END_DATE__);
</script>
</body>
</html>
"""


def _extract_city(destination: str) -> str:
    """从地名串提取城市部分：取最后一个「.」之后的内容。

    如「湖南.长沙」→「长沙」、「Hunan.Changsha」→「Changsha」、「北京」→「北京」。
    """
    dest = (destination or "").strip()
    if "." in dest:
        dest = dest.rsplit(".", 1)[1].strip()
    return dest


def _js_string_safe(value) -> str:
    """生成可安全内嵌于 <script> 的 JS 字面量。

    JSON 编码后转义 < > &，避免「</script>」等序列被 HTML 解析器误判为脚本结束
    标签；ensure_ascii=True 顺带转义 U+2028/2029 等 JS 行终止符。
    """
    encoded = json.dumps(value, ensure_ascii=True)
    return (
        encoded.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def build_map_html(origin: str, destination: str, transport: str = "car", start_date: str = "", end_date: str = "") -> str:
    """根据出发地与目的地生成地图 HTML（地名经安全编码后注入）。"""
    origin_city = _extract_city(origin)
    dest_city = _extract_city(destination)
    html = _MAP_TEMPLATE.replace("{AMAP_KEY}", AMAP_KEY)
    html = html.replace("{AMAP_SECURITY_CODE}", AMAP_SECURITY_CODE)
    html = html.replace("</style>", "#attractions{position:relative;width:300px;box-sizing:border-box;background:#fff;border-left:1px solid #ddd;overflow:hidden}#attraction-content{height:100%;box-sizing:border-box;padding:16px 16px 20px;overflow-y:auto}.attraction-header{display:flex;align-items:center;gap:10px;margin-bottom:12px}.attraction-header h3{margin:0;font-size:17px}.attraction-back{border:0;background:transparent;color:#2563eb;font-size:14px;cursor:pointer}.attraction-card{padding:10px;margin:10px 0;border:1px solid #e5e7eb;border-radius:8px;background:#fff}.attraction-photo{display:block;width:100%;height:135px;object-fit:cover;border-radius:6px;background:#f3f4f6}.attraction-photo-placeholder{display:flex;height:100px;align-items:center;justify-content:center;border-radius:6px;background:#f3f4f6;color:#94a3b8;font-size:13px}.attraction-name{margin-top:8px;font-weight:600}.attraction-detail{margin-top:4px;color:#64748b;font-size:12px}.xhs-search{margin-top:9px;padding:6px 10px;border:0;border-radius:5px;background:#f43f5e;color:#fff;font-size:12px;cursor:pointer}#attraction-status{color:#64748b;font-size:13px}</style>", 1)
    html = html.replace("</aside></div>\n<script>", "</aside><aside id=\"attractions\" style=\"display:none\"><div id=\"attraction-content\"><div class=\"attraction-header\"><button class=\"attraction-back\" onclick=\"closeAttractions()\">返回</button><h3>目的地附近景点</h3></div><div id=\"attraction-status\">点击地图上的目的地标志查看景点</div><div id=\"attraction-list\"></div></div></aside></div>\n<script>", 1)
    html = html.replace("__ORIGIN__", _js_string_safe(origin_city or None))
    html = html.replace("__DEST__", _js_string_safe(dest_city or None))
    normalized_transport = _normalize_transport(transport)
    html = html.replace("__TRANSPORT__", _js_string_safe(normalized_transport))
    html = html.replace("__ROUTES_DISPLAY__", "block" if normalized_transport == "car" else "none")
    html = html.replace("__FLIGHTS_DISPLAY__", "block" if normalized_transport == "plane" else "none")
    html = html.replace("__START_DATE__", _js_string_safe(start_date))
    html = html.replace("__END_DATE__", _js_string_safe(end_date))
    html = html.replace("__ORIGIN_LABEL__", _js_string_safe(origin or i18n.t("map_label_origin")))
    html = html.replace("__DEST_LABEL__", _js_string_safe(destination or i18n.t("map_label_dest")))
    return html


def _normalize_transport(value: str | None) -> str:
    """兼容旧行程和界面传入的中文/英文出行方式值。"""
    normalized = (value or "").strip().lower()
    if normalized in {"plane", "flight", "air", "airplane", "飞机"}:
        return "plane"
    if normalized in {"car", "drive", "driving", "自驾", "汽车"}:
        return "car"
    if normalized in {"rail", "train", "铁路", "火车", "高铁"}:
        return "rail"
    return "car"


class MapViewWindow(QWidget):
    """独立的地图窗口（非模态），展示出发地→目的地两个位置。"""

    def __init__(self, origin: str, destination: str, parent=None, transport: str = "car", start_date: str = "", end_date: str = "") -> None:
        super().__init__(parent)
        self.origin = origin
        self.destination = destination
        self.transport = _normalize_transport(transport)
        self.start_date, self.end_date = start_date, end_date
        self._flight_request_id = 0
        self._flight_jobs = []
        self._last_flight_query = None
        self._attraction_request_id = 0
        self._attraction_jobs = []
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle(self._build_title())
        self.resize(880, 620)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.view = QWebEngineView(self)
        self._page_ready = False
        self._map_bridge = _MapBridge(self)
        self._map_bridge.refreshFlightsRequested.connect(self._refresh_flights)
        self._map_bridge.attractionsRequested.connect(self._search_attractions)
        self._map_bridge.externalUrlRequested.connect(self._open_external_url)
        self._web_channel = QWebChannel(self.view.page())
        self._web_channel.registerObject("mapBridge", self._map_bridge)
        self.view.page().setWebChannel(self._web_channel)
        self.view.loadFinished.connect(self._on_load_finished)
        self.view.setHtml(
            build_map_html(origin, destination, transport, start_date, end_date), QUrl("https://webapi.amap.com/")
        )
        layout.addWidget(self.view)

    def _on_load_finished(self, ok: bool) -> None:
        self._page_ready = ok
        if ok:
            self.update_places(self.origin, self.destination)
            self._query_flights_if_needed()

    def update_places(self, origin: str, destination: str, transport: str = None, start_date: str = None, end_date: str = None) -> None:
        """更新地图上的出发地和目的地标记。"""
        self.origin, self.destination = origin, destination
        if transport is not None:
            self.transport = _normalize_transport(transport)
        if start_date is not None:
            self.start_date = start_date
        if end_date is not None:
            self.end_date = end_date
        self.setWindowTitle(self._build_title())
        script = "window.updatePlaces(%s,%s,%s,%s,%s,%s,%s);" % (
            _js_string_safe(_extract_city(origin) or None),
            _js_string_safe(_extract_city(destination) or None),
            _js_string_safe(origin or i18n.t("map_label_origin")),
            _js_string_safe(destination or i18n.t("map_label_dest")),
            _js_string_safe(self.transport),
            _js_string_safe(self.start_date),
            _js_string_safe(self.end_date),
        )
        if self._page_ready:
            self.view.page().runJavaScript(script)
            self._query_flights_if_needed()

    def _query_flights_if_needed(self, force: bool = False) -> None:
        if not self._page_ready or self.transport != "plane":
            return
        key = (self.origin, self.destination, self.start_date, self.end_date)
        if key == self._last_flight_query and not force:
            return
        if not self.start_date or not self.end_date:
            return
        self._last_flight_query = key
        self._flight_request_id += 1
        request_id = self._flight_request_id
        for direction, date in (("outbound", self.start_date), ("return", self.end_date)):
            leg_origin, leg_destination = (self.origin, self.destination) if direction == "outbound" else (self.destination, self.origin)
            job = _FlightLookup(request_id, direction, leg_origin, leg_destination, date)
            job.signals.finished.connect(self._on_flight_result)
            self._flight_jobs.append(job)
            QThreadPool.globalInstance().start(job)

    def _refresh_flights(self) -> None:
        if self.transport != "plane":
            return
        if not self.start_date or not self.end_date:
            self.view.page().runJavaScript('window.setFlightStatus("请先设置出发日期和返程日期");')
            return
        self._last_flight_query = None
        self._query_flights_if_needed(force=True)

    def _on_flight_result(self, request_id: int, direction: str, result: str) -> None:
        if request_id != self._flight_request_id or not self._page_ready:
            return
        self.view.page().runJavaScript(
            "window.setFlightResults(%s,%s);" % (_js_string_safe(direction), _js_string_safe(result))
        )

    def _search_attractions(self, longitude: float, latitude: float, city: str) -> None:
        self._attraction_request_id += 1
        request_id = self._attraction_request_id
        job = _AttractionLookup(request_id, longitude, latitude, city)
        job.signals.finished.connect(self._on_attractions_result)
        self._attraction_jobs.append(job)
        QThreadPool.globalInstance().start(job)

    def _on_attractions_result(self, request_id: int, result: str) -> None:
        if request_id != self._attraction_request_id or not self._page_ready:
            return
        self.view.page().runJavaScript("window.setAttractionResults(%s);" % _js_string_safe(result))

    @staticmethod
    def _open_external_url(url: str) -> None:
        target = QUrl(url)
        host = target.host().lower()
        if target.scheme() == "https" and (host == "xiaohongshu.com" or host.endswith(".xiaohongshu.com")):
            QDesktopServices.openUrl(target)

    def _build_title(self) -> str:
        if self.origin:
            route = i18n.t("list_route").format(
                origin=self.origin, destination=self.destination or "—"
            )
        else:
            route = self.destination or "—"
        return f"{i18n.t('map_dialog_title')} - {route}"

    def retranslate_ui(self) -> None:
        self.setWindowTitle(self._build_title())
