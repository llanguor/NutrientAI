from nutrient_ai_bot import start_bot_thread
from nutrient_ai_network import init_network
from logger import get_logger

try:
    init_network()
    start_bot_thread()
except Exception as e:
    get_logger().error(f"Error: {e}")

