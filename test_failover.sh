#!/bin/bash

echo "Testing Blue/Green Failover..."

# Test initial state (should be Blue)
echo "1. Testing initial state (should be Blue):"
for i in {1..5}; do
    curl -s http://localhost:8080/version | grep -o '"pool":"[^"]*"'
done

# Induce chaos on Blue
echo -e "\n2. Inducing chaos on Blue..."
curl -X POST http://localhost:8081/chaos/start?mode=error

# Test failover (should switch to Green)
echo -e "\n3. Testing failover (should be Green):"
for i in {1..10}; do
    response=$(curl -s -w "%{http_code}" http://localhost:8080/version)
    http_code=${response: -3}
    body=${response%???}
    
    echo "Request $i: HTTP $http_code"
    echo "$body" | grep -o '"pool":"[^"]*"'
    sleep 1
done

# Stop chaos
echo -e "\n4. Stopping chaos..."
curl -X POST http://localhost:8081/chaos/stop

echo "Test completed!"
