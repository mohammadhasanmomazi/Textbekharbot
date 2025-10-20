import logging
import re
from typing import Optional, Dict, Any, List
from telebot import types
from config import Messages, PROVINCES, PROVINCE_CITIES, ContentCategory, UserRole
from database import DatabaseManager

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class InputValidator:
    """Handles input validation and sanitization"""
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Validate phone number format"""
        # Remove all non-digit characters
        clean_phone = re.sub(r'\D', '', phone)
        
        # Handle different formats
        if clean_phone.startswith('98'):
            # Remove country code
            clean_phone = clean_phone[2:]
        elif clean_phone.startswith('+98'):
            # Remove country code with +
            clean_phone = clean_phone[3:]
        
        # Check if it's a valid Iranian phone number
        return len(clean_phone) >= 10 and clean_phone.startswith(('09', '9'))
    
    @staticmethod
    def validate_name(name: str) -> bool:
        """Validate name (Persian/English letters only)"""
        if not name or len(name.strip()) < 2:
            return False
        # Allow Persian and English letters, spaces, and common Persian characters
        pattern = r'^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFFa-zA-Z\s\u200C\u200D]+$'
        return bool(re.match(pattern, name.strip()))
    
    @staticmethod
    def validate_province(province: str) -> bool:
        """Validate province selection"""
        return province in PROVINCES
    
    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """Validate user ID format"""
        try:
            return int(user_id) > 0
        except ValueError:
            return False
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize text input"""
        if not text:
            return ""
        # Remove excessive whitespace and normalize
        return re.sub(r'\s+', ' ', text.strip())
    
    @staticmethod
    def validate_content_text(text: str) -> bool:
        """Validate content text"""
        if not text or len(text.strip()) < 5:
            return False
        return len(text.strip()) <= 1000  # Max 1000 characters

class KeyboardManager:
    """Manages keyboard layouts and UI components"""
    
    @staticmethod
    def get_phone_request_keyboard() -> types.ReplyKeyboardMarkup:
        """Get phone request keyboard"""
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        button = types.KeyboardButton(text="ارسال شماره تلفن", request_contact=True)
        markup.add(button)
        return markup
    
    @staticmethod
    def get_province_keyboard() -> types.ReplyKeyboardMarkup:
        """Get province selection keyboard"""
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        
        # Add provinces in rows of 2
        for i in range(0, len(PROVINCES), 2):
            row = []
            row.append(types.KeyboardButton(PROVINCES[i]))
            if i + 1 < len(PROVINCES):
                row.append(types.KeyboardButton(PROVINCES[i + 1]))
            markup.row(*row)
        
        return markup
    
    @staticmethod
    def get_main_menu_keyboard() -> types.ReplyKeyboardMarkup:
        """Get professional main menu keyboard"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        
        # Header section
        markup.row(types.KeyboardButton("🏠 صفحه اصلی"))
        
        # Music content section
        markup.row(
            types.KeyboardButton("🔥 پر بازدید ترین ترک ها"),
            types.KeyboardButton("💰 پکیج اقتصادی")
        )
        markup.row(types.KeyboardButton("👑 پکیج مگاهیت VIP"))
        
        # Services section
        markup.row(
            types.KeyboardButton("📞 ارتباط با ما"),
            types.KeyboardButton("ℹ️ درباره ما")
        )
        
        # User section
        markup.row(types.KeyboardButton("👤 پنل کاربری"))
        
        return markup
    
    @staticmethod
    def get_admin_choice_keyboard() -> types.ReplyKeyboardMarkup:
        """Get professional admin choice keyboard"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        
        # Welcome section
        markup.row(types.KeyboardButton("👋 خوش آمدید"))
        
        # Panel selection
        markup.row(
            types.KeyboardButton("👑 پنل ادمین"),
            types.KeyboardButton("👤 پنل کاربر")
        )
        
        # Quick actions
        markup.row(types.KeyboardButton("📊 آمار کلی"))
        
        return markup
    
    @staticmethod
    def get_admin_panel_keyboard() -> types.ReplyKeyboardMarkup:
        """Get comprehensive admin panel keyboard"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        
        # Header
        markup.row(types.KeyboardButton("🏠 صفحه اصلی"))
        
        # User Management Section
        markup.row(types.KeyboardButton("👥 مدیریت کاربران"))
        markup.row(
            types.KeyboardButton("📋 لیست کاربران"),
            types.KeyboardButton("➕ افزودن ادمین")
        )
        
        # Content Management Section
        markup.row(types.KeyboardButton("📁 مدیریت محتوا"))
        
        # Top Tracks Content
        markup.row(types.KeyboardButton("🔥 پر بازدید ترین ترک ها"))
        markup.row(
            types.KeyboardButton("🎵 افزودن موزیک"),
            types.KeyboardButton("📝 افزودن متن")
        )
        
        # Economic Package Content
        markup.row(types.KeyboardButton("💰 پکیج اقتصادی"))
        markup.row(
            types.KeyboardButton("🎵 افزودن موزیک"),
            types.KeyboardButton("📝 افزودن متن")
        )
        
        # VIP Package Content
        markup.row(types.KeyboardButton("👑 پکیج مگاهیت VIP"))
        markup.row(
            types.KeyboardButton("🎵 افزودن موزیک"),
            types.KeyboardButton("📝 افزودن متن")
        )
        
        # System Section
        markup.row(types.KeyboardButton("⚙️ تنظیمات سیستم"))
        markup.row(
            types.KeyboardButton("📊 آمار کلی"),
            types.KeyboardButton("🔧 ابزارها")
        )
        
        # Navigation
        markup.row(types.KeyboardButton("🔙 بازگشت"))
        
        return markup
    
    @staticmethod
    def get_user_panel_keyboard() -> types.ReplyKeyboardMarkup:
        """Get comprehensive user panel keyboard"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        
        # Header
        markup.row(types.KeyboardButton("🏠 صفحه اصلی"))
        
        # Music Content Section
        markup.row(
            types.KeyboardButton("🔥 پر بازدید ترین ترک ها"),
            types.KeyboardButton("💰 پکیج اقتصادی")
        )
        markup.row(types.KeyboardButton("👑 پکیج مگاهیت VIP"))
        
        # User Services
        markup.row(
            types.KeyboardButton("📞 ارتباط با ما"),
            types.KeyboardButton("ℹ️ درباره ما")
        )
        markup.row(
            types.KeyboardButton("📋 راهنما"),
            types.KeyboardButton("⚙️ تنظیمات")
        )
        
        # Account Section
        markup.row(
            types.KeyboardButton("👤 اطلاعات من"),
            types.KeyboardButton("📊 آمار من")
        )
        
        return markup
    
    @staticmethod
    def get_content_management_keyboard() -> types.ReplyKeyboardMarkup:
        """Get content management keyboard"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        
        # Header
        markup.row(types.KeyboardButton("🏠 صفحه اصلی"))
        
        # Content Categories
        markup.row(types.KeyboardButton("📁 دسته‌بندی محتوا"))
        markup.row(
            types.KeyboardButton("🔥 پر بازدید ترین ترک ها"),
            types.KeyboardButton("💰 پکیج اقتصادی")
        )
        markup.row(types.KeyboardButton("👑 پکیج مگاهیت VIP"))
        
        # Content Actions
        markup.row(types.KeyboardButton("➕ افزودن محتوا"))
        markup.row(
            types.KeyboardButton("🎵 افزودن موزیک"),
            types.KeyboardButton("📝 افزودن متن")
        )
        
        # Content Management
        markup.row(types.KeyboardButton("📋 مدیریت محتوا"))
        markup.row(
            types.KeyboardButton("👁️ مشاهده محتوا"),
            types.KeyboardButton("✏️ ویرایش محتوا")
        )
        markup.row(
            types.KeyboardButton("🗑️ حذف محتوا"),
            types.KeyboardButton("📊 آمار محتوا")
        )
        
        # Navigation
        markup.row(types.KeyboardButton("🔙 بازگشت"))
        
        return markup
    
    @staticmethod
    def get_system_settings_keyboard() -> types.ReplyKeyboardMarkup:
        """Get system settings keyboard"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        
        # Header
        markup.row(types.KeyboardButton("🏠 صفحه اصلی"))
        
        # System Information
        markup.row(types.KeyboardButton("📊 آمار سیستم"))
        markup.row(
            types.KeyboardButton("👥 آمار کاربران"),
            types.KeyboardButton("📁 آمار محتوا")
        )
        
        # System Tools
        markup.row(types.KeyboardButton("🔧 ابزارهای سیستم"))
        markup.row(
            types.KeyboardButton("🔄 بروزرسانی"),
            types.KeyboardButton("🧹 پاکسازی")
        )
        markup.row(
            types.KeyboardButton("💾 پشتیبان‌گیری"),
            types.KeyboardButton("📋 گزارش‌ها")
        )
        
        # Advanced Settings
        markup.row(types.KeyboardButton("⚙️ تنظیمات پیشرفته"))
        markup.row(
            types.KeyboardButton("🔐 امنیت"),
            types.KeyboardButton("📱 اعلان‌ها")
        )
        
        # Navigation
        markup.row(types.KeyboardButton("🔙 بازگشت"))
        
        return markup
    
    @staticmethod
    def get_inline_content_keyboard(content_id: int, category: str) -> types.InlineKeyboardMarkup:
        """Get inline keyboard for content actions"""
        markup = types.InlineKeyboardMarkup()
        
        markup.row(
            types.InlineKeyboardButton("نمایش", callback_data=f"view_{content_id}"),
            types.InlineKeyboardButton("حذف", callback_data=f"delete_{content_id}")
        )
        
        return markup
    
    @staticmethod
    def get_user_list_keyboard(users: List[Dict[str, Any]], page: int = 1, total_pages: int = 1, search: str = None) -> types.InlineKeyboardMarkup:
        """Get professional user list keyboard with glass buttons"""
        markup = types.InlineKeyboardMarkup()
        
        # Add user buttons (glass effect simulation with emojis)
        for user in users:
            user_id = user['user_id']
            name = f"{user.get('first_name', 'نامشخص')} {user.get('last_name', 'نامشخص')}"
            role_emoji = "👑" if user['role'] == 'super_admin' else "🛡️" if user['role'] == 'admin' else "👤"
            province = user.get('province', 'نامشخص')
            
            # Create glass button text with professional styling
            button_text = f"🔮 {role_emoji} {name} | {province}"
            markup.row(types.InlineKeyboardButton(button_text, callback_data=f"user_detail_{user_id}"))
        
        # Add pagination controls
        if total_pages > 1:
            nav_buttons = []
            
            if page > 1:
                nav_buttons.append(types.InlineKeyboardButton("⬅️ قبلی", callback_data=f"user_list_{page-1}_{search or ''}"))
            
            nav_buttons.append(types.InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="user_list_info"))
            
            if page < total_pages:
                nav_buttons.append(types.InlineKeyboardButton("بعدی ➡️", callback_data=f"user_list_{page+1}_{search or ''}"))
            
            markup.row(*nav_buttons)
        
        # Add search and refresh buttons
        markup.row(
            types.InlineKeyboardButton("🔍 جستجو", callback_data="user_search"),
            types.InlineKeyboardButton("🔄 بروزرسانی", callback_data=f"user_list_{page}_{search or ''}")
        )
        
        return markup
    
    @staticmethod
    def get_user_detail_keyboard(user_id: int, user_role: str, is_banned: bool = False) -> types.InlineKeyboardMarkup:
        """Get user detail keyboard with management actions"""
        markup = types.InlineKeyboardMarkup()
        
        # Ban/Unban button
        if user_role != 'super_admin':
            if is_banned:
                markup.row(types.InlineKeyboardButton("✅ آزاد کردن", callback_data=f"unban_user_{user_id}"))
            else:
                markup.row(types.InlineKeyboardButton("🚫 بن کردن", callback_data=f"ban_user_{user_id}"))
        
        # Role management buttons
        if user_role == 'user':
            markup.row(types.InlineKeyboardButton("🛡️ تبدیل به ادمین", callback_data=f"make_admin_{user_id}"))
        elif user_role == 'admin':
            markup.row(types.InlineKeyboardButton("👤 تبدیل به کاربر", callback_data=f"make_user_{user_id}"))
        
        # Additional actions
        markup.row(
            types.InlineKeyboardButton("📊 آمار کاربر", callback_data=f"user_stats_{user_id}"),
            types.InlineKeyboardButton("💬 پیام به کاربر", callback_data=f"message_user_{user_id}")
        )
        
        # Navigation
        markup.row(types.InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="user_list_1_"))
        
        return markup
    
    @staticmethod
    def get_user_search_keyboard() -> types.InlineKeyboardMarkup:
        """Get user search keyboard"""
        markup = types.InlineKeyboardMarkup()
        
        markup.row(
            types.InlineKeyboardButton("🔍 جستجو بر اساس نام", callback_data="search_by_name"),
            types.InlineKeyboardButton("📞 جستجو بر اساس شماره", callback_data="search_by_phone")
        )
        markup.row(
            types.InlineKeyboardButton("🗺️ جستجو بر اساس استان", callback_data="search_by_province"),
            types.InlineKeyboardButton("👑 جستجو بر اساس نقش", callback_data="search_by_role")
        )
        markup.row(types.InlineKeyboardButton("🔙 بازگشت", callback_data="user_list_1_"))
        
        return markup

class MessageFormatter:
    """Handles message formatting and templates"""
    
    @staticmethod
    def format_user_info(user_data: Dict[str, Any]) -> str:
        """Format user information for display"""
        return f"""📋 اطلاعات کاربر:
📞 شماره: {user_data.get('phone', 'نامشخص')}
👤 نام: {user_data.get('first_name', 'نامشخص')}
👨‍👩‍👧‍👦 نام خانوادگی: {user_data.get('last_name', 'نامشخص')}
🗺️ استان: {user_data.get('province', 'نامشخص')}
🏙️ شهر: {user_data.get('city', 'نامشخص')}
👑 نقش: {user_data.get('role', 'کاربر')}"""
    
    @staticmethod
    def format_user_list(users: List[Dict[str, Any]]) -> str:
        """Format user list for display"""
        if not users:
            return "هیچ کاربری ثبت نام نکرده است."
        
        user_list = []
        for i, user in enumerate(users, 1):
            user_info = f"{i}. {user.get('first_name', 'نامشخص')} {user.get('last_name', 'نامشخص')}"
            user_info += f" - {user.get('province', 'نامشخص')}"
            user_info += f" ({user.get('role', 'کاربر')})"
            user_list.append(user_info)
        
        return f"👥 لیست کاربران ({len(users)} نفر):\n\n" + "\n".join(user_list)
    
    @staticmethod
    def format_professional_user_list(users: List[Dict[str, Any]], page: int, total_pages: int, total_users: int, search: str = None) -> str:
        """Format professional user list with pagination info"""
        if not users:
            search_text = f" برای '{search}'" if search else ""
            return f"🔍 هیچ کاربری{search_text} یافت نشد."
        
        header = f"👥 لیست کاربران حرفه‌ای\n"
        header += f"📊 کل کاربران: {total_users} نفر\n"
        header += f"📄 صفحه {page} از {total_pages}\n"
        
        if search:
            header += f"🔍 جستجو: '{search}'\n"
        
        header += f"\n🔮 برای مشاهده جزئیات هر کاربر، روی دکمه شیشه‌ای مربوطه کلیک کنید:\n\n"
        
        return header
    
    @staticmethod
    def format_user_detail(user: Dict[str, Any]) -> str:
        """Format detailed user information"""
        if not user:
            return "❌ کاربر یافت نشد."
        
        # Role emoji mapping
        role_emojis = {
            'super_admin': '👑 ادمین اصلی',
            'admin': '🛡️ ادمین',
            'user': '👤 کاربر عادی'
        }
        
        # Status emoji
        status_emoji = "✅ فعال" if user.get('is_active', 1) else "🚫 غیرفعال"
        
        # Format creation date
        created_at = user.get('created_at', 'نامشخص')
        if created_at != 'نامشخص':
            try:
                from datetime import datetime
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_at = created_at.strftime('%Y/%m/%d %H:%M')
            except:
                pass
        
        detail = f"🔮 اطلاعات کامل کاربر\n"
        detail += f"{'='*30}\n\n"
        detail += f"🆔 شناسه کاربری: `{user['user_id']}`\n"
        detail += f"👤 نام: {user.get('first_name', 'نامشخص')}\n"
        detail += f"👨‍👩‍👧‍👦 نام خانوادگی: {user.get('last_name', 'نامشخص')}\n"
        detail += f"📞 شماره تلفن: {user.get('phone', 'نامشخص')}\n"
        detail += f"🗺️ استان: {user.get('province', 'نامشخص')}\n"
        detail += f"🏙️ شهر: {user.get('city', 'نامشخص')}\n"
        detail += f"👑 نقش: {role_emojis.get(user.get('role', 'user'), '👤 کاربر عادی')}\n"
        detail += f"📊 وضعیت: {status_emoji}\n"
        detail += f"📅 تاریخ ثبت نام: {created_at}\n"
        
        return detail
    
    @staticmethod
    def format_user_stats(user: Dict[str, Any]) -> str:
        """Format user statistics"""
        if not user:
            return "❌ آمار کاربر یافت نشد."
        
        stats = f"📊 آمار کاربر\n"
        stats += f"{'='*20}\n\n"
        stats += f"👤 نام: {user.get('first_name', 'نامشخص')} {user.get('last_name', 'نامشخص')}\n"
        stats += f"📅 عضو از: {user.get('created_at', 'نامشخص')}\n"
        stats += f"🔄 آخرین بروزرسانی: {user.get('updated_at', 'نامشخص')}\n"
        stats += f"📊 وضعیت: {'✅ فعال' if user.get('is_active', 1) else '🚫 غیرفعال'}\n"
        
        return stats
    
    @staticmethod
    def format_content_list(contents: Dict[str, List[Dict[str, Any]]], category_display: str) -> str:
        """Format content list for display"""
        if not any(contents.values()):
            return f"هیچ محتوایی در دسته {category_display} موجود نیست."
        
        result = f"📋 {category_display}:\n\n"
        
        # Text contents
        if contents.get('text'):
            result += "📝 متون:\n"
            for i, content in enumerate(contents['text'], 1):
                title = content.get('title', f'متن {i}')
                result += f"{i}. {title}\n"
            result += "\n"
        
        # Music contents
        if contents.get('music'):
            result += "🎵 موزیک‌ها:\n"
            for i, content in enumerate(contents['music'], 1):
                title = content.get('title', f'موزیک {i}')
                result += f"{i}. {title}\n"
            result += "\n"
        
        return result.strip()
    
    @staticmethod
    def format_error_message(error_type: str = "general") -> str:
        """Format error messages"""
        error_messages = {
            "general": Messages.ERROR_GENERAL,
            "invalid_input": Messages.ERROR_INVALID_INPUT,
            "permission_denied": Messages.ERROR_PERMISSION_DENIED,
            "validation_error": "اطلاعات وارد شده نامعتبر است. لطفا دوباره تلاش کنید. ❌",
            "database_error": "خطا در پایگاه داده. لطفا دوباره تلاش کنید. ❌",
            "file_error": "خطا در پردازش فایل. لطفا دوباره تلاش کنید. ❌"
        }
        return error_messages.get(error_type, Messages.ERROR_GENERAL)
    
    @staticmethod
    def format_success_message(action: str) -> str:
        """Format success messages"""
        success_messages = {
            "registration": Messages.REGISTRATION_COMPLETE,
            "content_added": "محتوای جدید با موفقیت اضافه شد. ✅",
            "admin_added": "کاربر با موفقیت به عنوان ادمین اضافه شد. ✅",
            "session_cleared": "جلسه کاربر پاک شد. ✅"
        }
        return success_messages.get(action, "عملیات با موفقیت انجام شد. ✅")

class SessionManager:
    """Manages user sessions and temporary data"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def start_registration_session(self, user_id: int) -> bool:
        """Start registration session"""
        session_data = {
            'step': 'phone',
            'registration_started': True
        }
        return self.db.save_session(user_id, session_data)
    
    def update_registration_step(self, user_id: int, step: str, data: Dict[str, Any] = None) -> bool:
        """Update registration step"""
        session = self.db.get_session(user_id) or {}
        session['step'] = step
        
        if data:
            session.update(data)
        
        return self.db.save_session(user_id, session)
    
    def get_registration_data(self, user_id: int) -> Dict[str, Any]:
        """Get registration data from session"""
        session = self.db.get_session(user_id) or {}
        return session.get('registration_data', {})
    
    def update_registration_data(self, user_id: int, data: Dict[str, Any]) -> bool:
        """Update registration data"""
        session = self.db.get_session(user_id) or {}
        registration_data = session.get('registration_data', {})
        registration_data.update(data)
        session['registration_data'] = registration_data
        
        return self.db.save_session(user_id, session)
    
    def complete_registration(self, user_id: int) -> bool:
        """Complete registration and clear session"""
        return self.db.clear_session(user_id)
    
    def start_admin_action(self, user_id: int, action: str, category: str = None) -> bool:
        """Start admin action session"""
        session_data = {
            'admin_action': action,
            'step': 'input',
            'category': category
        }
        return self.db.save_session(user_id, session_data)
    
    def get_admin_session(self, user_id: int) -> Dict[str, Any]:
        """Get admin session data"""
        session = self.db.get_session(user_id) or {}
        return session
    
    def update_admin_session(self, user_id: int, data: Dict[str, Any]) -> bool:
        """Update admin session"""
        session = self.db.get_session(user_id) or {}
        session.update(data)
        return self.db.save_session(user_id, session)
    
    def clear_admin_session(self, user_id: int) -> bool:
        """Clear admin session"""
        return self.db.clear_session(user_id)
