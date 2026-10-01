// SPDX-License-Identifier: GPL-3.0-only
package ui.activity;

import android.graphics.*;
import android.view.*;
import java.util.*;
import org.libsdl.app.SDLActivity;

/** Original multitouch overlay: each finger keeps its assigned action until released. */
final class TouchControls extends View {
    private static final int USE = 0, JUMP = 1, EXIT = 2, RUN = 3;
    private static final int ATK = 4, SNEAK = 5, WEAPON = 6, MAGIC = 7;
    private static final int INV = 8, MENU = 9, JOURNAL = 10, WAIT = 11, POV = 12;
    private static final int SDL_LEFT = 1, SDL_RIGHT = 3;
    // Grid index is the control id minus SNEAK. Column 0 lines up with USE/JUMP; row 0 is the upper row.
    private static final int[] GRID_COL = {1, 2, 2, 0, 0, 3, 1, 3};
    private static final int[] GRID_ROW = {1, 1, 0, 1, 0, 1, 0, 0};

    private final GameActivity activity;
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Map<Integer, Integer> actions = new HashMap<>();
    private final Map<Integer, Integer> mice = new HashMap<>();
    private final Set<Integer> keys = new HashSet<>();
    private final Set<Integer> mouseDown = new HashSet<>();
    private int move = -1, look = -1;
    private float lx, ly;
    private boolean running = true;
    private boolean shiftSent;
    private boolean sneaking;
    private boolean ctrlSent;
    private final int[] directions = {KeyEvent.KEYCODE_W, KeyEvent.KEYCODE_S, KeyEvent.KEYCODE_A, KeyEvent.KEYCODE_D};

    TouchControls(GameActivity a) { super(a); activity = a; setFocusable(false); }
    private float radius() { return Math.min(getWidth(), getHeight()) * .16f; }
    private float cx() { return radius() * 1.4f; }
    private float cy() { return getHeight() - radius() * 1.4f; }
    private float bw() { return getWidth() * .105f; }
    private float bh() { return getHeight() * .11f; }
    // Leaves the engine compass/minimap visible under USE. Not a gameplay constant.
    private float bottomGap() { return getHeight() * .13f; }

    @Override protected void onDraw(Canvas c) {
        float r = radius(); paint.setColor(0x55777777); c.drawCircle(cx(), cy(), r, paint);
        paint.setColor(Color.WHITE); paint.setTextSize(Math.max(16, getHeight() * .035f));
        c.drawText("MOVE", cx() - r * .42f, cy() + 8, paint);
        // Above the stick, not the top center. The engine name label sits there
        // (the Bandit caption in the published stair shot).
        paint.setTextSize(Math.max(14, getHeight() * .028f));
        c.drawText("Drag the right side to look", cx() - r, cy() - r - 8, paint);
        for (int i = 0; i <= POV; i++) button(c, label(i), i);
    }

    private String label(int i) {
        switch (i) {
            case USE: return "USE";
            case JUMP: return "JUMP";
            case EXIT: return "EXIT";
            case RUN: return running ? "WALK" : "RUN";
            case ATK: return "ATK";
            case SNEAK: return "SNEAK";
            case WEAPON: return "WEAPON";
            case MAGIC: return "MAGIC";
            case INV: return "INV";
            case MENU: return "MENU";
            case JOURNAL: return "JOURNAL";
            case WAIT: return "WAIT";
            default: return "POV";
        }
    }

    private RectF rect(int i) {
        float w = bw(), h = bh(), width = getWidth(), height = getHeight();
        if (i == RUN) return new RectF(width - w * 2.75f, h * .2f, width - w * 1.55f, h * 1.2f);
        if (i == EXIT)
            return new RectF(width - w * 1.2f, h * .2f, width - w * .2f, h * 1.2f);
        if (i == USE || i == JUMP) {
            float gap = bottomGap();
            return new RectF(width - w * 1.4f,
                height - gap - h * (i == USE ? 1.4f : 2.7f),
                width - w * .4f,
                height - gap - h * (i == USE ? .4f : 1.7f));
        }
        if (i == ATK) {
            float gap = bottomGap();
            return new RectF(width - w * 3.70f, height - gap - h * 2.7f, width - w * 1.55f, height - gap - h * .4f);
        }
        int g = i - SNEAK;
        float right = width - w * (0.4f + GRID_COL[g] * 1.15f);
        float top = h * (1.45f + GRID_ROW[g] * 1.25f);
        return new RectF(right - w, top, right, top + h);
    }

    private void button(Canvas c, String label, int i) {
        RectF b = rect(i);
        boolean on = (i == RUN && running) || (i == SNEAK && sneaking) || (i == ATK && mouseDown.contains(SDL_LEFT));
        paint.setColor(on ? 0xAA3D6B4F : 0x88606060);
        c.drawRoundRect(b, 14, 14, paint);
        paint.setColor(Color.WHITE);
        float size = Math.max(16f, getHeight() * .035f);
        paint.setTextSize(size);
        float limit = b.width() - 8f, measured = paint.measureText(label);
        if (limit > 0f && measured > limit) paint.setTextSize(size * limit / measured);
        paint.setTextAlign(Paint.Align.CENTER);
        c.drawText(label, b.centerX(), b.centerY() + paint.getTextSize() * .35f, paint);
        paint.setTextAlign(Paint.Align.LEFT);
    }

    private int keyCode(int control) {
        switch (control) {
            case USE: return KeyEvent.KEYCODE_SPACE;
            case JUMP: return KeyEvent.KEYCODE_E;
            case WEAPON: return KeyEvent.KEYCODE_F;
            case MAGIC: return KeyEvent.KEYCODE_R;
            case MENU: return KeyEvent.KEYCODE_ESCAPE;
            case JOURNAL: return KeyEvent.KEYCODE_J;
            case WAIT: return KeyEvent.KEYCODE_T;
            case POV: return KeyEvent.KEYCODE_TAB;
            default: return 0;
        }
    }

    private int controlAt(float x, float y) {
        for (int i = 0; i <= POV; i++) if (rect(i).contains(x, y)) return i;
        return -1;
    }

    private void key(int k, boolean down) {
        if (down && keys.add(k)) SDLActivity.onNativeKeyDown(k);
        else if (!down && keys.remove(k)) SDLActivity.onNativeKeyUp(k);
    }

    // sendMouseButton is the host injector (SDL button id). onNativeMouse also moves the pointer.
    private void mouse(int button, boolean down) {
        boolean changed = down ? mouseDown.add(button) : mouseDown.remove(button);
        if (!changed) return;
        SDLActivity.sendMouseButton(down ? 1 : 0, button);
        if (button == SDL_LEFT) invalidate();
    }

    private void take(int id, int control) {
        int k = keyCode(control);
        if (k != 0) {
            if (!actions.containsValue(k)) { actions.put(id, k); key(k, true); }
            return;
        }
        int sdlButton = control == ATK ? SDL_LEFT : control == INV ? SDL_RIGHT : 0;
        if (sdlButton != 0 && !mice.containsValue(sdlButton)) { mice.put(id, sdlButton); mouse(sdlButton, true); }
    }

    private void drop(int id) {
        Integer k = actions.remove(id);
        if (k != null) key(k, false);
        Integer sdlButton = mice.remove(id);
        if (sdlButton != null) mouse(sdlButton, false);
        if (id == move) { move = -1; for (int d : directions) key(d, false); }
        if (id == look) look = -1;
    }

    void syncRun() {
        if (running) SDLActivity.onNativeKeyDown(KeyEvent.KEYCODE_SHIFT_LEFT);
        else if (shiftSent) SDLActivity.onNativeKeyUp(KeyEvent.KEYCODE_SHIFT_LEFT);
        shiftSent = running;
        // Sneak holds Left Ctrl the same way run holds Shift. GameActivity calls syncRun() on focus.
        if (sneaking) SDLActivity.onNativeKeyDown(KeyEvent.KEYCODE_CTRL_LEFT);
        else if (ctrlSent) SDLActivity.onNativeKeyUp(KeyEvent.KEYCODE_CTRL_LEFT);
        ctrlSent = sneaking;
    }

    void release() {
        for (int k : new HashSet<>(keys)) key(k, false);
        if (shiftSent) SDLActivity.onNativeKeyUp(KeyEvent.KEYCODE_SHIFT_LEFT);
        shiftSent = false;
        if (ctrlSent) SDLActivity.onNativeKeyUp(KeyEvent.KEYCODE_CTRL_LEFT);
        ctrlSent = false;
        for (int sdlButton : new HashSet<>(mouseDown)) mouse(sdlButton, false);
        actions.clear();
        mice.clear();
        move = look = -1;
    }

    @Override public boolean onTouchEvent(MotionEvent e) {
        int a = e.getActionMasked(), ix = e.getActionIndex(), id = e.getPointerId(ix);
        if (a == MotionEvent.ACTION_CANCEL) { release(); return true; }
        if (a == MotionEvent.ACTION_DOWN || a == MotionEvent.ACTION_POINTER_DOWN) {
            float x = e.getX(ix), y = e.getY(ix);
            int c = controlAt(x, y);
            if (c == EXIT) { release(); activity.finish(); return true; }
            if (c == RUN) { running = !running; syncRun(); invalidate(); }
            else if (c == SNEAK) { sneaking = !sneaking; syncRun(); invalidate(); }
            else if (c >= 0) take(id, c);
            else if (x < getWidth() * .4f && move == -1) move = id;
            else if (x >= getWidth() * .4f && look == -1) { look = id; lx = x; ly = y; }
        }
        if (a == MotionEvent.ACTION_UP || a == MotionEvent.ACTION_POINTER_UP) drop(id);
        else {
            int m = e.findPointerIndex(move);
            if (m >= 0) { float dx = e.getX(m)-cx(), dy = e.getY(m)-cy(), dead = radius() * .25f;
                key(directions[0], dy < -dead); key(directions[1], dy > dead); key(directions[2], dx < -dead); key(directions[3], dx > dead); }
            int l = e.findPointerIndex(look);
            if (l >= 0 && a == MotionEvent.ACTION_MOVE) {
                float x = e.getX(l), y = e.getY(l);
                SDLActivity.sendRelativeMouseMotion(Math.round((x-lx)*.6f), Math.round((y-ly)*.6f)); lx=x; ly=y;
            }
        }
        syncRun();
        return true;
    }
}
