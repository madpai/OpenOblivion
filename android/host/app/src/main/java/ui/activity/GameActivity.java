// SPDX-License-Identifier: GPL-3.0-only
package ui.activity;

import android.os.Bundle;
import android.system.Os;
import android.view.*;
import java.io.File;
import org.libsdl.app.SDLActivity;

/** Original host; this class name is required by the released native path JNI hook. */
public final class GameActivity extends SDLActivity {
    public static final Mode Companion = new Mode();
    public static final class Mode { public MouseMode getMouseMode() { return MouseMode.Hybrid; } }
    private TouchControls controls;
    private native void getPathToJni(String global, String user);
    @Override public void loadLibraries() {
        try {
            Os.setenv("OPENMW_GLES_VERSION", "2", true); Os.setenv("LIBGL_ES", "2", true);
            Os.setenv("OSG_VERTEX_BUFFER_HINT", "VBO", true);
            Os.setenv("OSG_THREADING", "SingleThreaded", true);
            if (com.libopenmw.openmw.BuildConfig.NATIVE_GROUNDED_EYE) {
                Os.setenv("OPENOBLIVION_GROUNDED_EYE", "1", true);
                Os.setenv("OPENOBLIVION_AUTHORED_COLLISION", "1", true);
                Os.setenv("OPENOBLIVION_ORIGINAL_BODY", "1", true);
                Os.setenv("OPENOBLIVION_TES4_MOVEMENT", "1", true);
                Os.setenv("OPENOBLIVION_TES4_AIRBORNE", "1", true);
                Os.setenv("OPENOBLIVION_TES4_PLAYER", "1", true);
                Os.setenv("OPENOBLIVION_TES4_TREES", "1", true);
                // A native crash on the game thread leaves a backtrace here; MainActivity shows it with the scene log.
                Os.setenv("OPENOBLIVION_CRASH_LOG", new File(getFilesDir(), "preview-user/config/openoblivion-crash.txt").getPath(), true);
            }
            Os.setenv("OPENMW_USER_FILE_STORAGE", new File(getFilesDir(), "preview-user").getPath() + "/", true);
        } catch (android.system.ErrnoException e) { throw new RuntimeException(e); }
        // Load libEGL's drivers before any native library: libGL (GL4ES) calls eglGetDisplay from its load-time
        // initialiser while the dynamic linker's lock is held, and the UI RenderThread may hold libEGL's driver-init
        // lock while it needs that linker lock (dlsym). Seen as a hang before the first frame on the emulator.
        android.opengl.EGL14.eglGetDisplay(android.opengl.EGL14.EGL_DEFAULT_DISPLAY);
        for (String lib : new String[]{"c++_shared", "openal", "SDL2", "GL", "collada-dom2.5-dp", "openmw"}) System.loadLibrary(lib);
        getPathToJni(getFilesDir().getParent(), new File(getFilesDir(), "preview-user").getPath());
    }
    @Override protected String getMainSharedObject() { return getApplicationInfo().nativeLibraryDir + "/libopenmw.so"; }
    @Override protected String[] getArguments() {
        String cell = getIntent().getStringExtra("cell");
        if (!"VilverinExterior".equals(cell) && !"ICPrisonSewerExit01".equals(cell)) cell = "Vilverin";
        return new String[]{"--resources", new File(getFilesDir(), "payload/resources").getPath(),
            "--config", new File(getFilesDir(), "preview-user/config").getPath(), "--skip-menu", "--start", cell};
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        if (mBrokenLibraries || mLayout == null) return;
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        controls = new TouchControls(this);
        mLayout.addView(controls, new ViewGroup.LayoutParams(-1, -1));
    }
    @Override protected void onPause() { if (controls != null) controls.release(); super.onPause(); }
    @Override public void onWindowFocusChanged(boolean focus) {
        if (controls != null) { if (focus) controls.syncRun(); else controls.release(); }
        super.onWindowFocusChanged(focus);
    }
    @Override public void onBackPressed() { if (controls != null && controls.closeMenu()) return; finish(); }
    private boolean backHandled;
    // SDLActivity hands the back key to the engine and consumes it, so onBackPressed never runs: close menus here.
    @Override public boolean dispatchKeyEvent(KeyEvent event) {
        if (event.getKeyCode() == KeyEvent.KEYCODE_BACK && controls != null) {
            if (event.getAction() == KeyEvent.ACTION_DOWN && event.getRepeatCount() == 0) backHandled = controls.closeMenu();
            if (backHandled) { if (event.getAction() == KeyEvent.ACTION_UP) backHandled = false; return true; }
        }
        return super.dispatchKeyEvent(event);
    }
    @Override protected void onDestroy() { if (controls != null) controls.release(); super.onDestroy(); android.os.Process.killProcess(android.os.Process.myPid()); }
}
