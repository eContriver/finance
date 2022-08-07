# Overview
This is needed to run the `block_analyzer.py` script

You can find other shared nodes that support RPC (namely `bitcoind`), however you can just run your own node by following these directions.

# Reference
https://developer.bitcoin.org/examples/intro.html

One Linux a configuration file will be read from:
* Linux: `$HOME/.bitcoin/bitcoin.conf`

Let's create this file:
```shell
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
Visit: https://bitcoin.org/en/download

