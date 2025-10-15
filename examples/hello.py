def hello_world():
    print("Hello, World")
    numbers = [1, 2, 3, 4, 5]
    for num in numbers:
        (lambda x: print(f"Even: {x}") if x % 2 == 0 else print(f"Odd: {x}"))(num)

if __name__ == "__main__":
    hello_world()