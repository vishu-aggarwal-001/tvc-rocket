package com.skycrawler.app

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.view.MotionEvent
import android.view.View
import kotlin.math.hypot
import kotlin.math.min

/**
 * A thumb stick. sx and sy are -1..1 (up = +1).
 * springY = false keeps the vertical position when released (a drone throttle stick).
 */
class JoystickView(context: Context) : View(context) {
    var sx = 0f; private set
    var sy = 0f; private set
    var springY = true
        set(v) { field = v; if (v) { sy = 0f }; invalidate() }
    var label = ""
    var accent = Color.parseColor("#FF7A1A")
    var onMove: ((Float, Float) -> Unit)? = null

    private val ring = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.STROKE; strokeWidth = 6f; color = Color.argb(120, 255, 255, 255) }
    private val fill = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.argb(40, 255, 255, 255) }
    private val knob = Paint(Paint.ANTI_ALIAS_FLAG)
    private val text = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.argb(160, 255, 255, 255); textAlign = Paint.Align.CENTER; textSize = 30f }
    private val cross = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.argb(50, 255, 255, 255); strokeWidth = 3f }

    fun reset() { sx = 0f; if (springY) sy = 0f; invalidate(); onMove?.invoke(sx, sy) }
    fun setThrottle(v: Float) { sy = v; invalidate() }

    override fun onDraw(c: Canvas) {
        val cx = width / 2f; val cy = height / 2f; val r = min(width, height) / 2f - 10f
        c.drawCircle(cx, cy, r, fill); c.drawCircle(cx, cy, r, ring)
        c.drawLine(cx - r, cy, cx + r, cy, cross); c.drawLine(cx, cy - r, cx, cy + r, cross)
        knob.color = accent
        c.drawCircle(cx + sx * r * 0.8f, cy - sy * r * 0.8f, r * 0.24f, knob)
        c.drawText(label, cx, cy + r + 34f, text)
    }

    @SuppressLint("ClickableViewAccessibility")
    override fun onTouchEvent(e: MotionEvent): Boolean {
        val cx = width / 2f; val cy = height / 2f; val r = min(width, height) / 2f * 0.8f
        when (e.actionMasked) {
            MotionEvent.ACTION_DOWN, MotionEvent.ACTION_MOVE -> {
                var dx = (e.x - cx) / r; var dy = -(e.y - cy) / r
                val m = hypot(dx, dy)
                if (m > 1f) { dx /= m; dy /= m }
                sx = dx; sy = dy
                parent.requestDisallowInterceptTouchEvent(true)
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> { sx = 0f; if (springY) sy = 0f }
        }
        invalidate(); onMove?.invoke(sx, sy)
        return true
    }
}
