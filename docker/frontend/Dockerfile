# Production Dockerfile - Multi-stage build with nginx
FROM node:18.17.1-alpine AS base
WORKDIR /app

# Install build dependencies
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    cairo-dev \
    jpeg-dev \
    pango-dev \
    musl-dev \
    giflib-dev \
    pixman-dev \
    pangomm-dev \
    libjpeg-turbo-dev \
    freetype-dev \
    git

# Copy package files for dependency installation
COPY package*.json ./
COPY volview-insight/package*.json ./volview-insight/
COPY core/VolView/package*.json ./core/VolView/

# Install dependencies
RUN npm install --force
RUN cd volview-insight && npm install  
RUN cd core/VolView && npm install

# Build stage
FROM base AS build
WORKDIR /app

# Copy all source code
COPY . .

# Setup project and build for production
RUN npm run setup-project
RUN npm run build

# Production stage with nginx
FROM nginx:alpine AS production

# Copy built static files
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose nginx port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]