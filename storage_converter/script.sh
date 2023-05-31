#!/bin/bash
source ../env.sh
envsubst < convert.yaml | kubectl apply -n $NAME_SPACE -f -
echo "Run the following commands:
cp -r /mnt/chain_data /mnt/chain_data_bak
mv /mnt/chain_data ./old_chain_data
./storage_rocksdb run -c config_rocksdb.toml &
./storage_opendal run -c config_opendal.toml &
./converter 50003 60003
chown -R 1000:1000 chain_data/
mv ./chain_data /mnt/chain_data
exit"
sleep 10
kubectl exec -it ${CHAIN_NAME}-converter -n $NAME_SPACE -- bash
#kubectl delete -f convert.yaml -n $NAME_SPACE
