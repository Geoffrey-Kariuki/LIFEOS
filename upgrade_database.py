import sqlite3
import os


# =========================
# DATABASE LOCATION
# =========================

database_path = os.path.join(
    os.path.dirname(__file__),
    "instance",
    "lifeos.db"
)


# =========================
# CONNECT TO DATABASE
# =========================

connection = sqlite3.connect(database_path)

cursor = connection.cursor()


print("Connected to LIFEOS database.")
print()


# =========================
# CHECK TRANSACTIONS TABLE
# =========================

cursor.execute(
    "PRAGMA table_info(transactions)"
)

columns = cursor.fetchall()

existing_columns = [
    column[1]
    for column in columns
]


print("Existing transaction columns:")

for column in existing_columns:
    print(f" - {column}")

print()


# =========================
# ADD TYPE COLUMN
# =========================

if "type" not in existing_columns:

    print("Adding missing 'type' column...")

    cursor.execute(
        """
        ALTER TABLE transactions
        ADD COLUMN type VARCHAR(20)
        DEFAULT 'expense'
        """
    )

    print("✅ 'type' column added.")

else:

    print("✅ 'type' column already exists.")


# =========================
# CHECK AMOUNT COLUMN
# =========================

if "amount" not in existing_columns:

    print("Adding missing 'amount' column...")

    cursor.execute(
        """
        ALTER TABLE transactions
        ADD COLUMN amount FLOAT
        DEFAULT 0
        """
    )

    print("✅ 'amount' column added.")


# =========================
# CHECK CATEGORY COLUMN
# =========================

if "category" not in existing_columns:

    print("Adding missing 'category' column...")

    cursor.execute(
        """
        ALTER TABLE transactions
        ADD COLUMN category VARCHAR(100)
        DEFAULT 'General'
        """
    )

    print("✅ 'category' column added.")


# =========================
# CHECK DESCRIPTION COLUMN
# =========================

if "description" not in existing_columns:

    print("Adding missing 'description' column...")

    cursor.execute(
        """
        ALTER TABLE transactions
        ADD COLUMN description TEXT
        """
    )

    print("✅ 'description' column added.")


# =========================
# CHECK TRANSACTION DATE
# =========================

if "transaction_date" not in existing_columns:

    print("Adding missing 'transaction_date' column...")

    cursor.execute(
        """
        ALTER TABLE transactions
        ADD COLUMN transaction_date DATETIME
        """
    )

    print("✅ 'transaction_date' column added.")


# =========================
# CHECK CREATED AT
# =========================

if "created_at" not in existing_columns:

    print("Adding missing 'created_at' column...")

    cursor.execute(
        """
        ALTER TABLE transactions
        ADD COLUMN created_at DATETIME
        """
    )

    print("✅ 'created_at' column added.")


# =========================
# CHECK USER ID
# =========================

if "user_id" not in existing_columns:

    print("Adding missing 'user_id' column...")

    cursor.execute(
        """
        ALTER TABLE transactions
        ADD COLUMN user_id INTEGER
        """
    )

    print("✅ 'user_id' column added.")


# =========================
# SAVE CHANGES
# =========================

connection.commit()


# =========================
# SHOW FINAL STRUCTURE
# =========================

print()
print("============================")
print("FINAL TRANSACTIONS TABLE")
print("============================")

cursor.execute(
    "PRAGMA table_info(transactions)"
)

final_columns = cursor.fetchall()

for column in final_columns:

    print(
        f"{column[1]} "
        f"({column[2]})"
    )


# =========================
# CLOSE DATABASE
# =========================

connection.close()


print()
print("============================")
print("DATABASE UPGRADE COMPLETE")
print("============================")
print()
print("You can now start LIFEOS.")