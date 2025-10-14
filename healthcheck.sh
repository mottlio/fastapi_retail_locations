echo "=== Git Status ==="
git log -1 --oneline
echo ""
echo "=== Docker Image Build Time ==="
docker images gasapp:latest --format "{{.CreatedAt}}"
echo ""
echo "=== Service Tasks (most recent first) ==="
docker service ps gasapp_app --no-trunc | head -5
echo ""
echo "=== Code in Running Container ==="
docker exec $(docker ps -q -f name=gasapp_app) head -20 /app/app/main.py