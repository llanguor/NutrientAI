import pandas as pd
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense, Bidirectional
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

tokenizer = Tokenizer(char_level=False)

def obtain_data(path):
    df = pd.read_csv("dishes.csv", encoding="cp1251", sep=";")  # твой CSV
    texts = df['Название'].astype(str).tolist()  # названия блюд
    targets = df[['Калории', 'Жиры', 'Углеводы', 'Белки']].values.astype(float)  # КБЖУ
    return texts, targets

def predict(input):
    # Подготовка текста
    example = [input]
    seq = tokenizer.texts_to_sequences(example)
    seq_pad = pad_sequences(seq, maxlen=max_len, padding='post')

    # Предсказание КБЖУ
    pred_scaled = model.predict(seq_pad)
    pred = scaler.inverse_transform(pred_scaled)

    # Возврат результата
    calories, fats, carbs, proteins = pred[0]
    return calories, fats, carbs, proteins


#Получаем данные из таблиц
texts, targets = obtain_data("dishes.csv")

#Токенизируем текст
tokenizer.fit_on_texts(texts)
sequences = tokenizer.texts_to_sequences(texts)
max_len = max(len(seq) for seq in sequences)
X = pad_sequences(sequences, maxlen=max_len, padding='post')

#Масштабируем
scaler = StandardScaler()
y = scaler.fit_transform(targets)

#Разделяем на тренировочные и тестовые данные
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

#Строим модель
vocab_size = len(tokenizer.word_index) + 1
embedding_dim = 50

model = Sequential([
    Embedding(input_dim=vocab_size, output_dim=embedding_dim, input_length=max_len),
    Bidirectional(LSTM(64, return_sequences=False)),
    Dense(32, activation='relu'),
    Dense(4)  # 4 выхода: proteins, fats, carbs
])

model.compile(optimizer='adam', loss='mse', metrics=['mae'])

#Обучаем модель
model.fit(X_train, y_train, epochs=50, batch_size=32, validation_split=0.1)

#Оценка на тесте
loss, mae = model.evaluate(X_test, y_test)
print("Test MAE:", mae)


