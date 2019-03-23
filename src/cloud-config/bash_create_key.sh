#!/bin/bash
base_dir=$(cd `dirname $0` && pwd)

if [[ ! -d ./bin ]]; then
    wget -q --show-progress --https-only --timestamping \
        https://pkg.cfssl.org/R1.2/cfssl_linux-amd64 \
        https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
    mkdir ./bin
    mv cfssl_linux-amd64 ./bin/cfssl
    mv cfssljson_linux-amd64 ./bin/cfssljson
    chmod +x ./bin/cfssl 
    chmod +x ./bin/cfssljson
fi
CFSSL="$base_dir/bin/cfssl"
CFSSLJSON="$base_dir/bin/cfssljson"
if [[ ! -d ./keys ]]; then
    mkdir ./keys
    cd ./keys
else
    cd ./keys
fi


cat > ca-config.json <<EOF
{
  "signing": {
    "default": {
      "expiry": "8760h"
    },
    "profiles": {
      "kubernetes": {
        "usages": ["signing", "key encipherment", "server auth", "client auth"],
        "expiry": "8760h"
      }
    }
  }
}
EOF

# Admin Certificate
cat > ca-csr.json <<EOF
{
  "CN": "Kubernetes",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "AM",
      "L": "Yerevan",
      "O": "Kubernetes",
      "OU": "CA",
      "ST": "Yerevan"
    }
  ]
}
EOF

$CFSSL gencert -initca ca-csr.json | $CFSSLJSON -bare ca

# ADMIN certficiates

cat > admin-csr.json <<EOF
{
  "CN": "admin",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "AM",
      "L": "Yerevan",
      "O": "system:masters",
      "OU": "mkoyan",
      "ST": "Yerevan"
    }
  ]
}
EOF

$CFSSL gencert \
  -ca=ca.pem \
  -ca-key=ca-key.pem \
  -config=ca-config.json \
  -profile=kubernetes \
  admin-csr.json | $CFSSLJSON -bare admin


# WORKER Certficates
count=0
for instance in worker-0 worker-1 worker-2; do
  cat > ${instance}-csr.json <<EOF
  {
    "CN": "system:node:${instance}",
    "key": {
      "algo": "rsa",
      "size": 2048
    },
    "names": [
      {
        "C": "AM",
        "L": "Yerevan",
        "O": "system:nodes",
        "OU": "mkoyan",
        "ST": "Yerevan"
      }
    ]
  }
EOF

  INTERNAL_IP=`printf "10.100.130.20%d\n" "$count"`
  let count=count+1
  echo "$instance ----- $INTERNAL_IP"

  $CFSSL gencert \
    -ca=ca.pem \
    -ca-key=ca-key.pem \
    -config=ca-config.json \
    -hostname=${instance},${hostname}.mkoyan.local,${INTERNAL_IP} \
    -profile=kubernetes \
    ${instance}-csr.json | $CFSSLJSON -bare ${instance}

done

# kube-controller-manager, should match on OU,CN, valid on any ip and fqdn

cat > kube-controller-manager-csr.json <<EOF
{
  "CN": "system:kube-controller-manager",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "AM",
      "L": "Yerevan",
      "O": "system:kube-controller-manager",
      "OU": "mkoyan",
      "ST": "Yerevan"
    }
  ]
}
EOF

$CFSSL gencert \
  -ca=ca.pem \
  -ca-key=ca-key.pem \
  -config=ca-config.json \
  -profile=kubernetes \
  kube-controller-manager-csr.json | $CFSSLJSON -bare kube-controller-manager

# system:node-proxier (kubelet proxy), match on CN,OU

cat > kube-proxy-csr.json <<EOF
{
  "CN": "system:kube-proxy",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "AM",
      "L": "Yerevan",
      "O": "system:node-proxier",
      "OU": "mkoyan",
      "ST": "Yervan"
    }
  ]
}
EOF

$CFSSL gencert \
  -ca=ca.pem \
  -ca-key=ca-key.pem \
  -config=ca-config.json \
  -profile=kubernetes \
  kube-proxy-csr.json | $CFSSLJSON -bare kube-proxy


# kube scheduler, system:kube-scheduler

cat > kube-scheduler-csr.json <<EOF
{
  "CN": "system:kube-scheduler",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "AM",
      "L": "Yerevan",
      "O": "system:kube-scheduler",
      "OU": "mkoyan",
      "ST": "Yervan"
    }
  ]
}
EOF

$CFSSL gencert \
  -ca=ca.pem \
  -ca-key=ca-key.pem \
  -config=ca-config.json \
  -profile=kubernetes \
  kube-scheduler-csr.json | $CFSSLJSON -bare kube-scheduler


# kube-api server
cat > kubernetes-csr.json <<EOF
{
  "CN": "kubernetes",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "AM",
      "L": "Yerevan",
      "O": "Kubernetes",
      "OU": "mkoyan",
      "ST": "Yervan"
    }
  ]
}
EOF

$CFSSL gencert \
  -ca=ca.pem \
  -ca-key=ca-key.pem \
  -config=ca-config.json \
  -hostname="10.3.0.1,10.100.130.115,10.100.130.116,10.100.130.117,127.0.0.1,kubernetes,kubernetes.default,kubernetes.default.svc,kubernetes.default.svc.mkoyan,kubernetes.default.svc.mkoyan.local" \
  -profile=kubernetes \
  kubernetes-csr.json | $CFSSLJSON -bare kubernetes



# service account 

cat > service-account-csr.json <<EOF
{
  "CN": "service-accounts",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "AM",
      "L": "Yerevan",
      "O": "Kubernetes",
      "OU": "mkoyan",
      "ST": "Yervan"
    }
  ]
}
EOF

$CFSSL gencert \
  -ca=ca.pem \
  -ca-key=ca-key.pem \
  -config=ca-config.json \
  -profile=kubernetes \
  service-account-csr.json | $CFSSLJSON -bare service-account




# etcd 

cat > etcd-csr.json <<EOF
{
  "CN": "ETCD",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "AM",
      "L": "Yerevan",
      "O": "kubernetes",
      "OU": "mkoyan",
      "ST": "Yerevan"
    }
  ]
}
EOF
$CFSSL gencert \
  -ca=ca.pem \
  -ca-key=ca-key.pem \
  -config=ca-config.json \
  -hostname=10.100.130.111,10.100.130.112,10.100.130.113,127.0.0.1 \
  -profile=kubernetes \
  etcd-csr.json | $CFSSLJSON -bare etcd
