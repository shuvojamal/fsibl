package com.shuvojamal.tradebot;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
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
 * Shows the dashboard page. The page is downloaded from the repository when the
 * app opens (so dashboard changes need no new build and no GitHub Actions), kept
 * as a local copy for the next start or when offline, and the copy bundled in
 * assets/index.html is used only until the first download succeeds.
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

    /** Download the latest page; if it changed, save it and show it. */
    private void refresh() {
        try {
            HttpURLConnection c = (HttpURLConnection) new URL(PAGE + "?t=" + System.currentTimeMillis()).openConnection();
            c.setConnectTimeout(10000);
            c.setReadTimeout(15000);
            if (c.getResponseCode() != 200) return;
            String html = new String(readAll(c.getInputStream()), StandardCharsets.UTF_8);
            if (!html.contains("<html")) return;            // not the page (error page, captive portal)
            try (FileOutputStream out = new FileOutputStream(cacheFile())) {
                out.write(html.getBytes(StandardCharsets.UTF_8));
            }
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
