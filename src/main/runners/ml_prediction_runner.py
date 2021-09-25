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

import matplotlib.pyplot as plt
import numpy as np
import pandas
import pandas_datareader as web
from sklearn.preprocessing import MinMaxScaler
from tensorflow import keras

from main.application.adapter import Adapter
from main.application.time_interval import TimeInterval
from main.application.adapter_collection import AdapterCollection
from main.application.argument import ArgumentKey, Argument
from main.application.value_type import ValueType
from main.common.locations import Locations
from main.common.time_zones import TimeZones
from main.application.runner import Runner
from main.runners.ml_runner import MLRunner


class MLPredictionRunner(MLRunner):

    def __init__(self):
        super().__init__()

    def start(self, locations: Locations):
        logging.info("#### Starting ML prediction runner...")

        success = True
        symbol = 'AAPL'
        # symbol = 'BTC'

        # Create new dataframe with only close data
        # base_symbol = 'USD'
        # data_adapter: SeriesAdapter = AlphaVantageAdapter(symbol, base_symbol)
        # data_adapter.series_interval = TimeInterval.DAY
        # data_adapter.asset_type = AssetType.DIGITAL_CURRENCY
        # data_adapter.retrieve_data(QueryType.SERIES)
        # data = data_adapter.get_all_items(ValueType.CLOSE)

        data_source = 'alphaVantage'

        # alphaVantage.symbols47.outputs7.2001-05-24.2021-04-28.60days.h5

        # symbol_count = 47
        sample_size = 60
        predict_size = 7

        # today = datetime(year=2021, month=5, day=20)
        today = datetime.now(TimeZones.get_tz())
        years = 20
        start = today - timedelta(weeks=years*52)
        # start = datetime(year=2012, month=1, day=1)
        symbol_count = len(self.symbols)

        yesterday = today - timedelta(days=1)

        # Create new dataframe with only close column
        collection: AdapterCollection = AdapterCollection()
        symbol = 'AAPL'
        adapter: Adapter = self.adapter_class(symbol)
        adapter.base_symbol = 'USD'
        adapter.interval = TimeInterval.DAY
        adapter.request_value_types = [ValueType.CLOSE]
        adapter.add_argument(Argument(ArgumentKey.INTERVAL, self.price_interval))
        collection.add(adapter)
        collection.retrieve_all_data()
        data: pandas.Series = collection.get_column(symbol, ValueType.CLOSE)
        # df = web.DataReader(symbol, data_source='yahoo', start=start.strftime('%Y-%m-%d'), end=yesterday.strftime('%Y-%m-%d'))
        # data = df.filter(['Adj Close'])

        # Convert dataframe to numpy array
        dataset = data.values.reshape(-1, 1)
        logging.info("Closing Values: {}...".format(dataset[:5]))

        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(dataset)

        training_data_len = math.ceil(len(dataset) * 1.0)
        logging.info("Data length: {}".format(training_data_len))
        # training_data_len = 60  # We are using all of the data here as test data, we already trained (w/o this data)

        # Create the testing dataset
        # Create a new array containing scaled value from index 1860 to 2325
        test_data = scaled_data
        # test_data = scaled_data[training_data_len - 60:, :]  # Add trailing 60 as we need 60

        # Create the datasets x_test and y_test
        x_test = []
        y_test = []

        # y_test = dataset[training_data_len:, :]
        for i in range(sample_size, len(test_data) - predict_size + 1):
            x_test.append(test_data[i - sample_size:i, 0])
            y_test.append(test_data[i:i + predict_size, 0])  # Our final one, we do want to have to the end
            if i <= 61:
                logging.info("X:" + str(x_test))
                logging.info("Y:" + str(y_test))

        # Convert the data into numpy array
        y_test = np.array(y_test)
        x_test = np.array(x_test)
        logging.info("X test data: {} (shape: {})".format(x_test, x_test.shape))
        logging.info("Y test data: {} (shape: {})".format(y_test, y_test.shape))

        # Reshape the data into 3D
        x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))
        logging.info("X Test shape: {}".format(x_test.shape))

        # filename = 'yahoo.full.{}.{}.60days.h5'.format(start.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d'))
        filename = '../.cache/models/{}.symbols{}.outputs{}.{}.{}.{}days.h5'.format(
            data_source,
            symbol_count,
            predict_size,
            start.strftime('%Y-%m-%d'),
            yesterday.strftime('%Y-%m-%d'),
            sample_size)
        logging.info("Reading file: {}".format(filename))
        model = keras.models.load_model(filename)
        # model = keras.models.load_model('yahoo.2012-01-01.2021-03-31.60days.h5')

        # Get the models predicted price values
        predictions = model.predict(x_test)
        logging.info("Scaled predictions: {}".format(predictions))

        predictions = scaler.inverse_transform(predictions)  # unscale values
        logging.info("Predictions: {}".format(predictions))

        logging.info("Actual values: {}".format(y_test))

        # Get the root mean squared error (RMSE)
        rmse = np.sqrt(np.mean(((predictions - y_test) ** 2)))
        logging.info("RMSE: {}".format(rmse))

        # Plot the data
        train = data[:sample_size]
        # valid = {}
        # valid['Close'] = data[sample_size:-1 * predict_size + 1]
        valid = data.copy()
        valid['Predictions'] = predictions[:, 0]  # if we are predicting 7 out, we only use the first one?
        data.plot()
        predictions.plot()
        # Visualize the data
        plt.figure(figsize=(16, 8))
        plt.title('Model: {}'.format(symbol))
        plt.xlabel('Date', fontsize=18)
        plt.ylabel('Close Price USD ($)', fontsize=18)
        plt.plot(train)
        plt.plot(valid)
        plt.legend(['Train', 'Validation', 'Predictions'], loc='lower right')
        plt.show()

        # Show the valid and predicted prices
        logging.info("Validations and predictions:\n{}".format(valid))

        # Predict the next days closing price
        # Get the quote
        # apple_quote = web.DataReader(symbol, data_source='yahoo', start='2012-01-01', end='2021-03-31')
        # Create new dataframe
        # new_df = data.copy()
        # new_df.pop()  # dispose of todays data (ends at yesterday now)
        # new_df = apple_quote.filter(['Close'])
        # Get the last 60 day closing price values and convert the dataframe to an array

        previous_sample = data[-1 * sample_size - predict_size : -1 * predict_size].values
        # last_sample = new_df[-60:].values
        # Scale the data to be values between 0 and 1
        previous_sample_scaled = scaler.transform(previous_sample)
        # Create an empty list
        X_test = []
        # Append the last 60 days
        X_test.append(previous_sample_scaled)
        # Convert the X_test dataset to a numpy array
        X_test = np.array(X_test)
        # Reshape the data to 3D
        X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))
        # Get the predicted scaled price
        pred_price = model.predict(X_test)
        # Undo scaling
        pred_price = scaler.inverse_transform(pred_price)
        logging.info("Prediction of previous sample price: {}".format(pred_price))

        # apple_quote2 = web.DataReader(symbol, data_source='yahoo', start='2021-04-01', end='2021-04-01')
        # logging.info("Prediction was actually: {}".format(data[:-1 * predict_size]))
        logging.info("Price was actually: {}".format(data[-1 * predict_size:]))

        # Predict tomorrows unknown price
        # Get the quote
        # apple_quote = web.DataReader(symbol, data_source='yahoo', start='2021-01-01', end='2021-04-01')
        # Create new dataframe
        # new_df = data.copy()
        # new_df.pop()  # dispose of todays data
        # new_df = apple_quote.filter(['Close'])
        # Get the last 60 day closing price values and convert the dataframe to an array
        last_sample = data[-1 * sample_size:].values
        # last_sample = new_df[-60:].values
        # Scale the data to be values between 0 and 1
        last_sample_scaled = scaler.transform(last_sample)
        # Create an empty list
        X_test = []
        # Append the last 60 days
        X_test.append(last_sample_scaled)
        # Convert the X_test dataset to a numpy array
        X_test = np.array(X_test)
        # Reshape the data to 3D
        X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))
        # Get the predicted scaled price
        pred_price = model.predict(X_test)
        # Undo scaling
        pred_price = scaler.inverse_transform(pred_price)
        logging.info("Prediction for {} on {}: {}".format(symbol, today.strftime('%Y-%m-%d'), pred_price))

        return success

