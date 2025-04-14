import sqlite3
from datetime import datetime

DB_NAME = "thong_tin_ca_nhan.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS info (
        hoTen TEXT,
        DateBirth TEXT,
        Address TEXT,
        PhoneNumber TEXT,
        StudentID TEXT
    )
    """)
    # Tạo bảng DiemSo (nếu chưa tồn tại)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS DiemSo (
        TenMonHoc TEXT,
        DiemKiemTra1 REAL,
        DiemKiemTra2 REAL,
        ChuyenCan INTEGER
    )
    """)
    conn.commit()
    conn.close()


def getINFO():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM info")
    all_data = cur.fetchall()
    conn.close()
    return (all_data)


def getGPA():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    # Lấy TenMonHoc và GPA đã tính từ bảng DiemSo
    cur.execute("""
    SELECT
        TenMonHoc,
        ChuyenCan,
        ((DiemKiemTra1 + DiemKiemTra2) / 2) * 0.9 + (ChuyenCan * 0.1) AS GPA
    FROM
        DiemSo
    """)

    results = cur.fetchall()
    conn.close()
    # print("----------------------------")
    # for row in results:
    #     ten_mon_hoc = row[0]
    #     cc = row[1]
    #     gpa=row[2]
    #     print(f"| {ten_mon_hoc:<20} | {cc:<1}  | {gpa:.2f} |")
    return (results)


print(getINFO())
print(getGPA())

