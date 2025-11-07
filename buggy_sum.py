def buggy_sum(numbers):
    total = 0
    for i in range(1, len(numbers)):  # ❌ off-by-one, skips first element
        total += numbers[i]
    return total


if __name__ == "__main__":
    nums = [1, 2, 3]
    print("Sum is:", buggy_sum(nums))

