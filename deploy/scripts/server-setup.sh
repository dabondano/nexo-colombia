#!/usr/bin/env bash
# One-time setup of a fresh Ubuntu 24.04 (Arm) server on Oracle Cloud.
# Installs Docker, opens ports 80 and 443 in the host firewall and adds swap.
# Run as the default "ubuntu" user: bash deploy/scripts/server-setup.sh
set -euo pipefail

sudo apt-get update
sudo apt-get install -y ca-certificates curl git netfilter-persistent iptables-persistent

# Docker Engine and the Compose plugin, from Docker's repository.
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
# shellcheck disable=SC1091
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" |
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"

# Oracle's Ubuntu images reject everything but SSH in iptables, even when the
# cloud security list allows it. Open HTTP and HTTPS (TCP, and UDP for HTTP/3).
for rule in "-p tcp --dport 80" "-p tcp --dport 443" "-p udp --dport 443"; do
  # shellcheck disable=SC2086
  sudo iptables -C INPUT -m state --state NEW $rule -j ACCEPT 2>/dev/null ||
    sudo iptables -I INPUT 6 -m state --state NEW $rule -j ACCEPT
done
sudo netfilter-persistent save

# 2 GB of swap, as a cushion for image builds.
if ! swapon --show | grep -q /swapfile; then
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# Automatic security updates.
sudo apt-get install -y unattended-upgrades
sudo dpkg-reconfigure -f noninteractive unattended-upgrades

echo "Done. Log out and back in so the docker group applies, then follow the guide."
