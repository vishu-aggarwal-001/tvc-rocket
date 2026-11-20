#include "net.h"
#include "config.h"
#include <WiFi.h>
#include <WebServer.h>
#include <WebSocketsServer.h>
#include <ArduinoJson.h>

namespace Net {
static WebSocketsServer ws(WS_PORT);
static WebServer http(80);
static Sticks st;
static uint32_t lastIn = 0;
static int clients = 0;
static CmdHandler handler = nullptr;
static char apName[24];

static float clampf(float v) { return v < -1 ? -1 : v > 1 ? 1 : v; }

static void onWs(uint8_t num, WStype_t type, uint8_t *payload, size_t len) {
  if (type == WStype_CONNECTED) { clients++; if (handler) handler("hello", "", 0); return; }
  if (type == WStype_DISCONNECTED) { clients = max(0, clients - 1); return; }
  if (type != WStype_TEXT) return;
  JsonDocument d;
  if (deserializeJson(d, payload, len)) return;
  const char *t = d["t"] | "";
  if (!strcmp(t, "in")) {
    st.lx = clampf(d["lx"] | 0.0f); st.ly = clampf(d["ly"] | 0.0f);
    st.rx = clampf(d["rx"] | 0.0f); st.ry = clampf(d["ry"] | 0.0f);
    lastIn = millis();
  } else if (!strcmp(t, "cmd") && handler) {
    handler(d["c"] | "", d["a"] | "", d["v"] | 0.0f);
    lastIn = millis();
  } else if (!strcmp(t, "trim") && handler) {
    // {"t":"trim","leg":0,"h":1.5,"k":-2}
    char a[24]; snprintf(a, sizeof a, "%d,%.2f,%.2f", (int)(d["leg"] | 0), (float)(d["h"] | 0.0f), (float)(d["k"] | 0.0f));
    handler("trim", a, 0);
  }
}

void begin(CmdHandler h) {
  handler = h;
  uint8_t mac[6]; WiFi.macAddress(mac);
  snprintf(apName, sizeof apName, "SkyCrawler-%02X%02X", mac[4], mac[5]);
  WiFi.mode(WIFI_AP);
  WiFi.softAP(apName, AP_PASS, 6, 0, 2);
  WiFi.setTxPower(WIFI_POWER_15dBm);
  ws.begin();
  ws.onEvent(onWs);
  http.on("/", []() {
    http.send(200, "text/html",
              "<html><body style='font-family:sans-serif;background:#111;color:#eee'><h2>SkyCrawler</h2>"
              "<p>Open the SkyCrawler app and press Connect.</p><p>WebSocket: ws://192.168.4.1:81</p>"
              "<p>Assembly: <a style='color:#6af' href='/centre'>Centre all servos</a> &middot; "
              "<a style='color:#6af' href='/relax'>Relax all servos</a> &middot; <a style='color:#6af' href='/sit'>Sit</a></p></body></html>");
  });
  for (const char *c : {"centre", "relax", "sit"}) {
    http.on(String("/") + c, [c]() { if (handler) handler(c, "", 0); http.sendHeader("Location", "/"); http.send(303); });
  }
  http.begin();
}

void loop() { ws.loop(); http.handleClient(); }
const Sticks &sticks() { return st; }
uint32_t lastInputMs() { return lastIn; }
bool connected() { return clients > 0 && millis() - lastIn < LINK_TIMEOUT_MS; }
void sendText(const String &s) { String c = s; ws.broadcastTXT(c); }
const char *ssid() { return apName; }
}  // namespace Net
