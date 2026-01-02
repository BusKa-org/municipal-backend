#!/bin/bash
# Setup script para instalar Ansible e executar playbooks locais

set -e

echo "Installing Ansible..."
pip install ansible

echo "Running setup playbook..."
echo ""
echo "By default, this will NOT delete existing database."
echo "To reinitialize the database, run with: ./setup.sh -e clean_database=true"
echo ""

ansible-playbook -i ansible/hosts.ini ansible/setup-dev.yml "$@"

echo "Setup completed!"
echo ""
echo "Next steps:"
echo "1. Make sure Docker Desktop is running"
echo "2. Run: source .venv/bin/activate"
echo "3. Run: make run"
