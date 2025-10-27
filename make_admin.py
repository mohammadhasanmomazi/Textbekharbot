#!/usr/bin/env python3
"""
Script to make a user admin
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager, UserRole

def make_user_admin(user_id: int):
    """Make a user admin"""
    db = DatabaseManager()

    # Check if user exists
    user = db.get_user(user_id)
    if not user:
        print(f"❌ کاربر با شناسه {user_id} در سیستم یافت نشد.")
        return False

    # Check if already admin
    if user['role'] in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        role_text = "ادمین اصلی" if user['role'] == UserRole.SUPER_ADMIN else "ادمین"
        print(f"⚠️ کاربر با شناسه {user_id} قبلاً به عنوان {role_text} تعریف شده است.")
        return True

    # Update role
    success = db.update_user_role(user_id, UserRole.ADMIN)
    if success:
        user_name = f"{user.get('first_name', 'نامشخص')} {user.get('last_name', 'نامشخص')}"
        print(f"✅ کاربر {user_name} (شناسه: {user_id}) با موفقیت به عنوان ادمین اضافه شد.")
        return True
    else:
        print(f"❌ خطا در بروزرسانی نقش کاربر {user_id}.")
        return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("استفاده: python make_admin.py <user_id>")
        sys.exit(1)

    try:
        user_id = int(sys.argv[1])
        make_user_admin(user_id)
    except ValueError:
        print("❌ شناسه کاربری باید عدد باشد.")
        sys.exit(1)
