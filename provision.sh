#!/bin/bash
set -e
DOCKER_GW=$(ip addr show docker0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1)


if ! iptables --wait -t nat -i docker0 -p tcp --dport 80 --destination 169.254.169.254 --jump DNAT --to-destination "${DOCKER_GW}":45001 -C PREROUTING 2> /dev/null; then
  echo "creating ip tables rule ..."
  /sbin/iptables --wait -t nat \
      -A PREROUTING \
      -i docker0 \
      -p tcp \
      --dport 80 \
      --destination 169.254.169.254 \
      --jump DNAT \
      --to-destination "${DOCKER_GW}":45001
fi
