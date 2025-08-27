# store-finder-api/Dockerfile

FROM node:lts
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Only one entry point
CMD ["npm", "start"]