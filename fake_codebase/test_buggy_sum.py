from buggy_sum import buggy_sum


def test_buggy_sum():
    # expected output: 1 + 2 + 3 = 6
    result = buggy_sum([1, 2, 3])
    assert result == 6, f"Expected 6 but got {result}"
