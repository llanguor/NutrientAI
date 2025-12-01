import pandas as pd
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense, Bidirectional
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import load_model
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler
from logger import get_logger

logger = get_logger()

# --- Глобальные объекты ---
# Загрузка модели
model = load_model("kbju_model.keras")

# Загрузка данных для инициализации tokenizer и scaler
df = pd.read_excel("data.xlsx", engine="openpyxl")
df = df.dropna()  # убираем пустые строки
df.columns = df.columns.str.strip()

# Инициализация tokenizer
max_words = 10000
max_len = 10
tokenizer = Tokenizer(num_words=max_words, oov_token="<OOV>")
tokenizer.fit_on_texts(df['Name'])

# Инициализация scaler
y = df[['Energy', 'Protein', 'Fat', 'Carb']].values
scaler = MinMaxScaler()
scaler.fit(y)

def obtain_data(path):
    df = pd.read_csv(path, encoding="cp1251", sep=";")
    texts = df['Название'].astype(str).tolist()  # названия блюд
    targets = df[['Energy', 'Fat', 'Carb', 'Protein']].values.astype(float)
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
