# Overview
This is needed to run the `block_analyzer.py` script

You can find other shared nodes that support RPC (namely `bitcoind`), however you can just run your own node by following these directions.

# Support
See:
* Forum: https://bitcointalk.org/index.php?board=4.0
* IRC channels: https://en.bitcoin.it/wiki/IRC_channels

Supposed to use the faucet:
* https://tpfaucet.appspot.com
* we don't need money here, we just want to read data from teh chain, so I don't think we need this
* if we do need coins and the faucet isn't available, then we can use the `regtest` mode, see:
  https://developer.bitcoin.org/examples/testing.html


# Installing `bitcoind`
Visit: https://bitcoincore.org
I downloaded version 23.0
I extracted the tar ball, then ran:
```shell
sudo mv ~/Downloads/bitcoin-23.0 /opt/
```

# Configuring `bitcoind`
https://developer.bitcoin.org/examples/intro.html

One Linux a configuration file will be read from:
* Linux: `$HOME/.bitcoin/bitcoin.conf`

Let's create this file:
```shell
mkdir $HOME/.bitcoin
touch $HOME/.bitcoin/bitcoin.conf
chmod 0600 bitcoin.conf
vim $HOME/.bitcoin/bitcoin.conf
```
Then change the content to:
```conf
rpcpassword=my_veruy_super_secret_and_super_long_password_nody_can_guess
testnet=1
```

Bitcoin has a test network that we can use while testing:
* https://developer.bitcoin.org/devguide/p2p_network.html

# Running `bitcoind`

```shell
/opt/bitcoin-23.0/bin/bitcoind
```

This was syncing all of the test data and then replaying it - it was much faster than the live network
* This still took 1 hour

# Building Bitcoin Core from Source
```shell
cd ~/projects
git clone git@github.com:bitcoin/bitcoin.git
```

Start here: https://github.com/bitcoin/bitcoin/blob/master/doc/README.md

Install dependencies: https://github.com/bitcoin/bitcoin/blob/master/doc/dependencies.md
***WARNING: actually I stopped here the download finally went through (in [[#Installing bitcoind]] and I used a pre-compiled binary instead*

Then from: https://github.com/bitcoin/bitcoin/blob/master/doc/build-unix.md
*NOTE: Check to see if on BSD using `uname` if it says `Linux` then use what is above, but if it says `FreeBSD` then you have to find the BSD doc.*

Now configure:
```shell
./autogen.sh
./configure
make -j16
make install # optional
```

# Output from `bitcoind` upon start
```
➜  ~ /opt/bitcoin-23.0/bin/bitcoind 
2022-08-07T16:42:14Z Bitcoin Core version v23.0.0 (release build)
2022-08-07T16:42:14Z Assuming ancestors of block 00000000000163cfb1f97c4e4098a3692c8053ad9cab5ad9c86b338b5c00b8b7 have valid signatures.
2022-08-07T16:42:14Z Setting nMinimumChainWork=00000000000000000000000000000000000000000000064728c7be6fe4b2f961
2022-08-07T16:42:14Z Using the 'x86_shani(1way,2way)' SHA256 implementation
2022-08-07T16:42:14Z Using RdSeed as additional entropy source
2022-08-07T16:42:14Z Using RdRand as an additional entropy source
2022-08-07T16:42:14Z Default data directory /home/sooth/.bitcoin
2022-08-07T16:42:14Z Using data directory /home/sooth/.bitcoin/testnet3
2022-08-07T16:42:14Z Config file: /home/sooth/.bitcoin/bitcoin.conf
2022-08-07T16:42:14Z Config file arg: rpcpassword=****
2022-08-07T16:42:14Z Config file arg: testnet="1"
2022-08-07T16:42:14Z Using at most 125 automatic connections (1024 file descriptors available)
2022-08-07T16:42:14Z Using 16 MiB out of 32/2 requested for signature cache, able to store 524288 elements
2022-08-07T16:42:14Z Using 16 MiB out of 32/2 requested for script execution cache, able to store 524288 elements
2022-08-07T16:42:14Z Script verification uses 15 additional threads
2022-08-07T16:42:14Z scheduler thread start
2022-08-07T16:42:14Z HTTP: creating work queue of depth 16
2022-08-07T16:42:14Z Config options rpcuser and rpcpassword will soon be deprecated. Locally-run instances may remove rpcuser to use cookie-based auth, or may be replaced with rpcauth. Please see share/rpcauth for rpcauth auth generation.
2022-08-07T16:42:14Z HTTP: starting 4 worker threads
2022-08-07T16:42:14Z Using wallet directory /home/sooth/.bitcoin/testnet3/wallets
2022-08-07T16:42:14Z init message: Verifying wallet(s)…
2022-08-07T16:42:14Z Using /16 prefix for IP bucketing
2022-08-07T16:42:14Z init message: Loading P2P addresses…
2022-08-07T16:42:14Z Creating peers.dat because the file was not found ("/home/sooth/.bitcoin/testnet3/peers.dat")
2022-08-07T16:42:14Z init message: Loading banlist…
2022-08-07T16:42:14Z Recreating the banlist database
2022-08-07T16:42:14Z SetNetworkActive: true
2022-08-07T16:42:14Z Failed to read fee estimates from /home/sooth/.bitcoin/testnet3/fee_estimates.dat. Continue anyway.
2022-08-07T16:42:14Z Cache configuration:
2022-08-07T16:42:14Z * Using 2.0 MiB for block index database
2022-08-07T16:42:14Z * Using 8.0 MiB for chain state database
2022-08-07T16:42:14Z * Using 440.0 MiB for in-memory UTXO set (plus up to 286.1 MiB of unused mempool space)
2022-08-07T16:42:14Z init message: Loading block index…
2022-08-07T16:42:14Z Switching active chainstate to Chainstate [ibd] @ height -1 (null)
2022-08-07T16:42:14Z Opening LevelDB in /home/sooth/.bitcoin/testnet3/blocks/index
2022-08-07T16:42:14Z Opened LevelDB successfully
2022-08-07T16:42:14Z Using obfuscation key for /home/sooth/.bitcoin/testnet3/blocks/index: 0000000000000000
2022-08-07T16:42:14Z LoadBlockIndexDB: last block file = 0
2022-08-07T16:42:14Z LoadBlockIndexDB: last block file info: CBlockFileInfo(blocks=0, size=0, heights=0...0, time=1970-01-01...1970-01-01)
2022-08-07T16:42:14Z Checking all blk files are present...
2022-08-07T16:42:14Z Initializing databases...
2022-08-07T16:42:14Z Opening LevelDB in /home/sooth/.bitcoin/testnet3/chainstate
2022-08-07T16:42:14Z Opened LevelDB successfully
2022-08-07T16:42:14Z Wrote new obfuscate key for /home/sooth/.bitcoin/testnet3/chainstate: 9828c46eced5dbab
2022-08-07T16:42:14Z Using obfuscation key for /home/sooth/.bitcoin/testnet3/chainstate: 9828c46eced5dbab
2022-08-07T16:42:14Z init message: Verifying blocks…
2022-08-07T16:42:14Z  block index               9ms
2022-08-07T16:42:14Z loadblk thread start
2022-08-07T16:42:14Z UpdateTip: new best=000000000933ea01ad0ee984209779baaec3ced90fa3f408719526f8d77f4943 height=0 version=0x00000001 log2_work=32.000022 tx=1 date='2011-02-02T23:16:42Z' progress=0.000000 cache=0.0MiB(0txo)
2022-08-07T16:42:14Z block tree size = 1
2022-08-07T16:42:14Z nBestHeight = 0
2022-08-07T16:42:14Z Failed to open mempool file from disk. Continuing anyway.
2022-08-07T16:42:14Z loadblk thread exit
2022-08-07T16:42:14Z torcontrol thread start
2022-08-07T16:42:14Z Bound to 127.0.0.1:18334
2022-08-07T16:42:14Z Bound to [::]:18333
2022-08-07T16:42:14Z Bound to 0.0.0.0:18333
2022-08-07T16:42:14Z 0 block-relay-only anchors will be tried for connections.
2022-08-07T16:42:14Z init message: Starting network threads…
2022-08-07T16:42:14Z net thread start
2022-08-07T16:42:14Z dnsseed thread start
2022-08-07T16:42:14Z msghand thread start
2022-08-07T16:42:14Z opencon thread start
2022-08-07T16:42:14Z addcon thread start
2022-08-07T16:42:14Z init message: Done loading
2022-08-07T16:42:14Z Loading addresses from DNS seed seed.testnet.bitcoin.sprovoost.nl.
2022-08-07T16:42:15Z Loading addresses from DNS seed testnet-seed.bitcoin.jonasschnelli.ch.
2022-08-07T16:42:15Z Loading addresses from DNS seed testnet-seed.bluematt.me.
2022-08-07T16:42:15Z Loading addresses from DNS seed seed.tbtc.petertodd.org.
2022-08-07T16:42:15Z 96 addresses found from DNS seeds
2022-08-07T16:42:15Z dnsseed thread exit
2022-08-07T16:42:16Z New outbound peer connected: version: 70015, blocks=2315347, peer=0 (outbound-full-relay)
2022-08-07T16:42:16Z Synchronizing blockheaders, height: 2000 (~0.37%)
```