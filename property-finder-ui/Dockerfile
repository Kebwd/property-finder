FROM node:18-alpine
WORKDIR /usr/src/app

# Copy package files
COPY package*.json ./

# Debug: list files to ensure lockfile is present
RUN ls -la /usr/src/app

# Install dependencies
RUN npm ci

# Copy the rest of your source
COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]