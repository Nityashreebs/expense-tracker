import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate

class ExpenseTracker:
    def __init__(self):
        # Initialize the database
        self.conn = sqlite3.connect('expenses.db')
        self.create_tables()
        
    def create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                date TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        self.conn.commit()
        
        # Insert default categories if none exist
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            default_categories = [
                'Food', 'Transportation', 'Housing', 'Entertainment',
                'Utilities', 'Healthcare', 'Education', 'Shopping', 'Other'
            ]
            cursor.executemany("INSERT INTO categories (name) VALUES (?)", 
                             [(cat,) for cat in default_categories])
            self.conn.commit()

    def add_expense(self, amount, category, description=""):
        """Add a new expense to the database"""
        try:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)",
                (amount, category, description, date)
            )
            self.conn.commit()
            print(f"✅ Added expense: ${amount:.2f} for {category}")
        except sqlite3.Error as e:
            print(f"Error adding expense: {e}")

    def view_expenses(self, time_period="all"):
        """View expenses based on time period (day/week/month/all)"""
        cursor = self.conn.cursor()
        
        # Determine date range based on time period
        current_date = datetime.now()
        date_format = "%Y-%m-%d %H:%M:%S"
        
        if time_period == "day":
            start_date = current_date.replace(hour=0, minute=0, second=0).strftime(date_format)
            end_date = current_date.strftime(date_format)
            query = """SELECT * FROM expenses 
                       WHERE date BETWEEN ? AND ? 
                       ORDER BY date DESC"""
            cursor.execute(query, (start_date, end_date))
        elif time_period == "week":
            start_date = (current_date - pd.DateOffset(days=7)).strftime(date_format)
            end_date = current_date.strftime(date_format)
            query = """SELECT * FROM expenses 
                       WHERE date BETWEEN ? AND ? 
                       ORDER BY date DESC"""
            cursor.execute(query, (start_date, end_date))
        elif time_period == "month":
            start_date = (current_date - pd.DateOffset(days=30)).strftime(date_format)
            end_date = current_date.strftime(date_format)
            query = """SELECT * FROM expenses 
                       WHERE date BETWEEN ? AND ? 
                       ORDER BY date DESC"""
            cursor.execute(query, (start_date, end_date))
        else:  # all
            cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
        
        expenses = cursor.fetchall()
        
        if not expenses:
            print("No expenses found.")
            return
            
        # Display expenses in a formatted table
        columns = ["ID", "Amount", "Category", "Description", "Date"]
        print("\n" + tabulate(expenses, headers=columns, tablefmt="grid", floatfmt=".2f"))
        
        # Show total amount
        total = sum(expense[1] for expense in expenses)
        print(f"\nTotal: ${total:.2f}")

    def get_spending_by_category(self):
        """Get spending breakdown by category"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT category, SUM(amount) as total 
            FROM expenses 
            GROUP BY category 
            ORDER BY total DESC
        ''')
        results = cursor.fetchall()
        
        if not results:
            print("No spending data available.")
            return None
            
        return results

    def generate_report(self):
        """Generate a visual spending report"""
        spending_data = self.get_spending_by_category()
        if not spending_data:
            return
            
        categories = [item[0] for item in spending_data]
        amounts = [item[1] for item in spending_data]
        
        plt.figure(figsize=(10, 6))
        plt.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=140)
        plt.title("Spending by Category")
        plt.show()

    def add_category(self, category_name):
        """Add a new expense category"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
            self.conn.commit()
            print(f"✅ Added new category: {category_name}")
        except sqlite3.IntegrityError:
            print("⚠️ Category already exists")
        except sqlite3.Error as e:
            print(f"Error adding category: {e}")

    def get_categories(self):
        """Get list of all categories"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM categories ORDER BY name")
        return [cat[0] for cat in cursor.fetchall()]

    def __del__(self):
        """Close the database connection when done"""
        self.conn.close()


def main_menu():
    """Display the main menu and handle user input"""
    tracker = ExpenseTracker()
    
    while True:
        print("\n💵 Personal Expense Tracker")
        print("1. ➕ Add Expense")
        print("2. 👀 View Expenses")
        print("3. 📊 View Spending Report")
        print("4. 🗂️ Add New Category")
        print("5. 🚪 Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == "1":
            try:
                amount = float(input("Enter amount: $"))
                categories = tracker.get_categories()
                print("\nAvailable categories:")
                for i, cat in enumerate(categories, 1):
                    print(f"{i}. {cat}")
                
                cat_choice = input("\nSelect category by number or enter new category: ")
                
                try:
                    # If user entered a number
                    cat_index = int(cat_choice) - 1
                    if 0 <= cat_index < len(categories):
                        category = categories[cat_index]
                    else:
                        raise ValueError("Invalid number")
                except ValueError:
                    # If user entered text (new category)
                    category = cat_choice.strip()
                    tracker.add_category(category)
                
                description = input("Enter description (optional): ")
                tracker.add_expense(amount, category, description)
                
            except ValueError:
                print("⚠️ Invalid input. Please enter a valid amount.")
                
        elif choice == "2":
            print("\nView expenses for:")
            print("1. Today")
            print("2. This Week")
            print("3. This Month")
            print("4. All Time")
            
            period_choice = input("\nEnter your choice (1-4): ")
            
            periods = {"1": "day", "2": "week", "3": "month", "4": "all"}
            selected_period = periods.get(period_choice, "all")
            tracker.view_expenses(selected_period)
            
        elif choice == "3":
            tracker.generate_report()
            
        elif choice == "4":
            new_category = input("Enter new category name: ").strip()
            tracker.add_category(new_category)
            
        elif choice == "5":
            print("👋 Goodbye!")
            break
            
        else:
            print("⚠️ Invalid choice. Please try again.")


if __name__ == "__main__":
    main_menu()
