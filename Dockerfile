FROM node:25-alpine AS builder

WORKDIR /app

RUN apk add --no-cache git

COPY package*.json .

RUN npm ci
COPY . .

RUN npm run build
RUN npm prune --production

FROM node:25-alpine AS runtime

WORKDIR /app

RUN addgroup --system --gid 1001 svelte && \
    adduser --system --uid 1001 --ingroup svelte svelte

RUN apk add --no-cache curl

COPY --from=builder --chown=svelte:svelte /app/build build/
COPY --from=builder --chown=svelte:svelte /app/node_modules node_modules/
COPY --chown=svelte:svelte package.json .

USER svelte

EXPOSE 3000

ENV NODE_ENV=production

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD curl --fail --silent http://localhost:3000/ || exit 1

CMD [ "node", "build" ]