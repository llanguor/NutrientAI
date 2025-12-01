import pandas as pd
import numpy as np
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Embedding, LSTM, Dense, GlobalAveragePooling1D
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import openpyxl


def train():
    # ------------------------
    # 1. Загрузка данных
    # ------------------------
    df = pd.read_excel("data.xlsx", engine="openpyxl")
    df = df.dropna()  # убираем пустые строки

    # ------------------------
    # 2. Подготовка текста (названия блюд)
    # ------------------------
    MAX_WORDS = 10000  # размер словаря
    MAX_LEN = 10       # максимальная длина последовательности

    tokenizer = Tokenizer(num_words=MAX_WORDS, oov_token="<OOV>")
    tokenizer.fit_on_texts(df['Name'])
    X_seq = tokenizer.texts_to_sequences(df['Name'])
    X_padded = pad_sequences(X_seq, maxlen=MAX_LEN, padding='post')

    # ------------------------
    # 3. Подготовка выходных данных
    # ------------------------
    y = df[['Energy', 'Protein', 'Fat', 'Carb']].values

    # Масштабируем выход (рекомендуется для регрессии)
    scaler = MinMaxScaler()
    y_scaled = scaler.fit_transform(y)

    # ------------------------
    # 4. Разделяем данные на train/test
    # ------------------------
    X_train, X_test, y_train, y_test = train_test_split(X_padded, y_scaled, test_size=0.1, random_state=42)

    # ------------------------
    # 5. Строим модель
    # ------------------------
    input_layer = Input(shape=(MAX_LEN,))
    x = Embedding(input_dim=MAX_WORDS, output_dim=64, input_length=MAX_LEN)(input_layer)
    x = LSTM(64, return_sequences=True)(x)
    x = GlobalAveragePooling1D()(x)
    x = Dense(64, activation='relu')(x)
    output_layer = Dense(4, activation='linear')(x)  # 4 выхода: Energy, Protein, Fats, Carbs

    model = Model(inputs=input_layer, outputs=output_layer)
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])

    model.summary()

    # ------------------------
    # 6. Обучение
    # ------------------------
    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=30,
        batch_size=32
    )

    # ------------------------
    # 7. Сохранение модели
    # ------------------------
    model.save("kbju_model.keras")

train()