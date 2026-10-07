"""One local Deism origin for the static website and shared portal services."""
def site_config(site_port=8878):
    return '''events {}
http {
 include /etc/nginx/mime.types;
 default_type application/octet-stream;
 map $http_upgrade $connection_upgrade { default upgrade; '' close; }
 server {
  listen 8080;
  root /site;
  add_header Cache-Control "no-cache" always;
  proxy_http_version 1.1;
  proxy_set_header Host $http_host;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_set_header X-Forwarded-Host $http_host;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  location = /login { return 302 /users/login; }
  location = /services { return 302 /services/; }
  location ^~ /services/ {
   resolver 127.0.0.11 ipv6=off valid=10s;
   set $service_directory local-service-directory:8080;
   rewrite ^/services/(.*)$ /$1 break;
   proxy_pass http://$service_directory;
  }
  location /api/org/ {
   proxy_set_header X-Forwarded-Host portal.deism.church;
   rewrite ^/api/org/?(.*)$ /$1 break;
   proxy_pass http://deism-community-api:8001;
  }
  location /api/chat/ {
   rewrite ^/api/chat/?(.*)$ /$1 break;
   proxy_set_header Upgrade $http_upgrade;
   proxy_set_header Connection $connection_upgrade;
   proxy_read_timeout 1h;
   proxy_pass http://deism-chat-api:8003;
  }
  location /pidp/ {
   proxy_set_header Host $http_host;
   proxy_set_header X-Forwarded-Proto $scheme;
   proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
   rewrite ^/pidp/?(.*)$ /$1 break;
   proxy_set_header X-Forwarded-Host "";
   proxy_set_header X-Forwarded-Prefix /pidp;
   proxy_pass http://deism-identity-api:8000;
  }
  location / {
   error_page 418 = @portal;
   if ($http_upgrade != "") { return 418; }
   try_files $uri $uri.html $uri/ @portal;
  }
  location @portal {
   proxy_set_header Upgrade $http_upgrade;
   proxy_set_header Connection $connection_upgrade;
   proxy_buffering off;
   proxy_read_timeout 1h;
   proxy_pass http://deism-community-web:5173;
  }
 }
}
'''


def legacy_gateway_config(site_port=8878):
    return f'''events {{}}
http {{
 server {{
  listen 8443 ssl;
  ssl_certificate /certs/localhost.crt;
  ssl_certificate_key /certs/localhost.key;
  return 302 http://localhost:{site_port}$request_uri;
 }}
}}
'''
