package com.shuvojamal.tradebot;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * Shows the dashboard page and keeps it up to date without new builds or GitHub
 * Actions. The repository is private, so the page updates itself: once it has
 * the owner's GitHub token it fetches dashboard/index.html through the GitHub
 * API and passes it to TradebotApp.update(), which, if it differs from what is
 * shown, saves it as the local copy and shows it. The
 * copy bundled in assets/index.html is used until the first update. (A direct
 * download from raw.githubusercontent.com is also tried; it works only while
 * the repository is public.)
 */
public class MainActivity extends Activity {
    private static final String PAGE = "https://raw.githubusercontent.com/shuvojamal/binancebot/main/dashboard/index.html";
    // A fixed https origin (never fetched) so the token saved in localStorage
    // stays the same whichever copy of the page is shown.
    private static final String BASE = "https://tradebot.invalid/";
    private WebView web;
    private String shown = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.parseColor("#f3f4fb"));
        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);      // the GitHub token is kept in localStorage on this phone
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
                Uri u = req.getUrl();
                if ("http".equals(u.getScheme()) || "https".equals(u.getScheme())) {
                    startActivity(new Intent(Intent.ACTION_VIEW, u));  // links open in the browser
                    return true;
                }
                return false;
            }
        });
        web.addJavascriptInterface(new Bridge(), "TradebotApp");
        setContentView(web);
        String cached = read(cacheFile());
        show(cached != null ? cached : asset());
        new Thread(this::refresh).start();
    }

    private void show(String html) {
        if (html == null || html.equals(shown)) return;
        shown = html;
        web.loadDataWithBaseURL(BASE, html, "text/html", "utf-8", null);
    }

    /** Called by the page with a newer copy of itself (fetched with the owner's token). */
    private class Bridge {
        @JavascriptInterface
        public void update(String html) {
            if (html == null || !html.contains("<html")) return;
            runOnUiThread(() -> {
                if (html.equals(shown)) return;
                save(html);
                show(html);
            });
        }
    }

    private void save(String html) {
        try (FileOutputStream out = new FileOutputStream(cacheFile())) {
            out.write(html.getBytes(StandardCharsets.UTF_8));
        } catch (Exception ignored) {
        }
    }

    /** Download the latest page (public repositories only); if it changed, save it and show it. */
    private void refresh() {
        try {
            HttpURLConnection c = (HttpURLConnection) new URL(PAGE + "?t=" + System.currentTimeMillis()).openConnection();
            c.setConnectTimeout(10000);
            c.setReadTimeout(15000);
            if (c.getResponseCode() != 200) return;
            String html = new String(readAll(c.getInputStream()), StandardCharsets.UTF_8);
            if (!html.contains("<html")) return;            // not the page (error page, captive portal)
            save(html);
            runOnUiThread(() -> show(html));
        } catch (Exception ignored) {
            // offline: keep the copy already shown
        }
    }

    private File cacheFile() { return new File(getFilesDir(), "index.html"); }

    private String asset() {
        try (InputStream in = getAssets().open("index.html")) {
            return new String(readAll(in), StandardCharsets.UTF_8);
        } catch (Exception e) {
            return "<html><body>Page missing</body></html>";
        }
    }

    private static String read(File f) {
        if (!f.exists()) return null;
        try (FileInputStream in = new FileInputStream(f)) {
            return new String(readAll(in), StandardCharsets.UTF_8);
        } catch (Exception e) {
            return null;
        }
    }

    private static byte[] readAll(InputStream in) throws java.io.IOException {
        ByteArrayOutputStream b = new ByteArrayOutputStream();
        byte[] buf = new byte[16384];
        int n;
        while ((n = in.read(buf)) > 0) b.write(buf, 0, n);
        return b.toByteArray();
    }

    @Override
    public void onBackPressed() {
        if (web != null && web.canGoBack()) web.goBack(); else super.onBackPressed();
    }
}
