#!/bin/bash
# Setup script para instalar dependências e preparar ambiente local

set -e

# Check if Ansible is installed
if ! command -v ansible-playbook &> /dev/null; then
    echo "Installing Ansible..."
    pip install ansible --quiet
fi

echo "Running setup playbook..."
echo ""
echo "By default, this will NOT delete existing database."
echo "To reinitialize the database, run with: ./setup.sh -e clean_database=true"
echo ""

ansible-playbook -i ansible/hosts.ini ansible/setup-dev.yml "$@"

echo "Next steps:"
echo "1. Activate virtual environment:"
echo "   source .venv/bin/activate"
echo ""
echo "2. Option A - Run locally with Flask:"
echo "   make run"
echo ""
echo "3. Option B - Run with Docker:"
echo "   docker-compose -f docker-compose.prod.yml up"
echo ""
