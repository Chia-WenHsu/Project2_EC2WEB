response_cache = {}

# 多執行緒之間的同步鎖
import threading
response_cache_lock = threading.Lock()