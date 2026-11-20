package com.skycrawler.app

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import android.net.wifi.WifiNetworkSpecifier
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.PatternMatcher
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/**
 * Joins the robot's WiFi (SkyCrawler-XXXX), pins this app's traffic to that network
 * (it has no internet, so Android would otherwise send our packets over mobile data),
 * and keeps a WebSocket to ws://192.168.4.1:81.
 */
class RobotLink(private val ctx: Context, private val listener: Listener) {
    interface Listener {
        fun onStatus(text: String, connected: Boolean)
        fun onTelemetry(t: JSONObject)
    }

    private val cm = ctx.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
    private val main = Handler(Looper.getMainLooper())
    private var ws: WebSocket? = null
    private var callback: ConnectivityManager.NetworkCallback? = null
    private var client: OkHttpClient? = null
    @Volatile var connected = false; private set
    var host = "192.168.4.1"
    var password = "skycrawler"

    fun connect() {
        disconnect()
        status("Looking for SkyCrawler WiFi…", false)
        val req = NetworkRequest.Builder().addTransportType(NetworkCapabilities.TRANSPORT_WIFI)
            .removeCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            // Android 10+: the system shows a "connect to device" dialog listing SkyCrawler-* networks
            val spec = WifiNetworkSpecifier.Builder()
                .setSsidPattern(PatternMatcher("SkyCrawler-", PatternMatcher.PATTERN_PREFIX))
                .setWpa2Passphrase(password).build()
            req.setNetworkSpecifier(spec)
        }
        val cb = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) { main.post { openSocket(network) } }
            override fun onLost(network: Network) { main.post { status("WiFi lost", false) } }
            override fun onUnavailable() { main.post { status("Robot WiFi not found — is it on? (or join it in WiFi settings)", false) } }
        }
        callback = cb
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) cm.requestNetwork(req.build(), cb, 30000)
            else cm.requestNetwork(req.build(), cb)
        } catch (e: Exception) {
            status("WiFi request failed: ${e.message}", false)
        }
    }

    private fun openSocket(network: Network) {
        cm.bindProcessToNetwork(network)
        val c = OkHttpClient.Builder().socketFactory(network.socketFactory)
            .pingInterval(2, TimeUnit.SECONDS).connectTimeout(4, TimeUnit.SECONDS).build()
        client = c
        status("Connecting…", false)
        ws = c.newWebSocket(Request.Builder().url("ws://$host:81/").build(), object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) { connected = true; status("Connected", true) }
            override fun onMessage(webSocket: WebSocket, text: String) {
                try { val j = JSONObject(text); main.post { listener.onTelemetry(j) } } catch (_: Exception) { }
            }
            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) { connected = false; status("Disconnected", false) }
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                connected = false; status("Link error: ${t.message ?: "?"}", false)
                main.postDelayed({ if (!connected && callback != null) openSocket(network) }, 1500)   // keep retrying
            }
        })
    }

    fun sticks(lx: Float, ly: Float, rx: Float, ry: Float) {
        if (!connected) return
        ws?.send("{\"t\":\"in\",\"lx\":%.3f,\"ly\":%.3f,\"rx\":%.3f,\"ry\":%.3f}".format(java.util.Locale.US, lx, ly, rx, ry))
    }

    fun cmd(c: String, a: String = "", v: Float = 0f) {
        ws?.send(JSONObject().put("t", "cmd").put("c", c).put("a", a).put("v", v.toDouble()).toString())
    }

    fun trim(leg: Int, h: Float, k: Float) {
        ws?.send(JSONObject().put("t", "trim").put("leg", leg).put("h", h.toDouble()).put("k", k.toDouble()).toString())
    }

    fun disconnect() {
        connected = false
        ws?.close(1000, "bye"); ws = null
        callback?.let { try { cm.unregisterNetworkCallback(it) } catch (_: Exception) { } }
        callback = null
        cm.bindProcessToNetwork(null)
    }

    private fun status(s: String, ok: Boolean) { main.post { listener.onStatus(s, ok) } }
}
