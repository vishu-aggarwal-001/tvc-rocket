package com.skycrawler.app

import android.app.Activity
import android.app.AlertDialog
import android.content.Context
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.view.WindowInsets
import android.view.WindowInsetsController
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.SeekBar
import android.widget.TextView
import android.widget.Toast
import org.json.JSONObject

class MainActivity : Activity(), RobotLink.Listener {
    private lateinit var link: RobotLink
    private lateinit var left: JoystickView
    private lateinit var right: JoystickView
    private lateinit var status: TextView
    private lateinit var tele: TextView
    private lateinit var walkPanel: LinearLayout
    private lateinit var flyPanel: LinearLayout
    private lateinit var connectBtn: Button
    private lateinit var gaitBtn: Button
    private lateinit var armBtn: Button
    private val ui = Handler(Looper.getMainLooper())
    private var mode = "SIT"
    private var armed = false
    private var trot = false
    private var beeper = false
    private val trims = Array(4) { floatArrayOf(0f, 0f) }

    private val ORANGE = Color.parseColor("#FF7A1A")
    private val RED = Color.parseColor("#E5333B")
    private val BLUE = Color.parseColor("#2B6CFF")
    private val GREY = Color.parseColor("#2B2F36")

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        link = RobotLink(this, this)
        link.password = getPreferences(Context.MODE_PRIVATE).getString("pass", "skycrawler") ?: "skycrawler"
        setContentView(buildUi())
        immersive()
        ui.post(sendLoop)
    }

    override fun onResume() { super.onResume(); immersive() }
    override fun onDestroy() { link.disconnect(); super.onDestroy() }

    private fun immersive() {
        if (android.os.Build.VERSION.SDK_INT >= 30) {
            window.insetsController?.let {
                it.hide(WindowInsets.Type.systemBars())
                it.systemBarsBehavior = WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
            }
        }
    }

    // ------------------------------------------------------------------ UI
    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()
    private fun btn(text: String, color: Int = GREY, onClick: (() -> Unit)? = null) = Button(this).apply {
        this.text = text; isAllCaps = false; setTextColor(Color.WHITE); textSize = 15f
        background = GradientDrawable().apply { cornerRadius = dp(12).toFloat(); setColor(color) }
        setPadding(dp(14), dp(8), dp(14), dp(8))
        layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(46)).apply { setMargins(0, dp(4), 0, dp(4)) }
        if (onClick != null) setOnClickListener { haptic(); onClick() }
    }
    private fun row(vararg v: View) = LinearLayout(this).apply {
        orientation = LinearLayout.HORIZONTAL
        v.forEach { addView(it, LinearLayout.LayoutParams(0, dp(46), 1f).apply { setMargins(dp(3), dp(3), dp(3), dp(3)) }) }
    }

    private fun buildUi(): View {
        val root = FrameLayout(this).apply { setBackgroundColor(Color.parseColor("#121418")) }
        // top bar
        val top = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL; setPadding(dp(14), dp(8), dp(14), 0) }
        top.addView(TextView(this).apply { text = "SkyCrawler"; setTextColor(ORANGE); textSize = 22f; typeface = Typeface.DEFAULT_BOLD })
        status = TextView(this).apply { text = "Not connected"; setTextColor(Color.LTGRAY); textSize = 13f; setPadding(dp(14), 0, 0, 0) }
        top.addView(status, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        tele = TextView(this).apply { setTextColor(Color.WHITE); textSize = 14f; setPadding(0, 0, dp(10), 0) }
        top.addView(tele)
        connectBtn = btn("Connect", BLUE) { if (link.connected) link.disconnect().also { onStatus("Disconnected", false) } else link.connect() }
        top.addView(connectBtn, LinearLayout.LayoutParams(dp(120), dp(42)).apply { setMargins(dp(4), 0, dp(4), 0) })
        top.addView(btn("⚙") { settings() }, LinearLayout.LayoutParams(dp(52), dp(42)))
        root.addView(top, FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.TOP))

        // sticks
        left = JoystickView(this).apply { label = "MOVE / TURN" }
        right = JoystickView(this).apply { label = "HEIGHT" }
        root.addView(left, FrameLayout.LayoutParams(dp(230), dp(230), Gravity.BOTTOM or Gravity.START).apply { setMargins(dp(26), 0, 0, dp(34)) })
        root.addView(right, FrameLayout.LayoutParams(dp(230), dp(230), Gravity.BOTTOM or Gravity.END).apply { setMargins(0, 0, dp(26), dp(34)) })

        // centre: walk controls
        walkPanel = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        gaitBtn = btn("Gait: Creep") { trot = !trot; gaitBtn.text = if (trot) "Gait: Trot" else "Gait: Creep"; link.cmd("gait", if (trot) "trot" else "creep") }
        walkPanel.addView(row(btn("Stand") { link.cmd("stand") }, btn("Sit") { link.cmd("sit") }))
        walkPanel.addView(gaitBtn)
        walkPanel.addView(row(btn("👋 Wave") { link.cmd("trick", "wave") }, btn("💃 Dance") { link.cmd("trick", "dance") }, btn("🙇 Bow") { link.cmd("trick", "bow") }))
        walkPanel.addView(btn("✈  Transform to DRONE", ORANGE) { confirm("Transform to drone?", "Put the robot on flat open ground. The legs fold out onto their stops; propellers stay off until you arm.") { link.cmd("fly") } })

        // centre: fly controls
        flyPanel = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; visibility = View.GONE }
        armBtn = btn("Hold to ARM", ORANGE)
        armBtn.setOnTouchListener(holdToArm)
        flyPanel.addView(armBtn)
        flyPanel.addView(btn("DISARM", RED) { link.cmd("disarm"); haptic(80) }.apply { textSize = 20f; typeface = Typeface.DEFAULT_BOLD; layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(64)) })
        flyPanel.addView(row(btn("🔔 Beeper") { beeper = !beeper; link.cmd("beeper", "", if (beeper) 1f else 0f) },
            btn("🚶 Walk") { if (armed) toast("Land and disarm first") else link.cmd("walk") }))
        flyPanel.addView(TextView(this).apply { text = "Left: throttle / yaw   ·   Right: pitch / roll\nSelf-level (Angle) mode is always on."; setTextColor(Color.GRAY); textSize = 12f; gravity = Gravity.CENTER })

        val centre = ScrollView(this).apply { addView(FrameLayout(this@MainActivity).apply { addView(walkPanel); addView(flyPanel) }) }
        root.addView(centre, FrameLayout.LayoutParams(dp(300), ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.CENTER).apply { topMargin = dp(40) })
        return root
    }

    private fun setFlyUi(fly: Boolean) {
        val wasFly = flyPanel.visibility == View.VISIBLE
        if (fly == wasFly) return
        walkPanel.visibility = if (fly) View.GONE else View.VISIBLE
        flyPanel.visibility = if (fly) View.VISIBLE else View.GONE
        left.springY = !fly
        if (fly) { left.setThrottle(-1f); left.label = "THROTTLE / YAW"; right.label = "PITCH / ROLL" }
        else { left.label = "MOVE / TURN"; right.label = "HEIGHT" }
        left.invalidate(); right.invalidate()
    }

    // hold the ARM button for one second
    private var armStart = 0L
    private val armTick = object : Runnable {
        override fun run() {
            val held = System.currentTimeMillis() - armStart
            if (held >= 1000) { link.cmd("arm"); haptic(120); armBtn.text = "Hold to ARM"; armStart = 0; return }
            armBtn.text = "Arming… ${(100 * held / 1000)}%"
            ui.postDelayed(this, 50)
        }
    }
    private val holdToArm = View.OnTouchListener { _, e ->
        when (e.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                if (left.sy > -0.9f) toast("Throttle all the way down first") else { armStart = System.currentTimeMillis(); ui.post(armTick) }
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> { ui.removeCallbacks(armTick); armBtn.text = "Hold to ARM"; armStart = 0 }
        }
        true
    }

    private val sendLoop = object : Runnable {
        override fun run() {
            link.sticks(left.sx, left.sy, right.sx, right.sy)
            ui.postDelayed(this, 33)    // ~30 Hz: the robot fails safe if packets stop for 0.35 s
        }
    }

    private fun settings() {
        val box = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(dp(18), dp(8), dp(18), dp(8)) }
        val names = arrayOf("Front right", "Front left", "Back left", "Back right")
        box.addView(TextView(this).apply { text = "Leg trims (degrees). Stand the robot, then nudge each joint until the legs look square. In drone mode the knees should sit flat on their stops."; setTextColor(Color.LTGRAY) })
        for (leg in 0 until 4) for (j in 0..1) {
            val lbl = TextView(this).apply { setTextColor(Color.WHITE) }
            val sb = SeekBar(this).apply { max = 600; progress = ((trims[leg][j] + 30) * 10).toInt() }
            fun upd() { val v = sb.progress / 10f - 30; trims[leg][j] = v; lbl.text = "${names[leg]} ${if (j == 0) "hip" else "knee"}: %.1f°".format(v) }
            upd()
            sb.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(s: SeekBar?, p: Int, f: Boolean) { upd(); link.trim(leg, trims[leg][0], trims[leg][1]) }
                override fun onStartTrackingTouch(s: SeekBar?) {}
                override fun onStopTrackingTouch(s: SeekBar?) {}
            })
            box.addView(lbl); box.addView(sb)
        }
        box.addView(Button(this).apply {
            text = "Centre all servos (for fitting horns)"; isAllCaps = false
            setOnClickListener { link.cmd("centre") }
        })
        val pass = android.widget.EditText(this).apply { hint = "Robot WiFi password"; setText(link.password); setTextColor(Color.WHITE) }
        box.addView(pass)
        AlertDialog.Builder(this, android.R.style.Theme_DeviceDefault_Dialog_Alert)
            .setTitle("Settings & calibration")
            .setView(ScrollView(this).apply { addView(box) })
            .setPositiveButton("Save to robot") { _, _ ->
                link.cmd("trim_save")
                link.password = pass.text.toString()
                getPreferences(Context.MODE_PRIVATE).edit().putString("pass", link.password).apply()
            }
            .setNeutralButton("Relax servos") { _, _ -> link.cmd("relax") }
            .setNegativeButton("Close", null).show()
    }

    private fun confirm(title: String, msg: String, ok: () -> Unit) {
        AlertDialog.Builder(this, android.R.style.Theme_DeviceDefault_Dialog_Alert).setTitle(title).setMessage(msg)
            .setPositiveButton("Go") { _, _ -> ok() }.setNegativeButton("Cancel", null).show()
    }
    private fun toast(s: String) = Toast.makeText(this, s, Toast.LENGTH_SHORT).show()
    @Suppress("DEPRECATION")
    private fun haptic(ms: Long = 20) {
        val v = getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator ?: return
        v.vibrate(VibrationEffect.createOneShot(ms, VibrationEffect.DEFAULT_AMPLITUDE))
    }

    // ------------------------------------------------------------------ link callbacks
    override fun onStatus(text: String, connected: Boolean) {
        status.text = text
        connectBtn.text = if (connected) "Disconnect" else "Connect"
        if (!connected) tele.text = ""
    }

    override fun onTelemetry(t: JSONObject) {
        if (t.optString("t") != "tel") return
        mode = t.optString("mode", mode)
        armed = t.optBoolean("armed")
        val v = t.optDouble("vbat", 0.0); val cells = t.optInt("cells", 0)
        val bat = if (v > 1) (if (cells > 0) "%.2fV (%.2f/cell)".format(v, v / cells) else "%.2fV".format(v)) else "—"
        val fc = if (t.optBoolean("fc")) "FC ok" else "FC —"
        tele.text = "${if (armed) "⚠ ARMED" else mode}   🔋 $bat   $fc"
        tele.setTextColor(if (armed) RED else Color.WHITE)
        setFlyUi(mode == "FLY" || mode == "TO_FLY")
        val note = t.optString("note")
        if (note.isNotEmpty()) toast(note)
    }
}
