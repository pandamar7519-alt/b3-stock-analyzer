# ============================================================================
# IMPORTS COM FALLBACK PARA AMBIENTES RESTRITOS
# ============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import yfinance as yf
import warnings
import traceback

# pandas-ta com fallback elegante
try:
    import pandas_ta as ta
    HAS_PANDAS_TA = True
except ImportError:
    HAS_PANDAS_TA = False
    st.warning("⚠️ pandas-ta não disponível. Indicadores técnicos limitados.")

warnings.filterwarnings("ignore")
