# Fase de pruebas: docker build --target test frontend
FROM node:24-alpine AS dependencies
WORKDIR /app
COPY package*.json ./
# El bloqueo se generó en macOS; npm instala aquí los binarios opcionales de Linux.
RUN npm install

FROM dependencies AS test
COPY . .
RUN npm test && npm run build

FROM dependencies AS build
COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime
RUN apk add --no-cache openssl
COPY nginx.conf /etc/nginx/templates/dashboard.conf
COPY nginx.auth.conf /etc/nginx/templates/dashboard.auth.conf
COPY docker-entrypoint.sh /docker-entrypoint.d/40-configure-auth.sh
COPY --from=build /backend/static /usr/share/nginx/html
EXPOSE 8080
