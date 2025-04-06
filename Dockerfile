FROM node:23-alpine AS builder
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build
RUN npm prune --production

FROM node:23-alpine AS bruh
WORKDIR /app
COPY --from=builder /app/build build/
COPY --from=builder /app/node_modules node_modules/
COPY package.json .
EXPOSE 3000
ENV NODE_ENV=production
ENV PUBLIC_API_URL=https://raw.githubusercontent.com/twangodev/uw-coursemap-data/main
ENV PUBLIC_SEARCH_API_URL=http://127.0.0.1:5000

CMD [ "node", "build" ]