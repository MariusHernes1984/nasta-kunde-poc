const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const PORT = process.env.PORT || 8080;
const BACKEND_URL = process.env.BACKEND_URL || 'https://func-nasta-poc.azurewebsites.net';
const DAB_URL = process.env.DAB_URL || 'https://ca-nasta-mcp.salmonsmoke-ae79c912.norwayeast.azurecontainerapps.io';

const MIME = {
  '.html': 'text/html', '.js': 'application/javascript',
  '.css': 'text/css', '.json': 'application/json',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon',
};

const STATIC_DIR = path.join(__dirname, 'dist');

http.createServer((req, res) => {
  // Proxy /dab/* to Data API Builder
  if (req.url.startsWith('/dab/')) {
    const targetPath = req.url.replace('/dab/', '/api/');
    const targetUrl = new URL(targetPath, DAB_URL);
    const options = {
      hostname: targetUrl.hostname, port: 443,
      path: targetUrl.pathname + targetUrl.search,
      method: req.method,
      headers: { ...req.headers, host: targetUrl.hostname },
    };
    const proxyReq = https.request(options, (proxyRes) => {
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      proxyRes.pipe(res);
    });
    proxyReq.on('error', (e) => {
      res.writeHead(502, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'DAB unavailable: ' + e.message }));
    });
    proxyReq.setTimeout(30000);
    req.pipe(proxyReq);
    return;
  }
  // Proxy /api/* to Azure Functions backend
  if (req.url.startsWith('/api/')) {
    const targetUrl = new URL(req.url, BACKEND_URL);
    const options = {
      hostname: targetUrl.hostname, port: 443,
      path: targetUrl.pathname + targetUrl.search,
      method: req.method,
      headers: { ...req.headers, host: targetUrl.hostname },
    };
    const proxyReq = https.request(options, (proxyRes) => {
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      proxyRes.pipe(res);
    });
    proxyReq.on('error', (e) => {
      res.writeHead(502, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Backend unavailable: ' + e.message }));
    });
    proxyReq.setTimeout(120000);
    req.pipe(proxyReq);
    return;
  }
  const urlPath = req.url.split('?')[0];
  let filePath = path.join(STATIC_DIR, urlPath === '/' ? 'index.html' : urlPath);
  if (!fs.existsSync(filePath)) filePath = path.join(STATIC_DIR, 'index.html');
  const ext = path.extname(filePath);
  res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
  fs.createReadStream(filePath).pipe(res);
}).listen(PORT, () => console.log('Serving on port ' + PORT));
