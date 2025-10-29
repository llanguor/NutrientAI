from nutrition_network import predict

calories, fats, carbs, proteins = predict("kek")
print("Результат предсказания:")
print(f"{calories:.0}, {fats:.0}, {carbs:.0}, {proteins:.0}")
