# Production Reverse Proxy Example

Below is a minimal Nginx `server` block that proxies traffic to the frontend container. It preserves the original host, forwards real client IPs, and supports WebSocket upgrades for Vite HMR in dev mode and SSE connections.

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name dashboard.xmrfts.local;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support — Vite HMR + SSE
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

> **Recommendation:** For production, terminate TLS with a valid SSL certificate (for example, via Let's Encrypt / Certbot) and redirect HTTP to HTTPS.

Production-grade configs with TLS 1.3, security headers, SSE support, and separate rate-limit zones are provided in the [docs repository](https://github.com/risubrevis/xmr-fund-transparency-suite-docs). For running multiple instances behind a single nginx, see [Multi-Instance Deployment](./multi-instance.md#nginx-for-multiple-instances).