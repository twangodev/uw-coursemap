FROM node:24-alpine AS builder

WORKDIR /app

# Install git for version generation
RUN apk add --no-cache git

COPY package*.json .

RUN npm ci
COPY . .

RUN npm run build
RUN npm prune --production

FROM node:24-alpine AS runtime

WORKDIR /app

COPY --from=builder /app/build build/
COPY --from=builder /app/node_modules node_modules/

COPY package.json .

EXPOSE 3000

ENV NODE_ENV=production

CMD [ "node", "build" ]