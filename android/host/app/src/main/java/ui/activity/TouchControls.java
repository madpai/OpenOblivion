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
    private static final int INV = 8, MENU = 9, JOURNAL = 10, WAIT = 11, POV = 12, MORE = 13;
    private static final int SDL_LEFT = 1, SDL_RIGHT = 3;
    // Two columns, top to bottom. Hidden until MORE is open, so the right side stays a look surface.
    private static final int[] EXTRA = {RUN, SNEAK, WEAPON, MAGIC, INV, JOURNAL, WAIT, POV, MENU, EXIT};

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
    private boolean moreOpen;
    private boolean guiMode;
    private int guiPointer = -1;
    private float guiX, guiY;
    private final int[] directions = {KeyEvent.KEYCODE_W, KeyEvent.KEYCODE_S, KeyEvent.KEYCODE_A, KeyEvent.KEYCODE_D};

    TouchControls(GameActivity a) { super(a); activity = a; setFocusable(false); }
    // Menu taps are view pixels; the engine renders at the launcher's logical
    // resolution. Unscaled taps beyond it clamp to the bottom-right window corner.
    private static float gx(float x) { return SDLActivity.scaleAbsoluteMouseX(x); }
    private static float gy(float y) { return SDLActivity.scaleAbsoluteMouseY(y); }
    // The overlay hides while the engine shows its cursor (menus, loading). Poll
    // that state so the buttons return without waiting for a touch.
    private final Runnable watchCursor = new Runnable() {
        @Override public void run() {
            boolean gui = SDLActivity.isMouseShown() != 0;
            if (gui != guiMode) { release(); guiMode = gui; moreOpen = false; if (!gui) syncRun(); invalidate(); }
            postDelayed(this, 250);
        }
    };
    @Override protected void onAttachedToWindow() { super.onAttachedToWindow(); post(watchCursor); }
    @Override protected void onDetachedFromWindow() { removeCallbacks(watchCursor); super.onDetachedFromWindow(); }
    private float radius() { return Math.min(getWidth(), getHeight()) * .16f; }
    private float cx() { return radius() * 1.4f; }
    private float cy() { return getHeight() - radius() * 1.4f; }
    // Square edge cluster. 48px is the floor; the height cap keeps four buttons on a short screen.
    private float side() {
        float s = Math.min(getWidth(), getHeight()) * .105f;
        float cap = getHeight() * .14f;
        if (s > cap) s = cap;
        if (s < 48f) s = 48f;
        return s;
    }
    private float gap() { return Math.max(6f, side() * .16f); }
    // Leaves the engine compass/minimap visible under USE. Not a gameplay constant.
    private float bottomGap() { return getHeight() * .13f; }

    @Override protected void onDraw(Canvas c) {
        if (guiMode) return;
        float r = radius(); paint.setColor(0x55777777); c.drawCircle(cx(), cy(), r, paint);
        paint.setColor(Color.WHITE); paint.setTextSize(Math.max(16, getHeight() * .035f));
        c.drawText("MOVE", cx() - r * .42f, cy() + 8, paint);
        // Above the stick, not the top center. The engine name label sits there
        // (the Bandit caption in the published stair shot).
        paint.setTextSize(Math.max(14, getHeight() * .028f));
        c.drawText("Drag empty space to look", cx() - r, cy() - r - 8, paint);
        button(c, "USE", primaryRect(0), false);
        button(c, "JUMP", primaryRect(1), false);
        button(c, "ATK", primaryRect(2), mouseDown.contains(SDL_LEFT));
        button(c, moreOpen ? "CLOSE" : "MORE", primaryRect(3), moreOpen);
        if (!moreOpen) return;
        for (int i = 0; i < EXTRA.length; i++) button(c, label(EXTRA[i]), extraRect(i), highlighted(EXTRA[i]));
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

    private boolean highlighted(int i) {
        return (i == RUN && running) || (i == SNEAK && sneaking) || (i == ATK && mouseDown.contains(SDL_LEFT));
    }

    // slot 0 is the bottom button. USE, JUMP, ATK, MORE.
    private RectF primaryRect(int slotFromBottom) {
        float s = side(), g = gap();
        float right = getWidth() - g;
        float bottom = getHeight() - bottomGap() - s - slotFromBottom * (s + g);
        return new RectF(right - s, bottom, right, bottom + s);
    }

    private RectF extraRect(int index) {
        float s = side(), g = gap();
        int row = index / 2, col = index % 2;
        float right = primaryRect(0).left - g - (1 - col) * (s + g);
        // Row 4 lines up with USE. Earlier rows step up the screen (smaller y).
        float top = primaryRect(0).top - (4 - row) * (s + g);
        return new RectF(right - s, top, right, top + s);
    }

    private void button(Canvas c, String label, RectF b, boolean on) {
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
        if (primaryRect(3).contains(x, y)) return MORE;
        if (primaryRect(2).contains(x, y)) return ATK;
        if (primaryRect(1).contains(x, y)) return JUMP;
        if (primaryRect(0).contains(x, y)) return USE;
        if (!moreOpen) return -1;
        for (int i = 0; i < EXTRA.length; i++) if (extraRect(i).contains(x, y)) return EXTRA[i];
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
        // Always-run is on (overlay run gate), so Shift is held only to walk.
        if (!running) SDLActivity.onNativeKeyDown(KeyEvent.KEYCODE_SHIFT_LEFT);
        else if (shiftSent) SDLActivity.onNativeKeyUp(KeyEvent.KEYCODE_SHIFT_LEFT);
        shiftSent = !running;
        // Sneak holds Left Ctrl the same way run holds Shift. GameActivity calls syncRun() on focus.
        if (sneaking) SDLActivity.onNativeKeyDown(KeyEvent.KEYCODE_CTRL_LEFT);
        else if (ctrlSent) SDLActivity.onNativeKeyUp(KeyEvent.KEYCODE_CTRL_LEFT);
        ctrlSent = sneaking;
    }

    void release() {
        if (guiPointer != -1) SDLActivity.onNativeMouse(SDL_LEFT, MotionEvent.ACTION_UP, gx(guiX), gy(guiY), false);
        guiPointer = -1;
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
        boolean gui = SDLActivity.isMouseShown() != 0;
        if (gui != guiMode) { release(); guiMode = gui; moreOpen = false; invalidate(); }
        if (gui) {
            if (a == MotionEvent.ACTION_CANCEL) { release(); return true; }
            if (a == MotionEvent.ACTION_DOWN && guiPointer == -1) {
                guiPointer = id; guiX = e.getX(ix); guiY = e.getY(ix);
                SDLActivity.onNativeMouse(SDL_LEFT, MotionEvent.ACTION_DOWN, gx(guiX), gy(guiY), false);
            } else if (a == MotionEvent.ACTION_MOVE) {
                int pointer = e.findPointerIndex(guiPointer);
                if (pointer >= 0) {
                    guiX = e.getX(pointer); guiY = e.getY(pointer);
                    SDLActivity.onNativeMouse(SDL_LEFT, MotionEvent.ACTION_MOVE, gx(guiX), gy(guiY), false);
                }
            } else if ((a == MotionEvent.ACTION_UP || a == MotionEvent.ACTION_POINTER_UP) && id == guiPointer) {
                guiX = e.getX(ix); guiY = e.getY(ix);
                SDLActivity.onNativeMouse(SDL_LEFT, MotionEvent.ACTION_UP, gx(guiX), gy(guiY), false);
                guiPointer = -1;
            }
            return true;
        }
        if (a == MotionEvent.ACTION_CANCEL) { release(); return true; }
        if (a == MotionEvent.ACTION_DOWN || a == MotionEvent.ACTION_POINTER_DOWN) {
            float x = e.getX(ix), y = e.getY(ix);
            int c = controlAt(x, y);
            if (c == MORE) { moreOpen = !moreOpen; invalidate(); }
            else if (c == EXIT) { release(); activity.finish(); return true; }
            else if (c == RUN) { running = !running; syncRun(); invalidate(); }
            else if (c == SNEAK) { sneaking = !sneaking; syncRun(); invalidate(); }
            else if (c >= 0) { take(id, c); if (moreOpen) { moreOpen = false; invalidate(); } }
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
