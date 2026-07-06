FROM node:22-bookworm-slim

WORKDIR /app/frontend

RUN apt-get update \
  && apt-get install -y --no-install-recommends python3 python3-pip git ca-certificates \
  && rm -rf /var/lib/apt/lists/*

RUN npm install -g @openai/codex

COPY frontend/package*.json ./
RUN npm install

COPY . /app

WORKDIR /app/frontend
RUN npm run build

ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

EXPOSE 3000

CMD ["npm", "run", "start"]
