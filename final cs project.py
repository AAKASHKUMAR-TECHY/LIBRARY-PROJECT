import mysql.connector as mysq
import hashlib
import datetime
import re

# Global connection variable
db_conn = None

def connect_db():
    """Connect to database"""
    global db_conn
    try:
        db_conn = mysq.connect(
            host='localhost',
            user='root',
            password='Ammu@2611',
            database='library'
        )
        print("Connected to database!")
        return True
    except mysq.Error as e:
        print(f"Database connection failed: {e}")
        return False

def hash_password(pwd):
    """Hash password"""
    return hashlib.sha256(pwd.encode()).hexdigest()

def check_email(email):
    """Check email format"""
    pattern = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
    return re.match(pattern, email) is not None

def setup_database():
    """Make sure all tables exist"""
    try:
        cursor = db_conn.cursor()
        
        # Check if tables are there
        tables = ['students', 'admins', 'books_available', 'books_borrowed', 'borrowed_history']
        for table in tables:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            if not cursor.fetchone():
                print(f"Missing table: {table}")
                return False
        
        # Check superadmin account
        cursor.execute("SELECT password FROM admins WHERE username = 'superadmin'")
        result = cursor.fetchone()
        
        if not result:
            # Create superadmin if missing
            hashed_pwd = hash_password("admin123")
            cursor.execute(
                "INSERT INTO admins (username, password, admin_level, created_by) VALUES (%s, %s, 'superadmin', 'system')",
                ("superadmin", hashed_pwd)
            )
            db_conn.commit()
            print("Created superadmin account")
        else:
            # Fix password if wrong
            correct_hash = hash_password("admin123")
            if result[0] != correct_hash:
                cursor.execute(
                    "UPDATE admins SET password = %s WHERE username = 'superadmin'",
                    (correct_hash,)
                )
                db_conn.commit()
                print("Fixed superadmin password")
        
        print("Database ready!")
        return True
        
    except Exception as e:
        print(f"Database setup error: {e}")
        return False

def student_register():
    """Student sign up"""
    try:
        print("\n" + "="*40)
        print("Student Sign Up")
        print("="*40)
        
        username = input("Username: ").strip()
        if not username:
            print("Username needed!")
            return None
        
        cursor = db_conn.cursor()
        
        # Check if username taken
        cursor.execute("SELECT username FROM students WHERE username = %s", (username,))
        if cursor.fetchone():
            print("Username taken!")
            return None
        
        cursor.execute("SELECT username FROM admins WHERE username = %s", (username,))
        if cursor.fetchone():
            print("Username taken by admin!")
            return None
        
        password = input("Password: ").strip()
        if len(password) < 4:
            print("Password too short!")
            return None
        
        email = input("Email: ").strip()
        if not check_email(email):
            print("Email not valid!")
            return None
        
        full_name = input("Full name: ").strip()
        if not full_name:
            print("Name needed!")
            return None
        
        # Create account
        hashed_pwd = hash_password(password)
        cursor.execute(
            "INSERT INTO students (username, password, email, full_name) VALUES (%s, %s, %s, %s)",
            (username, hashed_pwd, email, full_name)
        )
        db_conn.commit()
        
        print("Account created!")
        return username
        
    except Exception as e:
        print(f"Sign up error: {e}")
        return None

def student_login():
    """Student log in"""
    try:
        print("\n" + "="*40)
        print("Student Login")
        print("="*40)
        
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        
        hashed_pwd = hash_password(password)
        cursor = db_conn.cursor()
        
        cursor.execute(
            "SELECT username, full_name FROM students WHERE username = %s AND password = %s",
            (username, hashed_pwd)
        )
        student = cursor.fetchone()
        
        if student:
            print(f"Welcome {student[1]}!")
            return student[0]
        else:
            print("Wrong username or password!")
            return None
            
    except Exception as e:
        print(f"Login error: {e}")
        return None

def admin_login():
    """Admin log in"""
    try:
        print("\n" + "="*40)
        print("Admin Login")
        print("="*40)
        
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        
        hashed_pwd = hash_password(password)
        cursor = db_conn.cursor()
        
        cursor.execute(
            "SELECT username, admin_level FROM admins WHERE username = %s AND password = %s",
            (username, hashed_pwd)
        )
        admin = cursor.fetchone()
        
        if admin:
            print(f"Welcome {admin[0]} ({admin[1]})!")
            return admin[0], admin[1]
        else:
            print("Wrong admin credentials!")
            return None, None
            
    except Exception as e:
        print(f"Admin login error: {e}")
        return None, None

def is_super_admin(username):
    """Check if super admin"""
    cursor = db_conn.cursor()
    cursor.execute("SELECT admin_level FROM admins WHERE username = %s", (username,))
    result = cursor.fetchone()
    return result and result[0] == 'superadmin'

def create_librarian(current_admin):
    """Create librarian account"""
    try:
        if not is_super_admin(current_admin):
            print("Only super admin can do this!")
            return False
        
        print("\n" + "="*40)
        print("Create Librarian")
        print("="*40)
        
        username = input("New librarian username: ").strip()
        if not username:
            print("Username needed!")
            return False
        
        cursor = db_conn.cursor()
        
        # Check if username exists
        cursor.execute("SELECT username FROM students WHERE username = %s", (username,))
        if cursor.fetchone():
            print("Username taken by student!")
            return False
        
        cursor.execute("SELECT username FROM admins WHERE username = %s", (username,))
        if cursor.fetchone():
            print("Username taken by admin!")
            return False
        
        password = input("Password: ").strip()
        if len(password) < 4:
            print("Password too short!")
            return False
        
        # Create account
        hashed_pwd = hash_password(password)
        cursor.execute(
            "INSERT INTO admins (username, password, admin_level, created_by) VALUES (%s, %s, 'librarian', %s)",
            (username, hashed_pwd, current_admin)
        )
        db_conn.commit()
        
        print(f"Librarian {username} created!")
        return True
        
    except Exception as e:
        print(f"Create librarian error: {e}")
        return False

def add_new_book():
    """Add book to library"""
    try:
        print("\n" + "="*40)
        print("Add Book")
        print("="*40)
        
        book_id = int(input("Book ID: "))
        name = input("Book name: ").strip()
        author = input("Author: ").strip()
        year = int(input("Year: "))
        genre = input("Genre: ").strip()
        copies = int(input("Copies: "))
        
        if copies < 0:
            print("Can't have negative copies!")
            return
        
        cursor = db_conn.cursor()
        
        # Check if book ID exists
        cursor.execute("SELECT bookid FROM books_available WHERE bookid = %s", (book_id,))
        if cursor.fetchone():
            print("Book ID already used!")
            return
        
        cursor.execute(
            "INSERT INTO books_available (bookid, book_name, author_name, year_of_publication, genre, availability) VALUES (%s, %s, %s, %s, %s, %s)",
            (book_id, name, author, year, genre, copies)
        )
        db_conn.commit()
        
        print("Book added!")
        
    except ValueError:
        print("Please enter numbers where needed!")
    except Exception as e:
        print(f"Add book error: {e}")

def find_books():
    """Search for books"""
    try:
        print("\n" + "="*40)
        print("Find Books")
        print("="*40)
        print("1. By Name")
        print("2. By Author") 
        print("3. By Genre")
        print("4. By Year")
        print("5. Show All")
        
        choice = input("Choose (1-5): ").strip()
        
        cursor = db_conn.cursor()
        sql = "SELECT * FROM books_available WHERE availability > 0"
        params = []
        
        if choice == '1':
            name = input("Book name: ").strip()
            sql += " AND book_name LIKE %s"
            params.append(f"%{name}%")
        elif choice == '2':
            author = input("Author: ").strip()
            sql += " AND author_name LIKE %s"
            params.append(f"%{author}%")
        elif choice == '3':
            genre = input("Genre: ").strip()
            sql += " AND genre LIKE %s"
            params.append(f"%{genre}%")
        elif choice == '4':
            year = int(input("Year: "))
            sql += " AND year_of_publication = %s"
            params.append(year)
        elif choice == '5':
            # Show all books
            pass
        else:
            print("Wrong choice!")
            return
        
        cursor.execute(sql, params)
        books = cursor.fetchall()
        
        if books:
            print(f"\nFound {len(books)} book(s):")
            print("-" * 70)
            print(f"{'ID':<5} {'Name':<20} {'Author':<15} {'Year':<6} {'Genre':<12} {'Avail':<8}")
            print("-" * 70)
            for book in books:
                print(f"{book[0]:<5} {book[1]:<20} {book[2]:<15} {book[3]:<6} {book[4]:<12} {book[5]:<8}")
        else:
            print("No books found!")
            
    except ValueError:
        print("Year should be a number!")
    except Exception as e:
        print(f"Search error: {e}")

def borrow_book(student_name):
    """Borrow books"""
    try:
        print("\n" + "="*40)
        print("Borrow Book")
        print("="*40)
        
        book_id = int(input("Book ID: "))
        count = int(input("How many: "))
        
        if count <= 0:
            print("Must borrow at least 1!")
            return
        
        cursor = db_conn.cursor()
        
        # Check if book exists
        cursor.execute("SELECT * FROM books_available WHERE bookid = %s", (book_id,))
        book = cursor.fetchone()
        
        if not book:
            print("Book not found!")
            return
        
        if book[5] < count:
            print(f"Only {book[5]} available!")
            return
        
        # Set due date (2 weeks)
        due_date = datetime.datetime.now() + datetime.timedelta(days=14)
        
        # Borrow book
        cursor.execute(
            "INSERT INTO books_borrowed (bookid, book_name, author_name, year_of_publication, genre, count, user, due_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (book[0], book[1], book[2], book[3], book[4], count, student_name, due_date)
        )
        
        cursor.execute(
            "INSERT INTO borrowed_history (bookid, book_name, author_name, year_of_publication, genre, count, user) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (book[0], book[1], book[2], book[3], book[4], count, student_name)
        )
        
        # Update available count
        cursor.execute(
            "UPDATE books_available SET availability = availability - %s WHERE bookid = %s",
            (count, book_id)
        )
        
        db_conn.commit()
        
        print(f"Borrowed {count} of '{book[1]}'")
        print(f"Due: {due_date.strftime('%Y-%m-%d')}")
        
    except ValueError:
        print("Please enter numbers!")
    except Exception as e:
        print(f"Borrow error: {e}")

def return_book(student_name):
    """Return borrowed books"""
    try:
        print("\n" + "="*40)
        print("Return Book")
        print("="*40)
        
        book_id = int(input("Book ID: "))
        count = int(input("How many: "))
        
        if count <= 0:
            print("Must return at least 1!")
            return
        
        cursor = db_conn.cursor()
        
        # Check if student borrowed this
        cursor.execute(
            "SELECT * FROM books_borrowed WHERE bookid = %s AND user = %s",
            (book_id, student_name)
        )
        borrowed = cursor.fetchone()
        
        if not borrowed:
            print("You didn't borrow this book!")
            return
        
        # Update history
        cursor.execute(
            "UPDATE borrowed_history SET returned_date = NOW(), status = 'returned' WHERE bookid = %s AND user = %s AND status = 'borrowed'",
            (book_id, student_name)
        )
        
        # Update available count
        cursor.execute(
            "UPDATE books_available SET availability = availability + %s WHERE bookid = %s",
            (count, book_id)
        )
        
        # Remove from borrowed list
        cursor.execute(
            "DELETE FROM books_borrowed WHERE bookid = %s AND user = %s",
            (book_id, student_name)
        )
        
        db_conn.commit()
        
        print(f"Returned {count} books!")
        
    except ValueError:
        print("Please enter numbers!")
    except Exception as e:
        print(f"Return error: {e}")
def show_history(username=None, admin_view=False):
    """Show borrowing history"""
    try:
        cursor = db_conn.cursor()
        
        if admin_view:
            cursor.execute("SELECT * FROM borrowed_history ORDER BY borrowed_date DESC")
            title = "All History"
        else:
            cursor.execute(
                "SELECT * FROM borrowed_history WHERE user = %s ORDER BY borrowed_date DESC",
                (username,)
            )
            title = f"History for {username}"
        
        records = cursor.fetchall()
        
        if records:
            print(f"\n{title}")
            print("-" * 90)
            print(f"{'Book':<20} {'Author':<15} {'User':<12} {'Borrowed':<12} {'Returned':<12} {'Status':<10}")
            print("-" * 90)
            
            for record in records:
                # Let's handle the record more safely
                try:
                    # Try to find the right columns by name if possible
                    cursor.execute("SHOW COLUMNS FROM borrowed_history")
                    columns = [col[0] for col in cursor.fetchall()]
                    
                    # Create a dictionary of column names to values
                    record_dict = dict(zip(columns, record))
                    
                    book_name = record_dict.get('book_name', 'Unknown')
                    author_name = record_dict.get('author_name', 'Unknown')
                    user = record_dict.get('user', 'Unknown')
                    borrowed_date = record_dict.get('borrowed_date')
                    returned_date = record_dict.get('returned_date')
                    status = record_dict.get('status', 'Unknown')
                    
                    # Format dates
                    borrowed_str = borrowed_date.strftime('%Y-%m-%d') if borrowed_date else "Unknown"
                    returned_str = returned_date.strftime('%Y-%m-%d') if returned_date else "Not yet"
                    
                    print(f"{book_name:<20} {author_name:<15} {user:<12} {borrowed_str:<12} {returned_str:<12} {status:<10}")
                    
                except Exception as record_error:
                    print(f"Error processing record: {record_error}")
                    continue
                    
        else:
            print("No history found!")
            
    except Exception as e:
        print(f"History error: {e}")
def remove_book():
    """Remove book from library"""
    try:
        print("\n" + "="*40)
        print("Remove Book")
        print("="*40)
        
        book_id = int(input("Book ID to remove: "))
        
        cursor = db_conn.cursor()
        
        # Check if book exists
        cursor.execute("SELECT * FROM books_available WHERE bookid = %s", (book_id,))
        if not cursor.fetchone():
            print("Book not found!")
            return
        
        # Check if book is borrowed
        cursor.execute("SELECT * FROM books_borrowed WHERE bookid = %s", (book_id,))
        if cursor.fetchone():
            print("Book is borrowed, can't remove!")
            return
        
        cursor.execute("DELETE FROM books_available WHERE bookid = %s", (book_id,))
        db_conn.commit()
        
        print("Book removed!")
        
    except ValueError:
        print("Book ID should be a number!")
    except Exception as e:
        print(f"Remove book error: {e}")

def show_admins():
    """Show all admin accounts"""
    try:
        cursor = db_conn.cursor()
        cursor.execute("SELECT username, admin_level, created_by, created_at FROM admins ORDER BY created_at")
        admins = cursor.fetchall()
        
        if admins:
            print("\n" + "="*40)
            print("All Admins")
            print("="*40)
            print(f"{'User':<12} {'Level':<10} {'Created By':<12} {'Date':<10}")
            print("-" * 50)
            for admin in admins:
                date = admin[3].strftime('%Y-%m-%d')
                print(f"{admin[0]:<12} {admin[1]:<10} {admin[2]:<12} {date:<10}")
        else:
            print("No admins found!")
            
    except Exception as e:
        print(f"Show admins error: {e}")

def student_screen(username):
    """Student menu"""
    while True:
        print("\n" + "="*40)
        print(f"Student: {username}")
        print("="*40)
        print("1. Find Books")
        print("2. Borrow Book") 
        print("3. Return Book")
        print("4. My History")
        print("5. Logout")
        
        choice = input("Choose (1-5): ").strip()
        
        if choice == '1':
            find_books()
        elif choice == '2':
            borrow_book(username)
        elif choice == '3':
            return_book(username)
        elif choice == '4':
            show_history(username)
        elif choice == '5':
            print("Logged out!")
            break
        else:
            print("Wrong choice!")

def librarian_screen(username):
    """Librarian menu"""
    while True:
        print("\n" + "="*40)
        print(f"Librarian: {username}")
        print("="*40)
        print("1. Add Book")
        print("2. Remove Book")
        print("3. Find Books")
        print("4. View History")
        print("5. Logout")
        
        choice = input("Choose (1-5): ").strip()
        
        if choice == '1':
            add_new_book()
        elif choice == '2':
            remove_book()
        elif choice == '3':
            find_books()
        elif choice == '4':
            show_history(admin_view=True)
        elif choice == '5':
            print("Logged out!")
            break
        else:
            print("Wrong choice!")

def super_admin_screen(username):
    """Super admin menu"""
    while True:
        print("\n" + "="*40)
        print(f"Super Admin: {username}")
        print("="*40)
        print("1. Add Book")
        print("2. Remove Book")
        print("3. Find Books")
        print("4. View History")
        print("5. Create Librarian")
        print("6. View Admins")
        print("7. Logout")
        
        choice = input("Choose (1-7): ").strip()
        
        if choice == '1':
            add_new_book()
        elif choice == '2':
            remove_book()
        elif choice == '3':
            find_books()
        elif choice == '4':
            show_history(admin_view=True)
        elif choice == '5':
            create_librarian(username)
        elif choice == '6':
            show_admins()
        elif choice == '7':
            print("Logged out!")
            break
        else:
            print("Wrong choice!")

def main():
    """Main program"""
    print("="*50)
    print("    LIBRARY SYSTEM")
    print("="*50)
    
    # Connect to database
    if not connect_db():
        print("Can't connect to database!")
        return
    
    # Setup database
    if not setup_database():
        print("Database setup failed!")
        return
    
    print("\nDefault Admin:")
    print("  User: superadmin")
    print("  Pass: admin123")
    
    while True:
        print("\n" + "="*40)
        print("Main Menu")
        print("="*40)
        print("1. Student Login")
        print("2. Student Sign Up")
        print("3. Admin Login")
        print("4. Exit")
        
        choice = input("Choose (1-4): ").strip()
        
        if choice == '1':
            user = student_login()
            if user:
                student_screen(user)
        elif choice == '2':
            student_register()
        elif choice == '3':
            user, level = admin_login()
            if user:
                if level == 'superadmin':
                    super_admin_screen(user)
                else:
                    librarian_screen(user)
        elif choice == '4':
            print("Thanks for using the library system!")
            if db_conn:
                db_conn.close()
            break
        else:
            print("Please choose 1-4!")

# Start the program
if __name__ == "__main__":
    main()
