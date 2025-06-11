



1. create a key pair
solana-keygen new --force --outfile fake_spl_token.json
solana-keygen new --force --outfile user.json
solana-keygen new --force --outfile user_1.json

2. airdrop 500 sol
solana airdrop 500 $(solana-keygen pubkey user.json) --url http://localhost:12345


2. create token
# 强制使用预生成密钥对创建 Token
spl-token create-token \
  --url http://localhost:12345 \
  --decimals 9 \
  --mint-authority fake_spl_token.json \
  --fee-payer user.json fake_spl_token.json       