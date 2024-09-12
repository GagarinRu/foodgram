server {
    listen 80;
    server_tokens off;
    client_max_body_size 20M;

    location /api/docs/ {
        root /usr/share/nginx/html;
        try_files $uri $uri/redoc.html;
    }
    location /api/ {
        proxy_set_header Host $http_host;
        proxy_pass http://backend:8000/api/;
    }
    location /admin/ {
        proxy_set_header Host $http_host;
        proxy_pass http://backend:8000/admin/;
    }
    location /backend_static/ {
        alias /static/;
    }
    location /media/ {
        alias /app/;
    }
    location /s/ {
        proxy_set_header Host $http_host;
        proxy_pass http://backend:8000/s/;
    }
    location / {
        root /usr/share/nginx/html;
        index  index.html index.htm;
        try_files $uri /index.html;
    }
}