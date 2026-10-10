FROM node:22-bookworm-slim
ENV MCP_CLIENT_DOCKER=true HOME=/home/node NODE_ENV=production
RUN apt-get update && apt-get install -y --no-install-recommends bash git python3 ca-certificates ripgrep && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /opt/dc /workspace/repo && chown node:node /workspace/repo
WORKDIR /opt/dc
RUN npm install --omit=dev --no-audit --no-fund --ignore-scripts @wonderwhy-er/desktop-commander@0.2.52 && npm rebuild @vscode/ripgrep
USER 1000:1000
WORKDIR /workspace/repo
CMD ["sleep", "infinity"]
