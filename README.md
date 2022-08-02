Copyright 2021 eContriver LLC

# Overview

The python scripts provided in this project facilitates trying different buy and sell strategies for stock and crypto currencies. There are also scripts that provide different types of security analysis. Both technical analysis and fundamental analysis are considered.

This software is intended for educational purposes only and nothing it produces should be taken as investment advice.
It's accuracy is not guaranteed, the software may have bugs, or the data that it receives from 3rd parties may be
inaccurate. You are responsible for verifying the results that are produced.

# Features

Some of these features are:

* Back-Testing Investment Strategies
* Machine Learning Predictors
* Investment Strategy Comparators
* Intrinsic Value Calculations
* Alerts
* Automated Order Placement

## Single Stock Strategies

Some of the already added strategies are:

* Buy and Hold strategy
* Buy low Sell High
* Trade on MACD Signal
* Trade on RSI
* Black soldiers and white crows

It's easy to add more, so this list will continue to grow.

## Multi stock strategy

Monitor 5 stocks, when any are below RSI 40 buy, when it crosses 70 sell, buy the next of the five to cross 40, rinse and repeat

## Strategy optimization

Each investment strategy has different variables (e.g. RSI has period, upper, lower) and these can be tuned via back testing for a given securities.

Once an optimized set of parameters is determined for one security, then those parameters can be back tested across many different securities.

## Build table of RSI and MACD and use it to predict the next relative price movement of a stock

* This is the correlation of RSI and MACD with how other investors act based on this data

## Integrated ML/AI to make price model predictor and then use it to trade

* Separate groups of data are used for training the model and another for testing/prediction

# Donations

If you want to donate, then you can do that here:
* 0x9046e392d4F12ec5950F058960aF48B3929eCad6 (ETH/BNB/any EVM compatible chain address really)

# Running Tools

_NOTE: If this is your first run, then see the [Getting Started](#getting-started) section first, also there is a [Tool List](#tool-list) which explains each of the different tools in this repository._

Let's run the intrinsic value runner which does a discounted cash flow analysis of securities.

First you must add a file at `~/.eContriver/intrinsic_value.yaml` with the contents:

```
adapter_class: AlphaVantage
base_symbol: USD
price_interval: monthly
fundamentals_interval: yearly
graph: false
symbol: AAPL
```

To run it:
```
(.venv) ➜  finance git:(main) ✗ ./src/intrinsic_value.py
Finance from eContriver (C) 2021 eContriver LLC
This program comes with ABSOLUTELY NO WARRANTY; for details see the GNU GPL v3.
This is free software, and you are welcome to redistribute it under certain conditions.
Last time: 2021-09-30  First time: 2017-09-30
Data table for intrinsic value calculation using TimeInterval.YEAR...
             Shares   Assets Liabilities   Equity Long Debt Short Debt    Eps  Revenue Cash Flow Net Income Dividends Low P/E High P/E      ROE
2017-09-30  5126.2m  $375.3b     $241.3b  $134.0b   $112.6b     $12.0b  $2.30  $229.2b    $64.2b     $48.4b    $12.8b   15.43    17.06   36.07%
2018-09-30  4755.0m  $365.7b     $258.6b  $107.1b   $112.0b     $12.0b  $2.97  $265.6b    $77.4b     $59.5b    $13.7b   17.51    18.68   55.56%
2019-09-30  4443.2m  $338.5b     $248.0b   $90.5b   $117.8b   $5980.0m  $2.98  $256.6b    $69.4b     $55.3b    $14.1b   16.81    18.64   61.06%
2020-09-30    17.0b  $323.9b     $258.5b   $65.3b   $125.9b   $4996.0m  $3.27  $271.6b    $80.7b     $57.4b    $14.1b   31.24    41.81   87.87%
2021-09-30    16.4b  $351.0b     $287.9b   $63.1b   $118.7b   $6000.0m  $5.62  $363.2b   $104.0b     $94.7b    $14.5b   25.07    27.91  150.07%
Data table of intrinsic value predictions using TimeInterval.YEAR...
           Shares   Assets Liabilities   Equity Long Debt Short Debt    Eps  Revenue Cash Flow Net Income Dividends Low P/E High P/E      ROE
2022-09-29  16.4b  $323.8b     $286.8b   $37.0b   $125.2b   $2513.8m  $5.51  $359.3b   $104.0b     $90.2b    $15.0b   31.11    38.25  156.13%
2023-09-28  16.4b  $314.8b     $296.1b   $18.7b   $127.8b    $628.4m  $6.20  $386.6b   $112.2b     $99.2b    $15.3b   34.40    42.72  182.07%
2024-09-26  16.4b  $305.8b     $305.4b  $356.7m   $130.4b      $0.00  $6.89  $413.9b   $120.5b    $108.2b    $15.7b   37.69    47.19  208.01%
2025-09-25  16.4b  $296.7b     $314.7b  $-18.0b   $133.0b      $0.00  $7.58  $441.2b   $128.8b    $117.2b    $16.1b   40.98    51.66  233.95%
2026-09-24  16.4b  $287.7b     $324.0b  $-36.3b   $135.6b      $0.00  $8.27  $468.5b   $137.0b    $126.3b    $16.5b   44.27    56.13  259.89%
book value: current=$63.1b (on 2021-09-30) | prediction=$-36.3b (for 2026-09-24)
dividend: payout=$14.5b (on 2021-09-30) | div/share(DPS)=$0.88 | DPS/EPS=15.67% | retained=84.33%
book: value(BVPS)=$3.84 (on 2021-09-30) | EPS/BVPS(yield)=146.33% | yield*retained(growth)=123.40%
dividends: 2022-09-29: $0.86  2023-09-28: $0.97  2024-09-26: $1.08  2025-09-25: $1.19  2026-09-24: $1.30  
P/Es: max=73.05 avg=46.03 med=36.19 min=32.49 | ROE=259.89%
future prices (P/Es * future EPS $8.27): max=$604.41 avg=$380.84 med=$299.38 min=$268.83 (62.23%) | ROE= (2026-09-24)
last IRR from $141.11 (2021-09-30): max=27.8338% avg=18.4508% med=13.8482% min=11.8506% on 2026-09-24
current IRR from $167.30 (2022-02-18): max=24.224% avg=15.1001% med=10.6243% min=8.6815% on 2026-09-24
fair prices (P/Es * current EPS $5.62): max=$410.56 avg=$258.69 med=$203.36 min=$182.61 (91.62%) (2022-02-18)
price/book=43.56 | price/earnings=29.77 | price/cash flow=26.42
debt/equity=197.65% | liabilities/assets=82.03% | debt/assets=35.53%
-- End report for AAPL
Report file: file:///home/nikc/projects/finance/output/intrinsic_value_runner/AAPL_yearly_AlphaVantage.log
>> Running took: 0:01:10.004127s
```

# Tool List

## Intrinsic Value Runner

Add `~/.eContriver/intrinsic_value.yaml`:

```yaml
adapter_class: AlphaVantage
base_symbol: USD
price_interval: monthly
fundamentals_interval: yearly
#fundamentals_interval: quarterly
asset_type_overrides:
  ETH: DIGITAL_CURRENCY
  LTC: DIGITAL_CURRENCY
  NET: EQUITY
  GEO: EQUITY
  BLK: EQUITY
  WDC: EQUITY
  NOBL: EQUITY
  AI: EQUITY
graph: false
symbol:

```

Run:
```shell
(.venv) ➜  finance git:(main) ✗ ./src/intrinsic_value.py
```

## Alert Runner

Add `~/.eContriver/alert.yaml`:

```yaml
base_symbol: USD
adapter_class: AlphaVantage
#price_interval: hourly
price_interval: daily
asset_type_overrides:
  ETH: DIGITAL_CURRENCY
  LTC: DIGITAL_CURRENCY
  GEO: EQUITY
  BLK: EQUITY
close_boundaries:
  AAPL: [105.00, 120.00]
  AMZN: [2700.00, 2800.00]
  GOOG: [2000.00, 2200.00]
  DIS: [150.00, 190.00]
  PYPL: [260.00, 300.00]
  TSLA: [600.00, 700.00]
  ETSY: [150.00, 200.00]
  ENPH: [150.00, 170.00]
  RDFN: [60.00, 70.00]
  ABNB: [150.00, 170.00]
  PLTR: [22.00, 23.00]
```

Run:
```
(.venv) ➜  finance git:(main) ✗ ./src/alert.py
```

## Multi-Symbol Runner

Add `~/.eContriver/multi_symbol.yaml`:

```yaml
adapter_class: AlphaVantage
base_symbol: USD
price_interval: daily
graph: false
start_time: 2019-07-23
#end_time: 2021-07-23
asset_type_overrides:
  ETH: DIGITAL_CURRENCY
  LTC: DIGITAL_CURRENCY
  GEO: EQUITY
  BLK: EQUITY
symbols:
  # Crypto dance...
#  - BTC
#  - ETH
  - XLK  # Technology
  - XLE  # Energy
```

Run:
```
(.venv) ➜  finance git:(main) ✗ ./src/multi_symbol.py
```

## Symbol Runner


Add `~/.eContriver/symbol.yaml`:

```yaml
base_symbol: USD
adapter_class: AlphaVantage
#price_interval: hourly
price_interval: daily
asset_type_overrides:
  ETH: DIGITAL_CURRENCY
  LTC: DIGITAL_CURRENCY
  DASH: EQUITY
  GEO: EQUITY
  BLK: EQUITY
graph: false
#graph: true
report_types:
  - BUY_AND_HOLD
  - LAST_BOUNCE
  - BUY_DOWN_SELL_UP_TRAILING
  - BUY_UP_SELL_DOWN_TRAILING
  - SOLDIERS_AND_CROWS
  - BOUNDED_RSI
  - MACD_CROSSING
symbol: BTC
```

Run:
```
(.venv) ➜  finance git:(main) ✗ ./src/symbol.py
```

## Trend Runner


Add `~/.eContriver/trend.yaml`:

```yaml
base_symbol: USD
adapter_class: AlphaVantage
price_interval: hourly
#price_interval: daily
asset_type_overrides:
  ETH: DIGITAL_CURRENCY
  LTC: DIGITAL_CURRENCY
  DASH: EQUITY
  GEO: EQUITY
  BLK: EQUITY
report_types:
  - INTEREST_OVER_TIME
#  - HISTORICAL_INTEREST
#  - REGION
#  - TRENDING
#  - TOP_CHARTS
#  - KEYWORD_SUGGESTION
  - RELATED_QUERY
  - RELATED_TOPIC
graph: true
terms: ['hood stock price']
symbol: HOOD
```

Run:
```
(.venv) ➜  finance git:(main) ✗ ./src/trend.py
```

# Adapter List

_WARNING: The code has changed a lot recently and not all of the adapters have been updated yet!_

The adapters that were working at one point are:

* `AlphaVantage`
* `Binance`
* `CoinbasePro`
* `FinancialModelingPrep`
* `IexCloud`
* `Kraken`
* `Quandl`
* `Robinhood`
* `TDAmeritrade`
* `Yahoo`

Only the brokerage/exchange endpoints support orders i.e.

* `Binance`
* `CoinbasePro`
* `Kraken`
* `Robinhood`
* `TDAmeritrade`

# Getting Started

## Linux Development

```
git clone git@github.com:eContriver/finance.git
cd finance
```

setup environment
```
poetry shell
```

start IDE
```
pushd ~/.pycharm/ && (nohup /opt/pycharm-community-2022.1.3/bin/pycharm.sh ~/projects/finance &); popd
```

install dependencies
```
sudo apt update

sudo apt -y install python-wxtools unzip wget libnss3 

# This will get the binaries instead of build from source which takes FOREVER
pip install -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04/ wxPython

pip install -r requirements.txt
```

### For new projects

To build the new environment start with:

```
poetry init
```

## Windows Development

## Windows WSL2 Development (w/ X11 forwarding)

If on Windows 10 Home you might need to add your user to the `docker-users` group:

    net localgroup docker-users "your-user-id" /ADD

Install an X11 display tool, some options are:

* Xming X Server for Windows
* MobaXterm

First setup your ssh keys:

    docker volume create root_home
    docker run --rm -it -v root_home:/root python:3.8.8 ssh-keygen
    docker run --rm -it -v root_home:/root python:3.8.8 cat /root/.ssh/id_rsa.pub

Copy this output and add it to your GitHub SSH keys:

> Top-right Profile Icon | Settings | SSH and GPG Keys | Add New SSH Key

Title: `root@finance_<hostname>`
Key: `<paste the content of the id_rsa.pub>`

_NOTE: The contents of `root_home` can be viewed on Windows usign WSL2 at `\\wsl$\docker-desktop-data\version-pack-data\community\docker\volumes\root_home\_data` and on Linux at `/var/lib/docker/volumes/root_home`. This area can be used for multiple projects so that you don't have to have a separate ssh key for each project._

### Cloning the repo

Create a volume mount on the host machine (works for BASH, CSH, and PowerShell):

    docker volume create --name finance --opt type=none --opt device=$PWD --opt o=bind
 
 Or create a volume mount on NFS using a CIFS path:
 
    docker volume create --name finance --opt type=cifs --opt device=//192.168.2.235/private/projects/finance --driver local --opt o=username=user,password=pw
    
On Windows either of these solutions may perform slowly, using a named volume uses a different file system and may be faster:

    docker volume create finance

If you make a mistake, then you can always clean these up with:

    docker volume rm finance

Now clone the repo into the `finance` volume:
    
    docker run --rm -it -v root_home:/root -v finance:/git alpine/git clone git@github.com:eContriver/finance.git .
    
_NOTE: The contents of `finance` can be viewed on Windows usign WSL2 at `\\wsl$\docker-desktop-data\version-pack-data\community\docker\volumes\finance\_data` and on Linux at `/var/lib/docker/volumes/finance`_

### Running from Docker

    cd <clone location>
    docker compose run dev
    ./src/intrinsic_value.py

# Managing Secrets

_NOTE: The above command only work if you have enable Docker Compose v2, if you have not then just add the `-` between docker and compose._

You only need to provide the secrets that you intend to use. These secrets are currently handled with environment variables.

In a `~/.bash_profile`, `~/.zshrc`, etc.

    export DISPLAY='192.168.1.1:0.0'
    export ALPHA_VANTAGE_API_KEY='?'
    export ROBINHOOD_USERNAME='<email>'
    export ROBINHOOD_PASSWORD='?'
    # Nickname: ?
    export BINANCE_API_KEY='?'
    export BINANCE_SECRET='?'
    # Nickname: ?
    export COINBASE_API_KEY='?'
    export COINBASE_PASSPHRASE='?'
    export COINBASE_SECRET='?'
    # export KRAKEN_API_KEY='?'
    # Description: ?
    # API Key: ?
    # Private: ?
    # Docs: https://apisb.etrade.com/docs/api/account/api-account-v1.html
    export ETRADE_OAUTH_CONSUMER_KEY='?'
    export ETRADE_CONSUMER_SECRET='?'
    # Docs: https://financialmodelingprep.com/developer/docs/
    export FMP_API_KEY='?'
    # Docs: https://www.quandl.com/tools/api
    export QUANDL_API_KEY='?'
    # Docs: https://iexcloud.io/docs/api/
    export IEX_CLOUD_API_KEY='?'

# Adding python dependencies

    # Install the thing
    pip install requests
    # Preserve the dependencies
    pip freeze | tee requirements.txt

## Install all dependencies

    pip install -r requirements.txt

## Upgrade individual

    pip3 install --upgrade tensorflow

## Upgrading all

    pip3 list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip3 install -U

## Upgrade to a specific version (can use ==)

    pip install typing-extensions~=3.7.4

# Building new images

To install a new OS dependency, or an image with new pip dependencies it is good to first test the
build before modifying or messing with the latest. Only after it is working should it over ride the 
latest. To attempt to add a new version - look-up the existing version adn then bump the version:

    export version=0.0.2
    docker-compose run dev

This will attempt to use the version 0.0.2 image and because it doesn't exist it will have to be created.

If you tried to do this without having the version set, then it would just use the latest image and it 
wouldn't even try to build. 


# Testing

## Sequential

The built in unittest runner can be invoked here

    python -m unittest discover ./test/

The built in unittest runner can also be invoked here with custom configuration:

    /app/src/test.py

## Parallel

To test in parallel use:

    pip install unittest-parallel
    cd /app
    unittest-parallel -t ./src/ -s ./src/test/ -v

In PyCharm this can be setup using a configuration with runs script:

* Script path

    /usr/local/bin/unittest-parallel

* Parameters

    -t ./src/ -s ./src/test/ -v

For PyCharm run test button next to each test to work it should be using unittests as the testing framework. PyCharm
will try to auto-detect the frame work and in the past it has failed and selected Twisted Trial. To fix this change it
back to Unittests here:

* File | Settings | Tools | Python Integrated Tools

The error message was:

    OSError: [Errno 95] Operation not supported: '12501' -> '/app/src/test/runners/_trial_temp.lock

The Twisted Trial runner: `_jb_trialtest_runner.py`
The Unittests runner: `_jb_unittest_runner.py`

# Coverage

Working flow is to run this as you work and make sure you are maintaining coverage.

    unittest-parallel -t ./src/ -s ./src/test/ --coverage --coverage-rcfile .coveragerc --coverage-html ./coverage

# Profiling

## cProfile from argument

The Launcher class which is used to start most of the command-line tools has an option '-p' or '--profile' which allows
you to profile the entire session. This will just generate a profile report at the end.

The Profile class can also be used to profile a small section of code, but it does require that you edit the code.

    Profiler.get_instance().enable()
    <code to profile>
    Profiler.get_instance().disable_and_report('/tmp/profile.log', 'cumtime')
    Profiler.get_instance().dump_stats('/tmp/profile.prof')

## cProfile from command-line

    pip install CProfileV
    /usr/local/bin/python -m cProfile /app/src/main.py

    pip install CProfileV
    /usr/local/bin/python -m cProfile -o /app/profile /app/src/main.py
    cprofilev -f /app/profile

## cProfile from command-line with KCacheGrind (a visualization tool)

    python -m cProfile -o multi_symbol.prof multi_symbol.py
    pip install pyprof2calltree
    apt-get install kcachegrind
    pyprof2calltree -k -i multi_symbol.prof

# Large Reruns

To rerun the YAMLs that exist use:

    find /app/output/intrinsic_value_runner/ -name "*.yaml" | xargs -n 1 -P 1 /app/src/intrinsic_value.py -i

To compare a line from these files:

    grep "current IRR" *.log | grep -v nan | grep yearly

# Example output

## STDOUT - Symbol Runner

Used to test strategies with different settings against a single stock

    == Strategy Comparison - Final Results
                                         Buy and Hold:     264.12 % (records:1000)
                                  SMA 200 crossing 50:     165.53 % (records:1000)
                                 Buy 0.9 and Sell 1.2:     107.36 % (records:1000)
                                 Buy 0.8 and Sell 1.4:      96.00 % (records:1000)
        Buy 0.8 -> 1.05 and Sell 1.4 -> 0.95 Trailing:     346.90 % (records:1000)
        Buy 0.9 -> 1.03 and Sell 1.2 -> 0.97 Trailing:     306.07 % (records:1000)

## STDOUT - Matrix Runner

Used to test a set of strategies with settings across a bunch of different securities.

    Strategies - ALL PASSED (260/260)
    == Strategies Across Symbols CAGR
                    : Buy and Hold
                    :               Last bounce ratio 0.5 threshold 0.05
                    :                             Buy down 0.6 Sell up 1.3 Trailing
                    :                                           Buy up 1.6 Sell down 0.6 Trailing
                    :                                                         3 white soldiers and black crows
               AAPL :        19.90 %        4.12 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
               MSFT :        33.36 %        0.00 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
               NVDA :        61.15 %       30.77 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
               INTC :         5.97 %        0.00 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
               AVGO :        39.71 %        0.00 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 2009-08-06 00:00:00)
                AMD :         4.59 %      -11.71 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
               XLNX :        21.73 %      -19.41 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
                TSM :        54.36 %      -13.49 %        0.00 %      -25.65 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
               GOOG :       111.34 %        0.00 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 2014-03-27 00:00:00)
                 FB :        40.42 %        0.00 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 2012-05-18 00:00:00)
                 VZ :        -1.32 %        0.00 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
                  T :        15.30 %        7.08 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
               NFLX :        -7.69 %        0.00 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 2002-05-23 00:00:00)
                DIS :        63.04 %        3.24 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
               AMZN :        12.60 %        0.00 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
               TSLA :        73.73 %      -25.93 %       24.00 %      -31.03 %        0.00 % (data 2021-06-18 00:00:00 to 2010-06-29 00:00:00)
                 HD :        12.18 %        0.00 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
                  V :        26.89 %        0.00 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 2008-03-19 00:00:00)
                 MA :        16.35 %        0.00 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 2006-05-25 00:00:00)
                AXP :        92.69 %       55.75 %        0.00 %        1.35 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
                JPM :        82.89 %       44.45 %        0.00 %      -13.15 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
                BAC :       112.05 %       71.74 %        0.00 %        0.19 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
                  C :       103.42 %       53.26 %        0.00 %       -1.64 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
                WFC :       153.22 %       -1.18 %        0.00 %       25.84 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
              BRK-B :        49.63 %        0.00 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
                AIG :        97.34 %       72.27 %        0.00 %      -12.53 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
               TTCF :       -17.83 %      -42.97 %      112.94 %      -48.31 %        0.00 % (data 2021-06-18 00:00:00 to 2018-09-12 00:00:00)
               BYND :       -30.45 %       -9.14 %        3.62 %      -49.10 %        0.00 % (data 2021-06-18 00:00:00 to 2019-05-02 00:00:00)
                TLT :       -11.71 %        0.00 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 2002-07-26 00:00:00)
               EXPI :        32.54 %      343.91 %        5.14 %       64.49 %        0.00 % (data 2021-06-18 00:00:00 to 2014-02-19 00:00:00)
                 DE :        62.17 %       55.51 %        0.00 %      -19.14 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
               UHAL :        82.21 %        0.00 %        0.00 %      -14.98 %        0.00 % (data 2021-06-18 00:00:00 to 1999-11-01 00:00:00)
                 SQ :        41.61 %       27.77 %        0.00 %      -23.73 %        0.00 % (data 2021-06-18 00:00:00 to 2015-11-19 00:00:00)
               PYPL :        67.46 %      -15.78 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 2015-07-20 00:00:00)
               SNOW :         1.47 %       -2.07 %       -1.21 %      -53.64 %        0.00 % (data 2021-06-18 00:00:00 to 2020-09-16 00:00:00)
               NVTA :       -44.57 %      -34.82 %      -16.46 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 2015-02-12 00:00:00)
               FROG :       -55.08 %      -13.62 %      -25.92 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 2020-09-16 00:00:00)
               CCIV :       275.47 %      751.48 %       -0.50 %      305.38 %        0.00 % (data 2021-06-18 00:00:00 to 2020-09-18 00:00:00)
               ARKW :        36.23 %       -5.36 %        0.00 %      -34.75 %        0.00 % (data 2021-06-18 00:00:00 to 2014-09-30 00:00:00)
               ARKQ :        49.01 %       -7.51 %        0.00 %      -25.97 %        0.00 % (data 2021-06-18 00:00:00 to 2014-09-30 00:00:00)
               ARKF :        35.70 %       -1.75 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 2019-02-04 00:00:00)
               ARKK :        27.48 %       -7.28 %        0.00 %      -34.73 %        0.00 % (data 2021-06-18 00:00:00 to 2014-10-31 00:00:00)
               ARKG :        28.38 %       43.46 %        0.00 %      -33.53 %        0.00 % (data 2021-06-18 00:00:00 to 2014-10-31 00:00:00)
               PRNT :        70.70 %       -4.26 %        0.00 %      -18.07 %        0.00 % (data 2021-06-18 00:00:00 to 2016-07-19 00:00:00)
               IZRL :        23.34 %        0.00 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 2017-12-05 00:00:00)
               SOXX :        52.23 %        0.00 %        0.00 %        0.00 %        0.00 % (data 2021-06-18 00:00:00 to 2001-07-13 00:00:00)
               CMPS :        -3.34 %        1.17 %       -2.73 %      -51.97 %        0.00 % (data 2021-06-18 00:00:00 to 2020-09-18 00:00:00)
               MNMD :       547.74 %      704.23 %       81.92 %       87.22 %        0.00 % (data 2021-06-18 00:00:00 to 2020-03-03 00:00:00)
                BTC :       413.54 %       54.26 %      -13.30 %      149.30 %        0.00 % (data 2021-06-21 00:00:00 to 2018-09-26 00:00:00)
                ETH :      1282.90 %     1134.22 %      -21.85 %      722.36 %        0.00 % (data 2021-06-21 00:00:00 to 2018-09-26 00:00:00)
                LTC :       465.35 %      647.02 %      -50.76 %      324.63 %        0.00 % (data 2021-06-21 00:00:00 to 2018-09-26 00:00:00)
               DOGE :    103066.29 %     7427.59 %      127.17 %     3439.62 %        0.00 % (data 2021-06-21 00:00:00 to 2019-07-05 00:00:00)
            Average :      2072.96 %      217.63 %        4.27 %       89.01 %        0.00 %
               Wins :           39             9             2             2             0
    >> Running took: 0:01:21.022097s

## Graphical

![BTC to USD Example](doc/images/btc_example.png)

# Proposal for new Adapter design

To get the data we need to connect the ValueType
    url
    end-point
    query params (apikey, args, etc.)
    the key to the location of the ValueType
    a conversion algorithm

# Proposal for new Visualizer design

Given the canned data in a time-series format graph as: bar, line
Given the canned data of high, low, open, close graph as: candle-stick
Add ability to
* draw annotations on any
* select if multiple are added to any one plot with a legend
* select if multiple are added to a single window

# Planned

## Play with

6/10 best days for the market came right after the worst 2 weeks
* Check for 2 weeks of down trend across the market or a sector
* Model buying here with an exponential increase

Exponential increase
* at 50% dip invest 99.999% of cash
* at 1% dip invest 2% or something similar
* these are percents of percents, so 2% + 4% the cash pool is getting smaller adn these percents are not the same as the
  percent when the strategy starts, try to see if we can compensate for that

Narrowing Yield Curves
* generally indicative of an on coming recession or a slowing of growth
* sharp decline in bonds
    * the 5 year yields are going up and 30 year yields are going down June 18 2021
    * the 5 year prices are going down and 30 year prices are going up June 18 2021
* Powell thinks we have more disk of seeing disinflation
    * commodities like copper have been going down for ~20 years and in the last 6-8 weeks we just broke out of that and
      trended up for the first in a long time, commodities are just now (June 19th 2021) going down again

Crypto leverage
* it is expected that because of no regulation cryptos are highly leveraged... what does this mean?
    * is crypt trade on margin?
    * is more than a 9/10 lent out?

## Identify highly shorted

* After GME heavily shorted companies will probably do well
* In addition to this, we need to be able to see how many shares were available
* For the short position to be open someone has to buy the stock and hold it so that someone else can short it
  if the number of available shares is low, then it's easier to buy through the resistance levels and push the stock
  higher and higher, the compound that with the short squeeze and wow

## Add page generation for:

* Bloomberg Terminal: Short interest
* Insider trading: http://openinsider.com/
* Bond maturity dates and prices - yield to maturity vs risk : finra
* Debt Exchange ?: ?
* Leverage exposure/risk: ?
* What are the whales buying: whalewisdom
* Read SEC information filings: sec.gov and openinsider.com
  * https://notebooks.gesis.org/binder/jupyter/user/janlukasschroed-python-tutorial-fadn373a/notebooks/SEC%2BAPI%2BDemo.ipynb
  * https://sec-api.io/docs
* Filters like market cap 100m - 700m for huge growth
* Time based trailing limit adjustment - didn't get my sell in the last 3 days, adjust to the new high/low (already just on 1 day anyways, right?)
* From X number of trailing days buy 10 on 5% dip buy using 10% of cash, 10% dip 20% of cash, 20% dip 40%, 30% dip 80%
* Sell on high short interest buy on low short interest
* Buy on high (6 sigma) insider buying and sell on high insider selling: edgar adapter
  * https://iexcloud.io/docs/api/#insider-transactions
* Momentum, day5ChangePercent...year5ChangePercent
  * https://iexcloud.io/docs/api/#key-stats
* Checkout Quandl
* For 10 years+ of balance sheets checkout: https://financialmodelingprep.com/
* Show margin debt for all of the traders and companies or in a macro way
    * https://www.advisorperspectives.com/dshort/updates/2021/05/19/margin-debt-and-the-market-up-another-3-in-april-continues-record-trend
    * This doesn't account for the equity in cryptos - $1.6T: https://coinmarketcap.com/
* Company debt is way up in May 2021, can we view this versus
* Average and aggregate all Future P/E estimates from all stocks in say the S&P 500 and see if the average estimate if
  the future is trending up or down

## Real Estate research

* Down payments size/percentages
* Interest rates
* Eviction Percentages
  * Mortgage forbearance
  * People holding in forbearance, how much equity do they have?
* What is the current equity rate?
* What is the appreciation rate?
* Inventory
* Who is getting loans and who is refinancing?
  * Credit scores
  * Income
* Who is looking to buy?
  * What are their credit scores?
  * Income
  * Is there enough of them to absorb a flood of supply?

## Tax Services

* Pay Taxes on the Spot for every crypto transaction = $100/year ?BTC/year ?ETH/year $10/month
    - Give us your wallet addresses and we'll calculate what you owe on taxes
    - Partner with: https://giveth.io/project/support-protests-in-colombia-soscolombia
        o To auto write-off donations
    - Suggest donations of things that would off-set taxes
* Save current Crypto prices and record from that point forward
* ...

* How does the price of a house in Bitcoin change over time?
* How does the price of a house in Gold change over time?
* How does the price of a house in Ethereum change over time?

## Calendar

Unemployment runs out in September
Evictions
Tapering
Etc.

Stimulus payments with
* Consumer spending
* Stock prices

# Service Signups

Sign-up for IEX Cloud: https://iexcloud.io/s/becb5771

# Social Media

* Social Media to Follow
    * https://www.reddit.com/user/Criand/
    * DFV

# Careers

* https://www.rentec.com/Careers.action?computerProgrammer=true

# Notes

## Normal Orders

    Order Types       - market: $50
    market            - buy: $50 (market)   sell: $50 (market)
    stop-loss         - buy: $55 -> market  sell: $45 -> market (a.k.a. stop order)
    limit             - buy: $45 (or less)  sell: $55 (or more)
    stop-limit        - buy(stop: $55 limit: $60): $55 -> $60 (or less)
                        sell(stop: $45 limit: $40): $45 -> $40 (or more)
    trailing stop     - buy(trailing: $5): low + $5 -> market
                      - sell(trailing: $5): high - $5 -> market
    one-cancels-other - limit + stop-limit

For _buy_ imagine stock closes one day $45 and then opens at $65

* stop-loss would execute at $65
* stop-limit would create a limit order at $60, but would not execute

For _sell_ imagine stock closes one day $55 and then opens at $35

* stop-loss would execute at $35
* stop-limit would create a limit order at $40, but would not execute

Had to sync Windows host to get docker and wsl time to be accurate, but that wasn't enough

    pip install --editable git+https://github.com/sammchardy/python-binance#egg=python-binance python-binance

# Infra

## Install pycharm into /root persistent local volume

    curl https://download.jetbrains.com/python/pycharm-community-2021.2.2.tar.gz > /tmp/file_to_extract
    tar -xzf /tmp/file_to_extract -C /root/
    rm -rf /tmp/file_to_extract
    mv /root/pycharm-community-*/ /root/pycharm-community/

Run with:

    /root/pycharm-community/bin/pycharm.sh /app

Then locate the Dockerfile installed pip packages by switching the interpreter to:

    /usr/local/bin/python

## Run without cython for debugging (if not hitting breakpoints otherwise):

    PYDEVD_USE_CYTHON=NO /root/pycharm-community-2020.3.3/bin/pycharm.sh /app

## Install a browser like Chrome with

    cd /root
    curl https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    apt update
    
    apt install google-chrome-stable_current_amd64.deb
    /usr/bin/google-chrome-stable --no-sandbox
    
    # Didn't work to install to root dir
    #dpkg-deb -x /root/google-chrome-stable_current_amd64.deb /root/google-chrome/

    # To prepend --no-sandbox
    cat ~/chrome.sh
    #!/bin/bash
    /usr/bin/google-chrome --no-sandbox $@

## WSL start up

Using WSL 2 on Windows 10

Use the Ubuntu 20.04 LTS (solid black background):

    sudo mount -t drvfs S: /mnt/s

Launching via docker from within the WSL 2 shell:

## PyCharm IDE logs and fixes

### Hyperlinks in console stop working

Regular hyperlinks like https://google.com only work if you have a browser setup in the container
(many do not).

File hyperlinks only work in Python console. To run and debug from the Python console then edit
the run configuration > [x] (check) Run with Python console


### libnss3

Logs are located here

    vi /root/.cache/JetBrains/PyCharmCE2020.3/log/idea.log

One error:

    2021-03-01 12:33:17,322 [   6969]  ERROR - #com.intellij.ui.jcef.JBCefApp - /root/pycharm-community-2020.3.3/jbr/lib/libjcef.so: libnss3.so: cannot open shared object file: No such file or directory
    java.lang.Throwable: /root/pycharm-community-2020.3.3/jbr/lib/libjcef.so: libnss3.so: cannot open shared object file: No such file or directory

Clicking link takes you to:

    https://intellij-support.jetbrains.com/hc/en-us/articles/360016421559

Reported missing years:

    12:33 PM	JCEF browser component failed to start
            Missing native libraries: 	libnss3.so, 	libnssutil3.so, 	libsmime3.so, 	libnspr4.so, 	libasound.so.2

Looking for missing libs:

    ldd /root/pycharm-community-2020.3.3/jbr/lib/libjcef.so | grep "not found"

    apt-get install -y unzip wget libnss3

That seems to have fixed it

### No connection

Debugger magically broke...

    2021-03-01 13:17:44,994 [ 109600]  ERROR - debugger.pydev.AbstractCommand - No connection (command:  113 )
    java.lang.Throwable: No connection (command:  113 )
            at com.intellij.openapi.diagnostic.Logger.error(Logger.java:159)
            at com.jetbrains.python.debugger.pydev.AbstractCommand.execute(AbstractCommand.java:159)
            at com.jetbrains.python.debugger.pydev.RemoteDebugger.evaluate(RemoteDebugger.java:158)
            at com.jetbrains.python.debugger.pydev.MultiProcessDebugger.evaluate(MultiProcessDebugger.java:167)

This sounds to be related to `__str__` conversions which has just been changed, but was able to find another workaround
which is to go to:

[File | Settings | Build, Execution, Deployment | Python Debugger](jetbrains://PyCharmCore/settings?name=Build%2C+Execution%2C+Deployment--Python+Debugger)

Enable: `Gevent compatible`

# Concepts

    DataAdapters - Interfaces to data bases/services/etc. A single dataAdapter
                   can be used with multiple symbolAdapters but sometimes there are duplicates - the cache helps here.
    SymbolAdapters - Owns dataAdapters for a symbol and has interval, current time, as well as
                     historic price data for that symbol
    SymbolCollection - A collection of symbolAdapters referenced by symbol
                       and tracks the baseSymbol
    Portfolio - Represents quantities of symbols which tracks it's value over time
                The only representation of 'today' is the getLastCompletedTime which is really now - 1
                as we have not yet calculated the current day - where we are


# Architecture

## Portfolio Topology

    Data               Symbol         Symbol
    Adapters           Adapters       Collection    Portfolio

                                +---> USD <---+---> USD
    (Broker A) <--+--> GOOG <---+             +---> GOOG
                  +--> BTC  <---+             +---> BTC
    (Broker B) <-----> DOGE <---+             +---> DOGE

## Adapter Topology

    Data            Data            Symbol
    Response        Adapter         Adapter
                      +-----------

    ValueType                            QueryType
    HIGH, LOW, OPEN, CLOSE    <----->    SERIES
    RSI                       <----->    RSI
    SMA                                  SMA


## User can pick data provider

For one stock a user may want series from provider A and MACD from another provider
Each of these requires a different data adapter, but we should store under the symbol adapter for one symbol

The client API to get value:

    collection.get_value(symbol, instance, value_type)

When the user requests a value it should traverse like:

    SymbolCollection()
    collection[symbol] -> SymbolAdapter()  # value_type -> query_type
                          symbolAdapter[query_type] -> DataAdapter(symbol)  # type should represent query_type
                                                       data_adapter.get_value(instance, value_type)

Construction:

    symbol_types = {'ETH': SymbolType.DIGITAL_CURRENCY}
    base_symbol = 'USD'
    series_data_adapter: SeriesAdapter = AlphaVantageAdapter('AMD', base_symbol)
    series_data_adapter.series_interval = interval
    series_data_adapter.asset_type = AssetType.EQUITY
    symbol_adapter = SymbolAdapter(symbol)
    symbol_adapter.data_adapters[QueryType.SERIES] = series_data_adapter
    rsi_data_adapter: RsiAdapter = BinanceAdapter('AMD', base_symbol)
    rsi_data_adapter.interval = interval
    rsi_data_adapter.period = period
    symbol_adapter.data_adapters[QueryType.RSI] = rsi_data_adapter
    macd_data_adapter: MacdAdapter = BinanceAdapter()
    macd_data_adapter.fast_period = fast
    macd_data_adapter.slow_period = slow
    macd_data_adapter.signal_period = signal
    symbol_adapter.data_adapters[QueryType.MACD] = macd_data_adapter
    collection = SymbolCollection()
    collection.baseSymbol = 'USD'  # propagate to all data adapters on set?
    collection.add_symbol_adapter(symbol_adapter)


# References

List of lots of quant APIs:

* https://github.com/wilsonfreitas/awesome-quant#data-sources

Pandas DataReader

* https://pydata.github.io/pandas-datareader/remote_data.html
* https://github.com/pydata/pandas-datareader

AlphaVantage

* https://github.com/RomelTorres/alpha_vantage
