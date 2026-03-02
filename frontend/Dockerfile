FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy project files
COPY . .

# Pass VITE_API_URL if necessary for build, but typically dynamic paths are better. Wait, Vite expects VITE_API_URL at build time if it's baked into static files.
# However, usually we can use relative paths like '/api' in production. 
# Let's assume we can pass it or it defaults correctly. The frontend might have a fallback.
# For now, just build.
RUN npm run build

# We will mount the host or a docker volume to /app/dist so the files persist after build.
# This CMD just outputs a message and exits.
CMD ["echo", "Frontend build complete."]
