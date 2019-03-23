#!/bin/bash

if [[ ! -d ./keys ]];then
    mkdir ./keys
    cd ./keys
fi
# Generate the CA private key.
openssl genrsa -out ca-key.pem 2048
# Generate the CA certificate.
sed -i 's/^CN.*/CN                 = mkoyan.local/g' ../cert.conf
openssl req -x509 -new -extensions v3_ca -key ca-key.pem -days 3650 \
-out ca.pem \
-subj '/C=AM/ST=Yervan/L=Yervan/O=mkoyan.local/CN=mkoyan.local' \
-config ../cert.conf

# Generate the server/client private key
openssl genrsa -out etcd-nodes-key.pem 2048
# Generate the server/client certificate request.
sed -i 's/^CN.*/CN                 = etcd-nodes/g' ../cert.conf
openssl req -new -key etcd-nodes-key.pem \
-newkey rsa:2048 -nodes -config ../cert.conf \
-subj '/C=AM/ST=Yervan/L=Yervan/O=mkoyan.local/CN=etcd-nodes' \
-outform pem -out etcd-nodes-req.pem -keyout etcd-nodes-req.key

# Sign the server/client certificate request.
openssl x509 -req -in etcd-nodes-req.pem -CA ca.pem -CAkey ca-key.pem -CAcreateserial \
-out etcd-nodes.pem -days 3650 -extensions v3_req -extfile ../cert.conf


# Generate the admin private key
openssl genrsa -out admin-key.pem 2048
# Generate the admin certificate request.
sed -i 's/^CN.*/CN                 = admin/g' ../cert.conf
openssl req -new -key admin-key.pem \
-newkey rsa:2048 -nodes -config ../cert.conf \
-subj '/C=AM/ST=Yervan/L=Yervan/O=mkoyan.local/CN=admin' \
-outform pem -out admin-req.pem -keyout admin-req.key
 
# Sign the server/client certificate request.
openssl x509 -req -in admin-req.pem -CA ca.pem -CAkey ca-key.pem -CAcreateserial \
-out admin.pem -days 3650 -extensions v3_req_admin -extfile ../cert.conf