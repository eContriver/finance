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