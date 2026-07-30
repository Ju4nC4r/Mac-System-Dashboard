# Fase de pruebas: docker build --target test frontend
FROM node:24-alpine AS dependencies
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM dependencies AS test
COPY . .
RUN npm test && npm run build

FROM dependencies AS build
COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /backend/static /usr/share/nginx/html
EXPOSE 8080
