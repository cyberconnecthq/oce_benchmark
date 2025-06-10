anvil:
	@anvil --fork-url $(RPC_URL) --fork-block-number $(BLOCK_NUM) --balance 1000 

sim:
	python simulate.py $(TX_RAW)