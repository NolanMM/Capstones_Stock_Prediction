import os
import sys
import io
import pytest
import pandas as pd
import numpy as np
import torch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from currentModels.test_pipeline_code import (
    compute_indicators,
    prepare_data_quarterly_minmax,
    fetch_all_history_fmp,
    fetch_from_sql,
    LSTMModel,
    EarlyStopping,
    train_lstm
)


def test_compute_indicators_output_columns():
    dates = pd.date_range('2020-01-01', periods=50, freq='D')
    df = pd.DataFrame({
        'Open': np.arange(50)+1,
        'High': np.arange(50)+2,
        'Low': np.arange(50),
        'Close': np.arange(50)+0.5,
        'Volume': np.ones(50)
    }, index=dates)
    out = compute_indicators(df)
    expected = [
        'Return_1D', 'Return_3D_past', 'Volatility_3D_past',
        'RSI', 'MACD', 'MACD_Signal', 'MACD_Hist',
        'BB_Mid', 'BB_Upper', 'BB_Lower'
    ]
    for col in expected:
        assert col in out.columns
    assert not out.isna().any().any()


def test_compute_indicators_length_reduced():
    dates = pd.date_range('2020-01-01', periods=25, freq='D')
    df = pd.DataFrame({
        'Open': range(25),
        'High': range(25),
        'Low': range(25),
        'Close': range(25),
        'Volume': np.ones(25)
    }, index=dates)
    out = compute_indicators(df)
    assert 0 < len(out) < len(df)


def test_prepare_data_quarterly_empty():
    dates = pd.date_range('2020-01-01', periods=5, freq='D')
    df = pd.DataFrame({'feat1': range(5), 'Return_1D': range(5)}, index=dates)
    X, y, scalers, df_s = prepare_data_quarterly(df, ['feat1'], 'Return_1D', window=10)
    assert X.size == 0
    assert y.size == 0
    assert scalers == {}
    assert df_s.empty


def test_prepare_data_quarterly_shapes():
    np.random.seed(0)
    dates = pd.date_range('2020-01-01', periods=30, freq='D')
    df = pd.DataFrame({
        'feat1': np.random.rand(30),
        'feat2': np.random.rand(30),
        'Return_1D': np.random.rand(30)
    }, index=dates)
    feats, tgt, window = ['feat1','feat2'], 'Return_1D', 5
    X, y, scalers, df_s = prepare_data_quarterly(df, feats, tgt, window)
    assert X.shape[0] == df_s.shape[0] - window
    assert X.shape[1:] == (window, len(feats))
    assert y.shape[0] == X.shape[0]
    assert isinstance(scalers, dict) and len(scalers) > 0


def test_fetch_all_history_fmp_no_data(monkeypatch):
    class Dummy:
        def json(self): return {'historical': []}
        def raise_for_status(self): pass
    monkeypatch.setattr('pipeline.requests.get', lambda *a,**k: Dummy())
    df = fetch_all_history_fmp('XYZ','key')
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_fetch_all_history_fmp_simple(monkeypatch):
    hist = [{'date':'2021-01-01','open':1,'high':1,'low':1,'close':1,'volume':1}]
    calls = [hist, []]
    class Dummy:
        def json(self):
            return {'historical': calls.pop(0)}
        def raise_for_status(self): pass
    monkeypatch.setattr('pipeline.requests.get', lambda *a,**k: Dummy())
    df = fetch_all_history_fmp('ABC','key')
    assert len(df) == 1
    for col in ('open','high','low','close','volume','Return_1D','Return_3D','Volatility_3D'):
        assert col in df.columns


def test_fetch_from_sql_error(monkeypatch):
    monkeypatch.setattr('pipeline.pyodbc.connect',
                        lambda *a,**k: (_ for _ in ()).throw(Exception('fail')))
    df = fetch_from_sql('conn','tbl','SYM',100)
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_fetch_from_sql_success(monkeypatch):
    # simulate pd.read_sql returning a small DataFrame
    content = 'date,open,high,low,close,volume\n2021-01-01,1,2,3,4,5'
    df_dummy = pd.read_csv(io.StringIO(content), parse_dates=['date'])
    monkeypatch.setattr('pipeline.pd.read_sql', lambda sql,cn,params: df_dummy)
    class C: 
        def close(self): pass
    monkeypatch.setattr('pipeline.pyodbc.connect', lambda *a,**k: C())
    df = fetch_from_sql('conn','Silver.Historical_Prices','AAPL',1)
    assert not df.empty
    assert list(df.columns) == ['date','open','high','low','close','volume']


def test_early_stopping_triggers():
    es = EarlyStopping(patience=2, min_delta=0)
    es(1.0); assert not es.stop
    es(0.9); assert not es.stop
    es(0.9); assert es.stop


def test_lstmmodel_forward_shape():
    model = LSTMModel(inp=3, hid=4, nl=1, do=0)
    x = torch.rand(2,5,3)
    y = model(x)
    assert y.shape == (2,)


def test_train_lstm_smoke():
    X = np.random.rand(20,5,2).astype(np.float32)
    y = np.random.rand(20).astype(np.float32)
    model = train_lstm(
        X, y,
        hid=5, nl=1, do=0.1,
        lr=1e-3, wd=1e-4,
        bs=4, epochs=5, patience=2
    )
    assert isinstance(model, LSTMModel)


def test_sliding_window_monotonic():
    dates = pd.date_range('2020-01-01', periods=10)
    df = pd.DataFrame({'feat': range(10), 'Return_1D': range(10)}, index=dates)
    X, y, _, df_s = prepare_data_quarterly(df, ['feat'], 'Return_1D', window=3)
    # first window should be [0,1,2]
    assert (X[0].flatten() == np.array([0,1,2])).all()


def test_no_nan_in_X_y():
    dates = pd.date_range('2020-01-01', periods=15)
    df = pd.DataFrame({'feat': np.arange(15), 'Return_1D': np.arange(15)}, index=dates)
    X, y, _, df_s = prepare_data_quarterly(df, ['feat'], 'Return_1D', window=5)
    assert not np.isnan(X).any()
    assert not np.isnan(y).any()


def test_fetch_all_history_date_parsing(monkeypatch):
    hist = [{'date':'2021-12-31','open':1,'high':1,'low':1,'close':1,'volume':1}]
    class D:
        def json(self): return {'historical': hist}
        def raise_for_status(self): pass
    monkeypatch.setattr('pipeline.requests.get', lambda *a,**k: D())
    df = fetch_all_history_fmp('ANY','key')
    assert np.issubdtype(df['date'].dtype, np.datetime64)


def test_pipeline_imports():
    import pipeline
    assert hasattr(pipeline, 'compute_indicators')


def test_train_lstm_early_stop():
    X = np.ones((20,5,2), dtype=np.float32)
    y = np.ones(20, dtype=np.float32)
    model = train_lstm(
        X, y,
        hid=3, nl=1, do=0.1,
        lr=1e-3, wd=1e-4,
        bs=4, epochs=50, patience=1
    )
    assert isinstance(model, LSTMModel)


def test_prepare_data_single_quarter():
    dates = pd.date_range('2021-01-01', periods=12, freq='D')
    df = pd.DataFrame({'feat': np.arange(12), 'Return_1D': np.arange(12)}, index=dates)
    X, y, scalers, df_s = prepare_data_quarterly(df, ['feat'], 'Return_1D', window=10)
    assert len(scalers) == 1
    assert X.shape[0] == df_s.shape[0] - 10


def test_lstmmodel_parameters_trainable():
    model = LSTMModel(inp=2, hid=3, nl=2, do=0.5)
    params = list(model.parameters())
    assert any(p.requires_grad for p in params)


def test_compute_indicators_input_unchanged():
    dates = pd.date_range('2020-01-01', periods=10)
    df = pd.DataFrame({
        'Open': range(10),
        'High': range(10),
        'Low': range(10),
        'Close': range(10),
        'Volume': range(10)
    }, index=dates)
    before = df.copy()
    _ = compute_indicators(df)
    pd.testing.assert_frame_equal(df, before)
