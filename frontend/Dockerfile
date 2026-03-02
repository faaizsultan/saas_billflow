FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy project files
COPY . .


# For now, just build.
RUN npm run build

# We will mount the host or a docker volume to /app/dist so the files persist after build.
# This CMD just outputs a message and exits.
CMD ["echo", "Frontend build complete."]
