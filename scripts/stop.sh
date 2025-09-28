#!/bin/bash

echo "🛑 Stopping VolView Insight services..."

# Stop both dev and prod configurations
docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.prod.yml down

echo "✅ All services stopped!"
echo ""
echo "🧹 Optional cleanup commands:"
echo "   - Remove volumes: docker-compose down --volumes"
echo "   - Remove images: docker system prune -a"
echo "   - Clean everything: docker system prune -a --volumes"
echo ""
