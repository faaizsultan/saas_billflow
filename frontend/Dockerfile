FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy project files
COPY . .

# Expose port 5173 for Vite
EXPOSE 5173

# Start Vite with host exposed
CMD ["npm", "run", "dev", "--", "--host"]
