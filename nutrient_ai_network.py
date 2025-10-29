import pandas as pd
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense, Bidirectional
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from logger import get_logger

logger = get_logger()

# --- Глобальные объекты ---
tokenizer = Tokenizer(char_level=False)
model = None
scaler = None
max_len = 0


def obtain_data(path):
    df = pd.read_csv(path, encoding="cp1251", sep=";")
    texts = df['Название'].astype(str).tolist()  # названия блюд
    targets = df[['Калории', 'Жиры', 'Углеводы', 'Белки']].values.astype(float)
    return texts, targets


def predict(input_text: str):
    """Делает предсказание КБЖУ по названию блюда."""
    global model, scaler, tokenizer, max_len

    if model is None or scaler is None:
        raise RuntimeError(f"Error: model is not init")

    try:
        seq = tokenizer.texts_to_sequences([input_text])
        seq_pad = pad_sequences(seq, maxlen=max_len, padding='post')

        pred_scaled = model.predict(seq_pad)
        pred = scaler.inverse_transform(pred_scaled)

        calories, fats, carbs, proteins = pred[0]
        return calories, fats, carbs, proteins

    except Exception as e:
        logger.error(f"Error: {e}")

def init_network():
    """Инициализирует и обучает модель."""
    global model, scaler, tokenizer, max_len

    texts, targets = obtain_data("dishes.csv")

    # Токенизация
    tokenizer.fit_on_texts(texts)
    sequences = tokenizer.texts_to_sequences(texts)
    max_len = max(len(seq) for seq in sequences)
    X = pad_sequences(sequences, maxlen=max_len, padding='post')

    # Масштабирование
    scaler = StandardScaler()
    y = scaler.fit_transform(targets)

    # Разделение
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Архитектура модели
    vocab_size = len(tokenizer.word_index) + 1
    embedding_dim = 50

    model = Sequential([
        Embedding(input_dim=vocab_size, output_dim=embedding_dim, input_length=max_len),
        Bidirectional(LSTM(64, return_sequences=False)),
        Dense(32, activation='relu'),
        Dense(4)  # Калории, жиры, углеводы, белки
    ])

    model.compile(optimizer='adam', loss='mse', metrics=['mae'])

    # Обучение
    model.fit(X_train, y_train, epochs=50, batch_size=32, validation_split=0.1, verbose=1)

    # Оценка
    loss, mae = model.evaluate(X_test, y_test, verbose=0)
    logger.info(f"Test MAE: {mae:.4f}")
    logger.info("Model is built")