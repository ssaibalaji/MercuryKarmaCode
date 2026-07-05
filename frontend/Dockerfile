# frontend/Dockerfile
# Multi-stage build for the Abhyas React + Vite frontend

# ---- Build stage ----
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# ---- Final stage: serve with nginx ----
FROM nginx:1.27-alpine AS final

# Run nginx as a non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup \
    && sed -i 's/user  nginx;//' /etc/nginx/nginx.conf \
    && touch /var/run/nginx.pid \
    && chown -R appuser:appgroup /var/run/nginx.pid /var/cache/nginx /usr/share/nginx/html /etc/nginx

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

USER appuser

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
