#from nutrient_ai_network_training import train
import nutrient_ai_network
from nutrient_ai_bot import start_bot_thread
from logger import get_logger

try:
    start_bot_thread()
except Exception as e:
    get_logger().error(f"Error: {e}")

