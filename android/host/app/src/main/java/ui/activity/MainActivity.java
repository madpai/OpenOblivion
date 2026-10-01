// SPDX-License-Identifier: GPL-3.0-only
package ui.activity;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.os.Bundle;
import android.os.StatFs;
import android.widget.*;
import android.util.Log;
import java.io.*;
import java.nio.file.Files;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.zip.*;
import org.json.*;

/** Original personal test launcher. No game files or donor payload in the source tree. */
public final class MainActivity extends Activity {
    public static final Resolution Companion = new Resolution();
    public static final class Resolution {
        public int getResolutionX() { return 960; }
        public int getResolutionY() { return 540; }
    }
    private TextView status;
    private ProgressBar progress;
    private final List<Button> launches = new ArrayList<>();
    private boolean preparing;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(32, 16, 32, 16);
        TextView title = new TextView(this);
        title.setText("OpenOblivion — personal scene preview"); title.setTextSize(24);
        layout.addView(title);
        TextView scope = new TextView(this);
        scope.setText("OpenMW Android 0.51 baseline · ARM64 · OpenGL ES\nWorld viewing and touch movement. Quests, combat and multiplayer are not implemented.\nLeft pad: move. Drag right: look. USE is the lower-right button. JUMP is above it. The top button switches run and walk, and starts on run. Exit: return here.");
        layout.addView(scope);
        status = new TextView(this); layout.addView(status);
        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setMax(100); layout.addView(progress);
        LinearLayout buttons = new LinearLayout(this); layout.addView(buttons);
        addScene(buttons, "Vilverin interior", "Vilverin");
        addScene(buttons, "Vilverin exterior", "VilverinExterior");
        Button logs = new Button(this); logs.setText("View scene log"); buttons.addView(logs);
        logs.setOnClickListener(v -> {
            File file = new File(getFilesDir(), "preview-user/config/openmw.log");
            String text = "No scene log yet. Launch a location first.";
            if (file.isFile()) try (RandomAccessFile in = new RandomAccessFile(file, "r")) {
                in.seek(Math.max(0, in.length()-96*1024)); byte[] bytes = new byte[(int)(in.length()-in.getFilePointer())];
                in.readFully(bytes); text = new String(bytes, StandardCharsets.UTF_8);
            } catch (IOException e) { text = "Cannot read log: " + e.getMessage(); }
            ScrollView scroll = new ScrollView(this); TextView view = new TextView(this);
            view.setText(text); view.setTextIsSelectable(true); view.setPadding(24, 16, 24, 16); scroll.addView(view);
            new AlertDialog.Builder(this).setTitle("Scene log").setView(scroll).setPositiveButton("Close", null).show();
        });
        setContentView(layout);
        preparing = true;
        new Thread(() -> {
            try {
                prepare();
                runOnUiThread(() -> { preparing = false; status.setText("Bundled scene assets ready. Choose a location to start.");
                    progress.setProgress(100); for (Button b : launches) b.setEnabled(true); });
            } catch (Exception e) {
                Log.e("OpenOblivion", "Asset preparation failed", e);
                runOnUiThread(() -> { preparing = false; status.setText("Preparation failed: " + e.getMessage() + "\nClose and reopen to retry."); });
            }
        }, "OpenOblivion-assets").start();
    }

    private void addScene(LinearLayout layout, String label, String cell) {
        Button b = new Button(this); b.setText(label); b.setEnabled(false); launches.add(b); layout.addView(b);
        b.setOnClickListener(v -> startActivity(new Intent(this, GameActivity.class).putExtra("cell", cell)));
    }
    private String assetText(String path) throws IOException {
        try (InputStream in = getAssets().open(path)) { ByteArrayOutputStream out = new ByteArrayOutputStream(); byte[] buf = new byte[8192]; for (int n; (n=in.read(buf))!=-1;) out.write(buf,0,n); return out.toString("UTF-8"); }
    }
    private static String hex(byte[] value) {
        StringBuilder s = new StringBuilder(); for (byte b : value) s.append(String.format(Locale.ROOT, "%02x", b & 255)); return s.toString();
    }
    private void prepare() throws Exception {
        JSONObject manifest = new JSONObject(assetText("payload-manifest.json"));
        String id = manifest.getString("id");
        File root = new File(getFilesDir(), "payload"); root.mkdirs();
        File ready = new File(root, ".ready");
        if (ready.isFile() && read(ready).equals(id)) { configure(root); return; }
        if (new StatFs(root.getPath()).getAvailableBytes() < manifest.getLong("unpacked_bytes") + 256L * 1024 * 1024)
            throw new IOException("Not enough free storage to unpack the bundled assets; free space, then reopen");
        Map<String, JSONObject> expected = new HashMap<>();
        JSONArray entries = manifest.getJSONArray("files");
        for (int i = 0; i < entries.length(); ++i) { JSONObject e = entries.getJSONObject(i); expected.put(e.getString("path"), e); }
        long done = 0, total = manifest.getLong("unpacked_bytes"), lastUpdate = 0;
        byte[] buffer = new byte[1024 * 1024];
        try (ZipInputStream zip = new ZipInputStream(new BufferedInputStream(getAssets().open("payload.zip"), buffer.length))) {
            for (ZipEntry entry; (entry = zip.getNextEntry()) != null;) {
                JSONObject e = expected.remove(entry.getName());
                if (e == null || entry.isDirectory()) throw new IOException("Unexpected payload entry");
                File dest = new File(root, entry.getName());
                if (!dest.getCanonicalPath().startsWith(root.getCanonicalPath() + File.separator)) throw new IOException("Invalid payload path");
                dest.getParentFile().mkdirs();
                File temp = new File(dest.getPath() + ".part");
                MessageDigest hash = MessageDigest.getInstance("SHA-256"); long size = 0;
                try (OutputStream out = new BufferedOutputStream(new FileOutputStream(temp), buffer.length)) {
                    for (int n; (n = zip.read(buffer)) != -1;) {
                        size += n; if (size > e.getLong("size")) throw new IOException("Payload size mismatch");
                        out.write(buffer, 0, n); hash.update(buffer, 0, n); done += n;
                        if (System.currentTimeMillis() - lastUpdate > 350) {
                            lastUpdate = System.currentTimeMillis(); final int percent = (int)(done * 100 / total);
                            runOnUiThread(() -> { progress.setProgress(percent); status.setText("Installing bundled assets: " + percent + "%\nKeep this app open for the first installation."); });
                        }
                    }
                }
                if (size != e.getLong("size") || !hex(hash.digest()).equals(e.getString("sha256"))) { temp.delete(); throw new IOException("Asset verification failed: " + entry.getName()); }
                Files.move(temp.toPath(), dest.toPath(), java.nio.file.StandardCopyOption.REPLACE_EXISTING);
            }
        }
        if (!expected.isEmpty()) throw new IOException("Incomplete payload");
        configure(root);
        write(ready, id);
    }
    private static String read(File f) throws IOException { return new String(Files.readAllBytes(f.toPath()), StandardCharsets.UTF_8); }
    private static void write(File f, String text) throws IOException { Files.write(f.toPath(), text.getBytes(StandardCharsets.UTF_8)); }
    private void configure(File root) throws IOException {
        File global = new File(getFilesDir(), "config"); global.mkdirs();
        File user = new File(getFilesDir(), "preview-user/config"); user.mkdirs();
        Files.copy(new File(root, "base/defaults.bin").toPath(), new File(global, "defaults.bin").toPath(), java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        String resourcePath = new File(root, "resources").getAbsolutePath();
        String base = read(new File(root, "base/openmw.base.cfg"));
        base = base.replace("resources=./resources", "resources=" + resourcePath).replace("data=./resources/vfs-mw", "data=" + resourcePath + "/vfs-mw");
        write(new File(global, "openmw.cfg"), base);
        String cfg = "replace=content\nreplace=fallback-archive\nresources=" + resourcePath
            + "\ndata=" + root + "/template\ndata=" + root + "/data\ndata=" + root + "/qa\ncontent=template.omwgame\ncontent=Oblivion.esm\ncontent=phone_qa.omwscripts\ncontent=run_gate.omwscripts\ncontent=camera_repair.omwscripts\ncontent=look_name.omwscripts\n"
            + (com.libopenmw.openmw.BuildConfig.NATIVE_GROUNDED_EYE ? "content=native_stair_qa.omwscripts\n" : "")
            + "encoding=win1252\n"
            ;
        write(new File(user, "openmw.cfg"), cfg);
        String settings = read(new File(root, "template-settings.cfg"));
        settings = settings.replace("[Models]", "[Models]\nload unsupported nif files = true");
        settings += "\n[Video]\nresolution x = 960\nresolution y = 540\nfullscreen = true\nvsync = true\n"
            + "\n[Shadows]\nenable shadows = false\n\n[Water]\nshader = false\n\n[Camera]\nviewing distance = 4096\n"
            + "\n[Terrain]\ndistant terrain = false\n\n[Post Processing]\nenabled = false\n"
            // Comfort scale for the 960x540 framebuffer. Not an Oblivion constant.
            + "\n[GUI]\nscaling factor = 1.25\nfont size = 20\n";
        write(new File(user, "settings.cfg"), settings);
    }
    @Override public void onBackPressed() { if (!preparing) super.onBackPressed(); }
}
