#!/bin/bash
set -e

# 1. Write systemd override to expose Ollama on all interfaces
mkdir -p /etc/systemd/system/ollama.service.d
cat > /etc/systemd/system/ollama.service.d/override.conf << 'CONF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
CONF

echo "Override file written:"
cat /etc/systemd/system/ollama.service.d/override.conf

# 2. Reload and restart
systemctl daemon-reload
systemctl restart ollama
sleep 5

# 3. Confirm it's listening on 0.0.0.0
echo
echo "Listening ports:"
ss -tlnp | grep 11434

echo
echo "Ollama status:"
systemctl status ollama --no-pager | head -10

# 4. Pull gemma3:4b (fits in 15GB T4 easily)
echo
echo "Pulling gemma3:4b ..."
ollama pull gemma3:4b

echo
echo "Done! Models available:"
ollama list
