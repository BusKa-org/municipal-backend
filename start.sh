#!/bin/bash
# Complete setup and run script for Buska Backend with Docker

set -e

echo "Buska Backend - Complete Setup & Run"
echo "========================================="
echo ""

# Check if Ansible is installed
if ! command -v ansible-playbook &> /dev/null; then
    echo "Installing Ansible..."
    pip install ansible --quiet
fi

# Step 1: Setup (venv + dependencies + database)
echo "Step 1: Setting up development environment..."
echo "By default, existing database will be preserved."
echo "To reinitialize database: run with -e clean_database=true"
echo ""
ansible-playbook -i ansible/hosts.ini ansible/setup-dev.yml "$@"

echo ""
echo "Development environment ready!"
echo ""

# Step 2: Run with Docker
echo "Step 2: Building and running Docker containers..."
echo ""
ansible-playbook -i ansible/hosts.ini ansible/run-docker.yml

echo ""
echo "========================================="
echo "Buska Backend is ready!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env.prod with your credentials if needed"
echo "2. Access the API at: http://localhost:5001/apidocs"
echo "3. View logs: docker compose -f docker-compose.prod.yml logs -f"
echo ""
