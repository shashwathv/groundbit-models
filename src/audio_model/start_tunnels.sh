#!/bin/bash
# Script to create SSH tunnels for the private AWS RDS instances
# Uses ports 15432/15433 to avoid clash with local PostgreSQL on 5432

BASTION_IP="16.170.106.41"
USER="ubuntu"
KEY="$(dirname "$0")/agri.pem"

# Kill any existing tunnels first
pkill -f 'ssh.*agri.pem.*groundbit' 2>/dev/null
sleep 1

echo "Creating SSH Tunnels to AWS RDS Database..."
echo "  → Local 15432  =>  groundbit-db (MAIN DB)"
echo "  → Local 15433  =>  groundbit-audio (AUDIO DB)"
echo ""

ssh -i "$KEY" -N -f \
    -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=60 \
    -L 15432:groundbit-db.c7guey2eqdtb.eu-north-1.rds.amazonaws.com:5432 \
    -L 15433:groundbit-audio.c7guey2eqdtb.eu-north-1.rds.amazonaws.com:5432 \
    $USER@$BASTION_IP

if [ $? -eq 0 ]; then
    echo "✓ Tunnels are running in the background!"
    echo "  You can now start: python -m uvicorn api.main:app --host 0.0.0.0 --reload"
    echo "  To close tunnels:  pkill -f 'ssh.*agri.pem.*groundbit'"
else
    echo "✗ Failed to create tunnels. Check your SSH key and network."
    exit 1
fi
