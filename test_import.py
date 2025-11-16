import sys
import os

print("--- sys.path ---")
for path in sys.path:
    print(path)
print("-" * 16)

try:
    # 嘗試匯入上層模組
    import scipy.stats.qmc
    print("Successfully imported scipy.stats.qmc")

    # 嘗試匯入目標類別
    from scipy.stats.qmc import LatinHypercube
    print("Successfully imported LatinHypercube")

    # 檢查 scipy 的安裝路徑
    import scipy
    print(f"SciPy installed at: {os.path.dirname(scipy.__file__)}")

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")