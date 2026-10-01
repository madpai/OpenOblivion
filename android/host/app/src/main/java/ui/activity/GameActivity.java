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
            Os.setenv("OPENMW_USER_FILE_STORAGE", new File(getFilesDir(), "preview-user").getPath() + "/", true);
        } catch (android.system.ErrnoException e) { throw new RuntimeException(e); }
        for (String lib : new String[]{"c++_shared", "openal", "SDL2", "GL", "collada-dom2.5-dp", "openmw"}) System.loadLibrary(lib);
        getPathToJni(getFilesDir().getParent(), new File(getFilesDir(), "preview-user").getPath());
    }
    @Override protected String getMainSharedObject() { return getApplicationInfo().nativeLibraryDir + "/libopenmw.so"; }
    @Override protected String[] getArguments() {
        String cell = getIntent().getStringExtra("cell");
        if (!"VilverinExterior".equals(cell)) cell = "Vilverin";
        return new String[]{"--resources", new File(getFilesDir(), "payload/resources").getPath(),
            "--config", new File(getFilesDir(), "preview-user/config").getPath(), "--skip-menu", "--no-sound", "--start", cell};
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        if (mBrokenLibraries || mLayout == null) return;
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        controls = new TouchControls(this);
        mLayout.addView(controls, new ViewGroup.LayoutParams(-1, -1));
    }
    @Override protected void onPause() { if (controls != null) controls.release(); super.onPause(); }
    @Override public void onWindowFocusChanged(boolean focus) { if (!focus && controls != null) controls.release(); super.onWindowFocusChanged(focus); }
    @Override public void onBackPressed() { finish(); }
    @Override protected void onDestroy() { if (controls != null) controls.release(); super.onDestroy(); android.os.Process.killProcess(android.os.Process.myPid()); }
}
