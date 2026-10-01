// SPDX-License-Identifier: GPL-3.0-only
package ui.activity;

import android.graphics.*;
import android.view.*;
import java.util.*;
import org.libsdl.app.SDLActivity;

/** Original multitouch overlay: each finger keeps its assigned action until released. */
final class TouchControls extends View {
    private final GameActivity activity;
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Map<Integer, Integer> actions = new HashMap<>();
    private final Set<Integer> keys = new HashSet<>();
    private int move = -1, look = -1;
    private float lx, ly;
    private final int[] directions = {KeyEvent.KEYCODE_W, KeyEvent.KEYCODE_S, KeyEvent.KEYCODE_A, KeyEvent.KEYCODE_D};
    TouchControls(GameActivity a) { super(a); activity = a; setFocusable(false); }
    private float radius() { return Math.min(getWidth(), getHeight()) * .16f; }
    private float cx() { return radius() * 1.4f; }
    private float cy() { return getHeight() - radius() * 1.4f; }
    @Override protected void onDraw(Canvas c) {
        float r = radius(); paint.setColor(0x55777777); c.drawCircle(cx(), cy(), r, paint);
        paint.setColor(Color.WHITE); paint.setTextSize(Math.max(16, getHeight() * .035f));
        c.drawText("MOVE", cx() - r * .42f, cy() + 8, paint);
        c.drawText("Drag right to look", getWidth() * .5f, getHeight() * .12f, paint);
        button(c, "USE", 0); button(c, "JUMP", 1); button(c, "EXIT", 2);
    }
    private RectF rect(int i) {
        float w = getWidth() * .105f, h = getHeight() * .15f;
        return new RectF(getWidth() - w * (i == 2 ? 1.2f : 1.4f),
            i == 2 ? h * .2f : getHeight() - h * (i == 0 ? 1.4f : 2.7f),
            getWidth() - w * (i == 2 ? .2f : .4f), i == 2 ? h * 1.2f : getHeight() - h * (i == 0 ? .4f : 1.7f));
    }
    private void button(Canvas c, String label, int i) {
        RectF b = rect(i); paint.setColor(0x88606060); c.drawRoundRect(b, 14, 14, paint);
        paint.setColor(Color.WHITE); c.drawText(label, b.left + 10, b.centerY() + 7, paint);
    }
    private void key(int k, boolean down) {
        if (down && keys.add(k)) SDLActivity.onNativeKeyDown(k);
        else if (!down && keys.remove(k)) SDLActivity.onNativeKeyUp(k);
    }
    void release() { for (int k : new HashSet<>(keys)) key(k, false); actions.clear(); move = look = -1; }
    @Override public boolean onTouchEvent(MotionEvent e) {
        int a = e.getActionMasked(), ix = e.getActionIndex(), id = e.getPointerId(ix);
        if (a == MotionEvent.ACTION_CANCEL) { release(); return true; }
        if (a == MotionEvent.ACTION_DOWN || a == MotionEvent.ACTION_POINTER_DOWN) {
            float x = e.getX(ix), y = e.getY(ix);
            if (rect(2).contains(x, y)) { release(); activity.finish(); return true; }
            int k = rect(0).contains(x,y) ? KeyEvent.KEYCODE_SPACE : rect(1).contains(x,y) ? KeyEvent.KEYCODE_E : 0;
            if (k != 0) { if (!actions.containsValue(k)) { actions.put(id, k); key(k, true); } }
            else if (x < getWidth() * .4f && move == -1) move = id;
            else if (x >= getWidth() * .4f && look == -1) { look = id; lx = x; ly = y; }
        }
        if (a == MotionEvent.ACTION_UP || a == MotionEvent.ACTION_POINTER_UP) {
            Integer k = actions.remove(id); if (k != null) key(k, false);
            if (id == move) { move = -1; for (int d : directions) key(d, false); }
            if (id == look) look = -1;
        } else {
            int m = e.findPointerIndex(move);
            if (m >= 0) { float dx = e.getX(m)-cx(), dy = e.getY(m)-cy(), dead = radius() * .25f;
                key(directions[0], dy < -dead); key(directions[1], dy > dead); key(directions[2], dx < -dead); key(directions[3], dx > dead); }
            int l = e.findPointerIndex(look);
            if (l >= 0 && a == MotionEvent.ACTION_MOVE) {
                float x = e.getX(l), y = e.getY(l);
                SDLActivity.sendRelativeMouseMotion(Math.round((x-lx)*.6f), Math.round((y-ly)*.6f)); lx=x; ly=y;
            }
        }
        return true;
    }
}
