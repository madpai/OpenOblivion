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
import java.net.HttpURLConnection;
import java.net.URL;
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
    private boolean installedData;

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
        addScene(buttons, "Sewer exit (game start)", "ICPrisonSewerExit01");
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
        ScrollView page = new ScrollView(this); page.setFillViewport(true); page.addView(layout);
        setContentView(page);
        preparing = true;
        getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        new Thread(() -> {
            try {
                prepare();
                runOnUiThread(() -> { preparing = false; status.setText(installedData
                        ? "Complete installed assets ready. Choose a location to start. Gameplay parity remains in development."
                        : "Bundled scene assets ready. Choose a location to start.");
                    progress.setProgress(100); for (Button b : launches) b.setEnabled(true);
                    getWindow().clearFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON); });
            } catch (Exception e) {
                Log.e("OpenOblivion", "Asset preparation failed", e);
                runOnUiThread(() -> { preparing = false; status.setText("Preparation failed: " + e.getMessage() + "\nClose and reopen to retry; finished downloads are kept.");
                    getWindow().clearFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON); });
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
        installedData = "installed-data".equals(manifest.optString("content_scope"));
        String id = manifest.getString("id");
        File root = new File(getFilesDir(), "payload"); root.mkdirs();
        File ready = new File(root, ".ready");
        if (ready.isFile() && read(ready).equals(id)) { configure(root); return; }
        List<String> parts = new ArrayList<>();
        Map<String, JSONObject> partInfo = new HashMap<>();
        if (manifest.getInt("schema") == 2) {
            JSONArray packaged = manifest.getJSONArray("parts");
            for (int i = 0; i < packaged.length(); ++i) {
                String name = packaged.getJSONObject(i).getString("asset");
                if (!name.matches("payload-[0-9]{3}\\.zip") || parts.contains(name))
                    throw new IOException("Invalid payload part name");
                parts.add(name); partInfo.put(name, packaged.getJSONObject(i));
            }
        } else if (manifest.getInt("schema") == 1) parts.add("payload.zip");
        else throw new IOException("Unsupported payload manifest");
        if (parts.isEmpty()) throw new IOException("No payload parts");
        String downloadBase = manifest.optString("download_base", "");
        if (!downloadBase.isEmpty() && !downloadBase.matches("http://100\\.[0-9.]+:[0-9]+/"))
            throw new IOException("Invalid private download address");
        File downloads = new File(getFilesDir(), "downloads"); downloads.mkdirs();
        // Check every installed split before writing any new payload files.
        // Parts missing from the APK are fetched when this build names a server.
        Set<String> remote = new HashSet<>();
        long largestRemote = 0;
        for (String part : parts) {
            try (InputStream in = getAssets().open(part)) { if (in.read() == -1) throw new IOException("Empty payload part"); }
            catch (IOException error) {
                if (downloadBase.isEmpty() || !partInfo.containsKey(part))
                    throw new IOException("Missing bundled assets. Install every APK in the complete package together.", error);
                remote.add(part); largestRemote = Math.max(largestRemote, partInfo.get(part).getLong("size"));
            }
        }
        // Files already unpacked by an interrupted run do not need space again.
        long present = 0;
        JSONArray listed = manifest.getJSONArray("files");
        for (int i = 0; i < listed.length(); ++i) {
            File file = new File(root, listed.getJSONObject(i).getString("path"));
            if (file.isFile() && file.length() == listed.getJSONObject(i).getLong("size")) present += file.length();
        }
        long needed = manifest.getLong("unpacked_bytes") - present + largestRemote + 256L * 1024 * 1024;
        if (new StatFs(root.getPath()).getAvailableBytes() < needed)
            throw new IOException("Not enough free storage: about " + (needed / 1000000000 + 1)
                + " GB more is needed. Free space, then reopen");
        Map<String, JSONObject> expected = new HashMap<>();
        JSONArray entries = manifest.getJSONArray("files");
        for (int i = 0; i < entries.length(); ++i) {
            JSONObject e = entries.getJSONObject(i); String name = e.getString("path");
            if (expected.put(name, e) != null) throw new IOException("Duplicate payload path");
        }
        Set<String> retained = new HashSet<>(expected.keySet());
        long done = 0, total = manifest.getLong("unpacked_bytes"), lastUpdate = 0;
        byte[] buffer = new byte[1024 * 1024];
        int partNumber = 0;
        for (String part : parts) {
        ++partNumber;
        File marker = new File(downloads, part + ".installed");
        File local = new File(downloads, part);
        if (remote.contains(part)) {
            String sha = partInfo.get(part).getString("sha256");
            // A part unpacked and verified by an interrupted earlier run is not fetched again.
            if (marker.isFile() && read(marker).equals(id + " " + sha)) continue;
            download(downloadBase + part, local, partInfo.get(part).getLong("size"), sha, partNumber, parts.size());
        }
        final int shown = partNumber;
        try (ZipInputStream zip = new ZipInputStream(new BufferedInputStream(remote.contains(part)
                ? new FileInputStream(local) : getAssets().open(part), buffer.length))) {
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
                            runOnUiThread(() -> { progress.setProgress(percent); status.setText("Installing assets (part " + shown + " of " + parts.size()
                                + "): " + percent + "% overall\nKeep this app open for the first installation."); });
                        }
                    }
                }
                if (size != e.getLong("size") || !hex(hash.digest()).equals(e.getString("sha256"))) { temp.delete(); throw new IOException("Asset verification failed: " + entry.getName()); }
                Files.move(temp.toPath(), dest.toPath(), java.nio.file.StandardCopyOption.REPLACE_EXISTING);
            }
        }
        if (remote.contains(part)) { write(marker, id + " " + partInfo.get(part).getString("sha256")); local.delete(); }
        }
        // Files from parts verified by an earlier interrupted run must still be present.
        for (Map.Entry<String, JSONObject> left : expected.entrySet()) {
            File file = new File(root, left.getKey());
            if (!file.isFile() || file.length() != left.getValue().getLong("size")) throw new IOException("Incomplete payload");
        }
        // Old loose scene extracts would override the complete BSA archives.
        // Remove obsolete files only after every replacement has verified.
        try (java.util.stream.Stream<java.nio.file.Path> old = Files.walk(root.toPath())) {
            for (java.nio.file.Path path : old.sorted(Comparator.reverseOrder()).toArray(java.nio.file.Path[]::new)) {
                if (path.equals(root.toPath())) continue;
                if (Files.isSymbolicLink(path)) throw new IOException("Invalid old payload link");
                String name = root.toPath().relativize(path).toString().replace(File.separatorChar, '/');
                if (Files.isDirectory(path)) {
                    try (java.util.stream.Stream<java.nio.file.Path> children = Files.list(path)) {
                        if (!children.findAny().isPresent()) Files.delete(path);
                    }
                } else if (!retained.contains(name)) Files.delete(path);
            }
        }
        configure(root);
        write(ready, id);
        File[] leftovers = downloads.listFiles();
        if (leftovers != null) for (File f : leftovers) f.delete();
    }
    /** Resumable download of one private payload part, verified before use. */
    private void download(String url, File dest, long size, String sha, int number, int count) throws Exception {
        byte[] buffer = new byte[1024 * 1024];
        int failures = 0, rejected = 0;
        while (true) {
            long have = dest.isFile() ? dest.length() : 0;
            if (have > size) { dest.delete(); have = 0; }
            if (have < size) {
                HttpURLConnection connection = null;
                try {
                    connection = (HttpURLConnection) new URL(url).openConnection();
                    connection.setConnectTimeout(15000); connection.setReadTimeout(60000);
                    if (have > 0) { connection.setRequestProperty("Range", "bytes=" + have + "-"); connection.setRequestProperty("If-Range", "\"" + sha + "\""); }
                    int code = connection.getResponseCode();
                    if (code != 200 && code != 206) throw new IOException("server answered HTTP " + code);
                    boolean append = have > 0 && code == 206;
                    if (!append) have = 0;
                    long lastUpdate = 0, startBytes = have, startTime = System.currentTimeMillis();
                    try (InputStream in = connection.getInputStream(); OutputStream out = new FileOutputStream(dest, append)) {
                        for (int n; (n = in.read(buffer)) != -1;) {
                            if (have + n > size) throw new IOException("download larger than expected");
                            out.write(buffer, 0, n); have += n; failures = 0;
                            if (System.currentTimeMillis() - lastUpdate > 500) {
                                lastUpdate = System.currentTimeMillis();
                                final long got = have; final double seconds = Math.max(1, lastUpdate - startTime) / 1000.0;
                                final double rate = (got - startBytes) / seconds / 1e6;
                                runOnUiThread(() -> { progress.setProgress((int) (got * 100 / size));
                                    status.setText(String.format(Locale.ROOT, "Downloading game data part %d of %d: %d of %d MB (%.1f MB/s)\n"
                                        + "Keep this app open and the phone connected to Tailscale. Interrupted downloads resume.",
                                        number, count, got / 1000000, size / 1000000, rate)); });
                            }
                        }
                    }
                } catch (IOException error) {
                    if (++failures > 40) throw new IOException("Download failed (" + error.getMessage() + "). Check Tailscale, then reopen", error);
                    final int attempt = failures;
                    runOnUiThread(() -> status.setText("Connection problem: " + error.getMessage() + "\nRetrying (" + attempt + ")…"));
                    Thread.sleep(Math.min(30000, 2000L * failures));
                    continue;
                } finally {
                    if (connection != null) connection.disconnect();
                }
            }
            if (dest.length() != size) continue;
            runOnUiThread(() -> status.setText("Verifying downloaded part " + number + " of " + count + "…"));
            MessageDigest hash = MessageDigest.getInstance("SHA-256");
            try (InputStream in = new FileInputStream(dest)) { for (int n; (n = in.read(buffer)) != -1;) hash.update(buffer, 0, n); }
            if (hex(hash.digest()).equals(sha)) return;
            dest.delete();
            if (++rejected >= 5) throw new IOException("Downloaded part " + number + " failed verification " + rejected
                + " times; the server may be serving damaged data. Try again later");
            final int count2 = rejected;
            runOnUiThread(() -> status.setText("Part " + number + " arrived damaged and was discarded; downloading it again (" + count2 + ")…"));
        }
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
        JSONObject manifest;
        try { manifest = new JSONObject(assetText("payload-manifest.json")); }
        catch (JSONException error) { throw new IOException("Invalid payload configuration", error); }
        StringBuilder gameConfig = new StringBuilder("content=Oblivion.esm\n");
        try {
            if (manifest.has("archives")) {
                gameConfig.setLength(0);
                JSONArray plugins = manifest.getJSONArray("plugins"), archives = manifest.getJSONArray("archives");
                for (int i = 0; i < plugins.length(); ++i) gameConfig.append("content=").append(configName(plugins.getString(i))).append('\n');
                for (int i = 0; i < archives.length(); ++i) gameConfig.append("fallback-archive=").append(configName(archives.getString(i))).append('\n');
            }
        } catch (JSONException error) { throw new IOException("Invalid installed content list", error); }
        File overlay = new File(getFilesDir(), "overlay");
        copyOverlay(overlay);
        String cfg = "replace=content\nreplace=fallback-archive\nresources=" + resourcePath
            + "\ndata=" + root + "/template\ndata=" + root + "/data\ndata=" + root + "/qa\ndata=" + overlay
            + "\ncontent=template.omwgame\n" + gameConfig
            + "content=phone_qa.omwscripts\ncontent=run_gate.omwscripts\ncontent=camera_repair.omwscripts\ncontent=look_name.omwscripts\ncontent=container.omwscripts\n"
            + (new File(overlay, "openoblivion_rules.omwaddon").isFile() ? "content=openoblivion_rules.omwaddon\n" : "")
            + "content=start_position.omwscripts\n"
            + (com.libopenmw.openmw.BuildConfig.NATIVE_GROUNDED_EYE ? "content=native_stair_qa.omwscripts\n" : "")
            + "encoding=win1252\n"
            ;
        write(new File(user, "openmw.cfg"), cfg);
        String settings = read(new File(root, "template-settings.cfg"));
        settings = settings.replace("[Models]", "[Models]\nload unsupported nif files = true");
        // Android's COLLADA loader rejects every .dae; the overlay carries an OSGT sky.
        if (new File(overlay, "meshes/sky_atmosphere.osgt").isFile())
            settings = settings.replace("meshes/sky_atmosphere.dae", "meshes/sky_atmosphere.osgt");
        settings += "\n[Video]\nresolution x = 960\nresolution y = 540\nfullscreen = true\nvsync = true\n"
            + "\n[Shadows]\nenable shadows = false\n\n[Water]\nshader = false\n\n[Camera]\nviewing distance = 4096\n"
            + "\n[Terrain]\ndistant terrain = false\n\n[Post Processing]\nenabled = false\n";
        write(new File(user, "settings.cfg"), settings);
    }
    /** Launcher scripts bundled in the APK; refreshed on every launch, independent of the payload. */
    private void copyOverlay(File overlay) throws IOException {
        String[] top = getAssets().list("overlay");
        if (top == null) return;
        for (String name : top) {
            String[] children = getAssets().list("overlay/" + name);
            if (children != null && children.length > 0) {
                for (String child : children) copyAsset("overlay/" + name + "/" + child, new File(overlay, name + "/" + child));
            } else copyAsset("overlay/" + name, new File(overlay, name));
        }
    }
    private void copyAsset(String path, File dest) throws IOException {
        dest.getParentFile().mkdirs();
        try (InputStream in = getAssets().open(path); OutputStream out = new FileOutputStream(dest)) {
            byte[] buffer = new byte[8192]; for (int n; (n = in.read(buffer)) != -1;) out.write(buffer, 0, n);
        }
    }
    private static String configName(String name) throws IOException {
        if (name.isEmpty() || name.contains("/") || name.contains("\\") || name.contains("\n")
                || name.contains("\r") || name.contains("=") || name.contains("\""))
            throw new IOException("Invalid content filename");
        return name;
    }
    @Override public void onBackPressed() { if (!preparing) super.onBackPressed(); }
}
