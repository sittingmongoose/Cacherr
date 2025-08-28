FROM mcr.microsoft.com/playwright:v1.47.0-jammy

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy test files
COPY . .

# Install browsers (already included in the base image, but ensure they're available)
RUN npx playwright install --with-deps

# Set default command
CMD ["npx", "playwright", "test"]
