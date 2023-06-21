#!/bin/bash
source ../env.sh
envsubst < convert.yaml | kubectl apply -n $NAME_SPACE -f -
echo "Run the following commands:
cp -r /mnt/chain_data /mnt/chain_data_bak
mv /mnt/chain_data ./old_chain_data
./storage_rocksdb run -c config_rocksdb.toml > rocksdb.log 2>&1 &
./storage_opendal run -c config_opendal.toml > opendal.log 2>&1 &
./converter 50003 60003
kill %1 %2
chown -R 1000:1000 chain_data/
mv ./chain_data /mnt/chain_data
exit"
sleep 10
kubectl exec -it ${CHAIN_NAME}-converter -n $NAME_SPACE -- bash
# envsubst < convert.yaml | kubectl delete -n $NAME_SPACE -f -
