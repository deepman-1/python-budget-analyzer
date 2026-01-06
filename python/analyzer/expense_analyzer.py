import csv
from collections import defaultdict

def analyze_expenses(file_path):
    totals = defaultdict(float)

    with open(file_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row["category"]
            amt = float(row["amount"])
            totals[cat] += amt

    return totals

def print_summary(totals):
    print("\nExpense Summary")
    print("--------------------")
    total_expenses = sum(totals.values())
    print(f"Total spent: {total_expenses:.2f}\n")
    
    for category, amount in totals.items():
        print(f"{category}: {amount:.2f}")

def main():
    path = input("Enter the path to your expense CSV file: ")
    try:
        totals = analyze_expenses(path)
        print_summary(totals)
    except FileNotFoundError:
        print("File not found — please check the path and try again.")
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()
