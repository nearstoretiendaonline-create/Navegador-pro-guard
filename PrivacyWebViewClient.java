package org.chromelite.anonymous;

import android.net.Uri;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.ByteArrayInputStream;
import java.util.HashSet;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Real network-level ad/tracker blocker + HTTPS enforcement for the
 * Kivy/Python build of Chrome-Lite Anonymous.
 *
 * WebViewClient is an abstract Android class, not an interface, so pyjnius
 * cannot subclass it directly from Python (PythonJavaClass only implements
 * interfaces). This small Java file is compiled straight into the APK by
 * buildozer (see buildozer.spec -> android.add_src), and Python only talks
 * to it through plain method calls: addBlockedDomain(), setEnabled(),
 * getBlockedCount(), isLoading(). All the per-request filtering runs here,
 * in Java, off the Python interpreter entirely -- fast and thread-safe.
 */
public class PrivacyWebViewClient extends WebViewClient {

    private final HashSet<String> blockedDomains = new HashSet<>();
    private final AtomicInteger blockedCount = new AtomicInteger(0);
    private volatile boolean enabled = true;
    private volatile boolean loading = false;

    /** Called once per domain from Python at startup, loading blocklist.txt. */
    public void addBlockedDomain(String domain) {
        if (domain != null && !domain.isEmpty()) {
            blockedDomains.add(domain.toLowerCase());
        }
    }

    public void setEnabled(boolean value) {
        this.enabled = value;
    }

    public boolean isEnabled() {
        return enabled;
    }

    public int getBlockedCount() {
        return blockedCount.get();
    }

    public void resetBlockedCount() {
        blockedCount.set(0);
    }

    public boolean isLoading() {
        return loading;
    }

    private boolean isBlocked(String host) {
        if (host == null) return false;
        String h = host.toLowerCase();
        while (true) {
            if (blockedDomains.contains(h)) return true;
            int dot = h.indexOf('.');
            if (dot < 0) return false;
            h = h.substring(dot + 1);
        }
    }

    /** HTTPS-Only: rewrite any http:// navigation to https:// before it loads. */
    @Override
    public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
        Uri url = request.getUrl();
        if ("http".equals(url.getScheme())) {
            Uri httpsUrl = url.buildUpon().scheme("https").build();
            view.loadUrl(httpsUrl.toString());
            return true;
        }
        return false;
    }

    /**
     * Runs for every sub-resource (scripts, images, iframes, beacons) before
     * it is fetched. Returning a blank response stops the request from ever
     * leaving the device.
     */
    @Override
    public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
        Uri url = request.getUrl();

        // Upgrade any leftover http:// sub-resource too (mixed content).
        if ("http".equals(url.getScheme())) {
            return new WebResourceResponse("text/plain", "UTF-8", new ByteArrayInputStream(new byte[0]));
        }

        if (enabled && isBlocked(url.getHost())) {
            blockedCount.incrementAndGet();
            return new WebResourceResponse("text/plain", "UTF-8", new ByteArrayInputStream(new byte[0]));
        }

        return null; // not blocked: let the engine fetch it normally
    }

    @Override
    public void onPageStarted(WebView view, String url, android.graphics.Bitmap favicon) {
        loading = true;
    }

    @Override
    public void onPageFinished(WebView view, String url) {
        loading = false;
    }
}
