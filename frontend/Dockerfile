# syntax=docker/dockerfile:1
# Sprint 0 walking-skeleton dev image. For production, switch to multi-stage
# (deps -> build -> runner with next.config "output: standalone").
FROM node:22-alpine

WORKDIR /app

# Install deps. We don't have a lockfile yet -> npm install (not npm ci).
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
