# Multi-stage build for production
FROM node:18.17.1-alpine AS base
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY volview-insight/package*.json ./volview-insight/
COPY core/VolView/package*.json ./core/VolView/

# Install dependencies
RUN npm ci --only=production

FROM node:18.17.1-alpine AS build
WORKDIR /app

# Copy everything
COPY . .

# Install all dependencies
RUN npm install --force
RUN cd volview-insight && npm install
RUN cd core/VolView && npm install

# Build the application
RUN npm run setup-project
RUN npm run build

FROM nginx:alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]