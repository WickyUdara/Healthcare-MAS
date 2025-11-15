FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build for production
RUN npm run build

# Install a simple HTTP server to serve the built app
RUN npm install -g serve

# Expose port
EXPOSE 5173

# Serve the app
CMD ["serve", "-s", "dist", "-l", "5173"]
