#!/bin/bash

public_peer_hostname="$(cat /etc/hostname)"
public_peer_ip="$(ifconfig ens192 | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1')"
rm -rf /var/lib/etcd/member/
mkdir -p /etc/systemd/system/etcd.service.d/

cat > "/etc/systemd/system/etcd.service.d/etcd.env" <<EOF

ETCD_INITIAL_CLUSTER="coreos-1=https://10.100.130.111:2380,coreos-2=https://10.100.130.112:2380,coreos-3=https://10.100.130.113:2380"
ETCD_NAME="$public_peer_hostname"
ETCD_INITIAL_CLUSTER_STATE="new"
ETCD_INITIAL_CLUSTER_TOKEN="etcd-cluster-1"

ETCD_ADVERTISE_CLIENT_URLS="https://$public_peer_hostname:2379"
ETCD_ADVERTISE_PEER_URLS="https://$public_peer_hostname:2380"
ETCD_INITIAL_ADVERTISE_PEER_URLS="https://$public_peer_hostname:2380"

ETCD_LISTEN_CLIENT_URLS="https://$public_peer_ip:2379,https://127.0.1.1:2379"
ETCD_CLIENT_CERT_AUTH="true"
ETCD_CERT_FILE="/var/lib/etcd/ssl/etcd-node.pem"
ETCD_KEY_FILE="/var/lib/etcd/ssl/etcd-node-key.pem"
ETCD_TRUSTED_CA_FILE="/var/lib/etcd/ssl/ca.pem"

ETCD_LISTEN_PEER_URLS="https://$public_peer_ip:2380"
ETCD_PEER_CLIENT_CERT_AUTH=true
ETCD_PEER_CERT_FILE="/var/lib/etcd/ssl/etcd-node.pem"
ETCD_PEER_KEY_FILE="/var/lib/etcd/ssl/etcd-node-key.pem"
ETCD_PEER_TRUSTED_CA_FILE="/var/lib/etcd/ssl/ca.pem"


ETCD_HEARTBEAT_INTERVAL=800
ETCD_ELECTION_TIMEOUT=4000
ETCD_IMAGE_TAG=v3.3.12
ETCD_NAME=%m
ETCD_USER=etcd
ETCD_DATA_DIR=/var/lib/etcd
ETCD_WAL_DIR=/var/lib/etcd

RKT_RUN_ARGS=--uuid-file-save=/var/lib/coreos/etcd-member-wrapper.uuid
EOF


# systemctl daemon-reload
# systemctl enable etcd-member
# systemctl start etcd-member
# systemctl status etcd-member
# etcdctl --key-file /var/lib/etcd/ssl/etcd-node-key.pem --cert-file /var/lib/etcd/ssl/etcd-node.pem --ca-file /var/lib/etcd/ssl/ca.pem --endpoints https://coreos-3.mkoyan.local:2379 cluster-health


exit 0


export NODE1=10.100.130.111
export NODE2=10.100.130.112
export NODE3=10.100.130.113
