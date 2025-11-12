#!/bin/bash

echo "🛑 Stopping VolView Insight services..."

# Stop all services
docker-compose down

echo "✅ All services stopped!"
echo ""
echo "🧹 Optional cleanup commands:"
echo "   - Remove volumes: docker-compose down --volumes"
echo "   - Remove images: docker system prune -a"
echo "   - Clean everything: docker system prune -a --volumes"
echo ""
