#  Copyright 2021 eContriver LLC
#  This file is part of Finance from eContriver.
#
#  Finance from eContriver is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  any later version.
#
#  Finance from eContriver is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Finance from eContriver.  If not, see <https://www.gnu.org/licenses/>.

import logging
import math
from datetime import datetime, timedelta
from typing import Dict

import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.python.keras import Sequential
from tensorflow.python.keras.layers import LSTM, Dense

from main.adapters.alpha_vantage import AlphaVantage
from main.application.adapter import TimeInterval, Adapter
from main.application.value_type import ValueType
from main.common.time_zones import TimeZones
from main.application.adapter_collection import AdapterCollection
from main.application.runner import Runner


class MLTrainingRunner(Runner):
    def __init__(self):
        super().__init__()
        self.symbols = []

    def start(self):
        logging.info("#### Starting ML training runner...")

        success = True
        self.symbols = [
            # Technology
            'AAPL',  # Consumer Electronics
            # 'MSFT',  # Software / Infrastructure
            # 'NVDA', 'INTC', 'AVGO',
            # 'AMD', 'XLNX', 'TSM',  # Semiconductors
            # # Communication Services
            # 'GOOG', 'FB',  # Internet Information
            # 'VZ', 'T',  # Telecommunications
            # 'NFLX', 'DIS',  # Entertainment
            # # Commercial
            # 'AMZN',  # Internet Retail
            # 'TSLA',  # Automotive Manufacturing
            # 'HD',  # Home Improvement
            # # Financial
            # 'V', 'MA', 'AXP',  # Credit Services
            # 'JPM', 'BAC', 'C', 'WFC',  # Banks - Diversified
            # 'BRK-B', 'AIG',  # Insurance - Diversified
            # # Foods
            # 'TTCF',  # Buy at 18
            # 'BYND',  # 'IMPM',  # Buy impossible at $120
            # # Bonds
            # 'TLT',
            # # Real Estate
            # 'EXPI',
            # # Farm / Commodities
            # 'DE', 'UHAL',
            # # Dividend + Reinvest
            # "FSKR",
            # # MJ
            # # "GGTTF",
            # # Payments
            # 'SQ', 'PYPL', 'SNOW', 'NVTA', 'FROG',
            # # SPACs
            # 'IPOE', 'CCIV',  # 'CCIX',
            # # ETFs
            # 'ARKW', 'ARKQ', 'ARKF', 'ARKK', 'ARKG', 'PRNT', 'IZRL',  # ARK
            # # Digital Currencies
            # # 'BTC', 'ETH', 'LTC', 'DOGE',
        ]

        # Split the data into x_train and y_train data sets
        x_train = []
        y_train = []

        sample_size = 60
        predict_size = 7

        today = datetime.now(TimeZones.get_tz())
        years = 20
        start = today - timedelta(weeks=years * 52)
        yesterday = today - timedelta(days=1)

        data_adapter_class = AlphaVantage
        # data_adapter_class = Yahoo
        collection: AdapterCollection = AdapterCollection()
        for symbol in self.symbols:
            adapter: Adapter = data_adapter_class(symbol)
            adapter.base_symbol = 'USD'
            adapter.interval = TimeInterval.DAY
            collection.add([ValueType.CLOSE], adapter)
        # These can run in parallel as they do for Strategy.run() which is called in ParallelStrategyRunner when
        # Runners are called, if we can build each model separately and then later join them we could get the data
        # in parallel here as well... for now we just get it all sequentially using this:
        collection.retrieve_all_data()
        # Each Strategy builds it's own Collection - 1 (base) Strategy owns 1 Collection, the
        #       Collection is determined and constructed by the Symbol (leaf) constructor (e.g. BuyAndHold)
        # The Collections are used here to house the Series, RSI, SMA, MACD, etc. DataAdapters used
        # collection.retrieve_data_parallel() # return values are not being passed

        for symbol in self.symbols:
            # dataframe = web.DataReader(symbol, data_source=data_adapter_class.name, start=start.strftime('%Y-%m-%d'), end=yesterday.strftime('%Y-%m-%d'))
            # Dataframe was Dates by ValueTypes
            #logging.info("Dataframe: {}".format(dataframe))

            # plt.style.use('fivethirtyeight')

            # plt.figure(figsize=(16, 8))
            # plt.title('Close Price History')
            # plt.plot(df['Close'])
            # plt.xlabel('Date', fontsize=18)
            # plt.ylabel('Close Price USD ($)', fontsize=18)
            # plt.show()

            # Create new dataframe with only close column

            # TODO: Rename to mlPriceTrainingRunner - where we try to guess the price
            # TODO: Add mlMovementTrainingRunner - where we try to guess direction of movement

            # TODO: Add LSTM 10 years of earnings growth, and everything that factors into valuing a business, and
            #       ensure that the system accurately predicts the future value of the company. Can back test using all
            #       stocks and just testing the most recent couple of years. Could also back test using all data for a
            #       select few stocks, and then test it against other stocks.

            # TODO: Predict 7 days from 60 most recent
            #       Multi-step time-series forecasting: Multiple output strategy
            # TODO: Predict 1 then use that in next prediction and predict 7 days out
            #       Multi-step time-series forecasting: Recursive multi-step forecast strategy
            # TODO: Predict 7th day into the future from 60 most recent (or add a model for each day to forward predeict 7 days == 7 models)
            #       Multi-step time-series forecasting: Direct multi-step forecast strategy
            # TODO: Create separate model to predict each future value (e.g. 7 models) and feedback output of first into 2nd (like above but uses predicted outputs in next model)
            #       Multi-step time-series forecasting: Direct-recursive hybrid strategy

            # TODO: Examine several of the 60 + 7 day views and see if an x^3 or x^4 etc matches
            # TODO: Consider that a x^3 will end up going up while a x^4 will end up going down
            #       Perhaps use both of these models to vote: is up is flat and down is down... then predict down

            # TODO: Layer count
            # TODO: Neuron count
            # TODO: Back count
            # TODO: Forward count
            # TODO: Use OCLH as the 4 inputs
            # TODO: Use low and high?

            data: Dict[datetime, float] = collection.get_column(symbol, ValueType.ADJUSTED_CLOSE)
            logging.info("Dataframe: {}".format(list(data.items())[:5]))
            # data = dataframe.filter(['Adj Close'])

            # Convert dataframe to numpy array
            dataset = np.array(list(data.values())).reshape(-1, 1)
            logging.info("Closing Values: {}...".format(list(dataset)[:5]))

            # Get the number of rows to train the model on
            # NOTE: In the example we used 80% of this one stock for training and 20% for testing, but here we use all
            #       data for training and then test against an unknown symbol
            training_data_len = math.ceil(len(dataset) * 1.0)
            logging.info("Data length: {}".format(training_data_len))

            # Scale the data (needed before presenting to a NN)
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(list(dataset))
            logging.info("Scaled data: {}...".format(scaled_data[:5]))

            # Create the training dataset
            # Create scaled training dataset
            train_data = scaled_data[0:training_data_len, :]  # 0 to train length and all of column
            logging.info("Training data: {}...".format(train_data[:5]))

            logging.info("Output size: {}".format(predict_size))

            for i in range(sample_size, len(train_data) - predict_size + 1):  # 1 to get last
                x_train.append(train_data[i - sample_size:i, 0])   # Add 60 values 0 - 59
                y_train.append(train_data[i:i + predict_size, 0])  # The feature is the 60th value
                if i <= 61:
                    logging.info("X:" + str(x_train))
                    logging.info("Y:" + str(y_train))

            break

        # Convert the x_train and y_train to numpy arrays
        x_train, y_train = np.array(x_train), np.array(y_train)
        logging.info("X training data: {} (shape: {})".format(x_train, x_train.shape))
        logging.info("Y training data: {} (shape: {})".format(y_train, y_train.shape))

        # Reshape the data into 3D
        features = 1
        time_steps = x_train.shape[0]
        assert sample_size == x_train.shape[1]
        x_train = np.reshape(x_train, (time_steps, sample_size, features))
        logging.info("X reshaped data: {} (shape: {})".format(x_train, x_train.shape))

        # TODO: Look at using KerasClassifier and see if we can add a mechanism to  determine the best models for us

        # Build the LSTM Model
        model = Sequential()
        # TODO: Use CuDNNLSTM as it should be more performant
        # Note that this cell is not optimized for performance on GPU.Please use
        # `tf.compat.v1.keras.layers.CuDNNLSTM` for better performance on GPU.
        model.add(LSTM(50, return_sequences=True, input_shape=(x_train.shape[1], features)))
        model.add(LSTM(50, return_sequences=False))
        model.add(Dense(25))
        model.add(Dense(predict_size))
        # model.add(Dense(1))

        ### Multi-Model Solution?  https://stackoverflow.com/questions/57227908/keras-multi-output-data-reshape-for-lstm-model
        # import tensorflow as tf
        # import numpy as np
        #
        # tf.enable_eager_execution()
        #
        # batch_size = 100
        # seq_length = 10
        # feature_cnt = 5
        # output_branches = 3
        #
        # # Say we've got:
        # # - 100-element batch
        # # - of 10-element sequences
        # # - where each element of a sequence is a vector describing 5 features.
        # X = np.random.random_sample([batch_size, seq_length, feature_cnt])
        #
        # # Every sequence of a batch is labelled with `output_branches` labels.
        # y = np.random.random_sample([batch_size, output_branches])
        # # Here y.shape() == (100, 3)
        #
        # # Here we split the last axis of y (output_branches) into `output_branches` separate lists.
        # y = np.split(y, output_branches, axis=-1)
        # # Here y is not a numpy matrix anymore, but a list of matrices.
        # # E.g. y[0].shape() == (100, 1); y[1].shape() == (100, 1) etc...
        #
        # outputs = []
        #
        # main_input = tf.keras.layers.Input(shape=(seq_length, feature_cnt), name='main_input')
        # lstm = tf.keras.layers.LSTM(32, return_sequences=True)(main_input)
        # for _ in range(output_branches):
        #     prediction = tf.keras.layers.LSTM(8, return_sequences=False)(lstm)
        #     out = tf.keras.layers.Dense(1)(prediction)
        #     outputs.append(out)
        #
        # model = tf.keras.models.Model(inputs=main_input, outputs=outputs)
        # model.compile(optimizer='rmsprop', loss='mse')
        #
        # model.fit(X, y)


        # Compile the model
        model.compile(optimizer='adam', loss='mean_squared_error')

        # Train the model
        model.fit(x_train, y_train, batch_size=1, epochs=1)

        # There are ways to merge models - if so, then can we train and work on each independently and then merge?

        model.summary()
        filename = '../.cache/models/{}.symbols{}.outputs{}.{}.{}.{}days.h5'.format(
            data_adapter_class.name,
            len(self.symbols),
            predict_size,
            start.strftime('%Y-%m-%d'),
            yesterday.strftime('%Y-%m-%d'),
            sample_size)
        logging.info("Saving model to: {}".format(filename))
        model.save(filename)

        return success

