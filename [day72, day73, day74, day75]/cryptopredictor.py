import pandas as pd
import os
from collections import deque
from sklearn import preprocessing
import numpy as np
import random
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, LSTM, CuDNNLSTM, BatchNormalization

SEQ_LEN = 60
FUTURE_PREDICT_PERIOD = 3
RATIO_PREDICT_TARGET = "LTC-USD"
EPOCHS = 10
BATCH_SIZE = 64
NAME = f"{SEQ_LEN}-SEQ-{FUTURE_PREDICT_PERIOD}-PRED-{int(time.time())}"


def preprocess_df(df):
    df = df.drop('future', 1)
    for col in df.columns:
        if col != "target":
            df[col] = df[col].pct_change()
            df.dropna(inplace=True)
            df[col] = preprocessing.scale(df[col].values)
    df.dropna(inplace=True)
    seq_data = []
    prev_day = deque(maxlen=SEQ_LEN)
    for i in df.values:
        prev_day.append([n for n in i[:-1]])
        if len(prev_day) == SEQ_LEN:
            seq_data.append([np.array(prev_day), i[-1]])
    random.shuffle(seq_data)

    buys = []
    sells = []

    for seq, target in seq_data:
        if target == 0:
            sells.append([seq, target])
        elif target == 1:
            sells.append([seq, target])

    random.shuffle(buys)
    random.shuffle(sells)

    lower = min(len(buys), len(sells))

    buys = buys[:lower]
    sells = sells[:lower]

    seq_data = buys+sells

    random.shuffle(seq_data)

    X = []
    y = []

    for seq, target in seq_data:
        X.append(seq)
        y.append(target)

    return np.array(X), y


def classify(current, future):
    if float(future > float(current)):
        return 1
    else:
        return 0


df = pd.read_csv("crypto_data/LTC-USD.csv",
                 names=["time", "low", "high", "open", "close", "volume"])

main_df = pd.DataFrame()

ratios = ["BTC-USD", "LTC-USD", "ETH-USD", "BCH-USD"]

for ratio in ratios:
    dataset = f"crypto_data/{ratio}.csv"
    df = pd.read_csv(
        dataset, names=["time", "low", "high", "open", "close", "volume"])
    df.rename(columns={"close": f"{ratio}_close",
                       "volume": f"{ratio}_volume"}, inplace=True)
    df.set_index("time", inplace=True)
    df = df[[f"{ratio}_close", f"{ratio}_volume"]]

    if len(main_df) == 0:
        main_df = df
    else:
        main_df = main_df.join(df)

main_df['future'] = main_df[f"{RATIO_PREDICT_TARGET}_close"].shift(
    -FUTURE_PREDICT_PERIOD)
print(main_df[[f"{RATIO_PREDICT_TARGET}_close", "future"]].head())

main_df['target'] = list(map(
    classify, main_df[f"{RATIO_PREDICT_TARGET}_close"], main_df["future"]))
print(main_df[[f"{RATIO_PREDICT_TARGET}_close", "future", "target"]].head(10))

times = sorted(main_df.index.values)
last_fivepct = times[-int(0.05*len(times))]
print(last_fivepct)

validation_main_df = main_df[(main_df.index >= last_fivepct)]
main_df = main_df[(main_df.index < last_fivepct)]


trainx, trainy = preprocess_df(main_df)
validationx, validationy = preprocess_df(validation_main_df)

print(len(trainx))
print(f"don't buy{trainy.count(0)}")
print(f"don't buy{trainy.count(1)}")
