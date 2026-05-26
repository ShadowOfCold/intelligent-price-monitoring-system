import numpy as np

from backend.services.forecast_service import calculate_mape, create_sequences


def test_create_sequences():
    data = np.array([[1], [2], [3], [4], [5]])
    x, y = create_sequences(data, window_size=2)

    assert len(x) == 3
    assert len(y) == 3

    assert x[0].tolist() == [[1], [2]]
    assert y[0].tolist() == [3]


def test_calculate_mape():
    y_true = np.array([100, 200, 300])
    y_pred = np.array([110, 190, 330])

    result = calculate_mape(y_true, y_pred)

    assert round(result, 2) == 8.33


def test_calculate_mape_with_zero_values():
    y_true = np.array([0, 100])
    y_pred = np.array([50, 110])

    result = calculate_mape(y_true, y_pred)

    assert round(result, 2) == 10.0