# Development Dockerfile - Vite dev server only
FROM node:18.17.1-alpine
WORKDIR /app

# Install build dependencies for native modules and git
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

# Copy all source code first
COPY . .

# Install dependencies in correct order
RUN npm install --force
RUN cd volview-insight && npm install --force
RUN cd core/VolView && npm install --force

# Run setup (but don't build - we'll use dev server)
RUN npm run setup-project

# Expose Vite dev server port
EXPOSE 8080

# Start Vite dev server with hot reloading
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "8080"]