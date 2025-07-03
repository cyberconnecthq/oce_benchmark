# On Chain Execution Benchmark
```shell
# Download foundry installer `foundryup`
curl -L https://foundry.paradigm.xyz | bash
# Install forge, cast, anvil, chisel
foundryup
# Install the latest nightly release
foundryup -i nightly
```


anvil --fork-url 'https://rpc.ankr.com/eth/e1529327d27a49660f1b8b9e747aec94256fcd84c82bd3ae28ce178915e00017' --fork-block-number '22636495' --balance 1000

docker run -it --rm -p 8000:8000 -p 8545:8545 --env-file .env oce-benchmark-app:latest
docker build -t oce-benchmark-app -f app/Dockerfile .


anvil --fork-url 'https://base-mainnet.public.blastapi.io'  --balance 1000 --port 8546