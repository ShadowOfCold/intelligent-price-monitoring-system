from backend.services.report_service import safe_filename


def test_safe_filename_removes_invalid_symbols():
    result = safe_filename('Отчёт: товар / тест?')

    assert ":" not in result
    assert "/" not in result
    assert "?" not in result
    assert " " not in result