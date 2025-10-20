import logging
import os
from typing import Optional, Dict, Any, List
from telebot import TeleBot, types
from telebot.apihelper import ApiTelegramException

from config import BOT_TOKEN, Messages, ContentCategory, UserRole, PROVINCE_CITIES
from database import DatabaseManager
from utils import (
    InputValidator, KeyboardManager, MessageFormatter,
    SessionManager, ValidationError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class TextBekharBot:
    """Main bot class with clean architecture"""

    def __init__(self, token: str = BOT_TOKEN):
        self.bot = TeleBot(token)
        self.db = DatabaseManager()
        self.session_manager = SessionManager(self.db)
        self.validator = InputValidator()
        self.keyboard_manager = KeyboardManager()
        self.formatter = MessageFormatter()

        self._setup_handlers()
        logger.info("Bot initialized successfully")

    def _setup_handlers(self):
        """Setup all bot handlers"""
        # Command handlers
        self.bot.message_handler(commands=['start'])(self.handle_start)
        self.bot.message_handler(commands=['help'])(self.handle_help)
        self.bot.message_handler(commands=['makeadmin'])(
            self.handle_make_admin)
        self.bot.message_handler(commands=['myid'])(self.handle_my_id)
        self.bot.message_handler(commands=['send'])(self.handle_send_command)

        # Contact handler
        self.bot.message_handler(
            content_types=['contact'])(self.handle_contact)

        # Registration handlers
        self.bot.message_handler(func=self._is_registration_step(
            'first_name'))(self.handle_first_name)
        self.bot.message_handler(func=self._is_registration_step(
            'last_name'))(self.handle_last_name)
        self.bot.message_handler(func=self._is_registration_step(
            'province'))(self.handle_province)

        # Main menu handlers - Professional layout
        self.bot.message_handler(
            func=lambda m: m.text == "🏠 صفحه اصلی")(self.handle_home)
        self.bot.message_handler(func=lambda m: m.text == "🔥 پر بازدید ترین ترک ها")(
            self.handle_top_tracks)
        self.bot.message_handler(func=lambda m: m.text == "💰 پکیج اقتصادی")(
            self.handle_economic_package)
        self.bot.message_handler(func=lambda m: m.text == "👑 پکیج مگاهیت VIP")(
            self.handle_vip_package)
        self.bot.message_handler(func=lambda m: m.text == "📞 ارتباط با ما")(
            self.handle_contact_us)
        self.bot.message_handler(
            func=lambda m: m.text == "ℹ️ درباره ما")(self.handle_about_us)
        self.bot.message_handler(func=lambda m: m.text == "👤 پنل کاربری")(
            self.handle_user_panel)

        # User panel handlers
        self.bot.message_handler(func=lambda m: m.text == "👤 اطلاعات من")(
            self.handle_user_info)
        self.bot.message_handler(func=lambda m: m.text == "📊 آمار من")(
            self.handle_user_stats)
        self.bot.message_handler(func=lambda m: m.text == "⚙️ تنظیمات")(
            self.handle_user_settings)
        self.bot.message_handler(
            func=lambda m: m.text == "📋 راهنما")(self.handle_guide)

        # Admin panel handlers - Professional layout
        self.bot.message_handler(func=lambda m: m.text == "👑 پنل ادمین")(
            self.handle_admin_panel)
        self.bot.message_handler(func=lambda m: m.text == "👤 پنل کاربر")(
            self.handle_user_panel)
        self.bot.message_handler(
            func=lambda m: m.text == "👋 خوش آمدید")(self.handle_welcome)
        self.bot.message_handler(func=lambda m: m.text == "📊 آمار کلی")(
            self.handle_general_stats)
        self.bot.message_handler(func=lambda m: m.text == "🔙 بازگشت")(
            self.handle_back_to_main)

        # User Management handlers
        self.bot.message_handler(func=lambda m: m.text == "👥 مدیریت کاربران")(
            self.handle_user_management)
        self.bot.message_handler(func=lambda m: m.text == "📋 لیست کاربران")(
            self.handle_list_users)
        self.bot.message_handler(func=lambda m: m.text == "➕ افزودن ادمین")(
            self.handle_add_admin_prompt)

        # Content Management handlers
        self.bot.message_handler(func=lambda m: m.text == "📁 مدیریت محتوا")(
            self.handle_content_management)
        self.bot.message_handler(func=lambda m: m.text == "🎵 افزودن موزیک")(
            self.handle_add_music_menu)
        self.bot.message_handler(func=lambda m: m.text == "📝 افزودن متن")(
            self.handle_add_text_menu)

        # System Settings handlers
        self.bot.message_handler(func=lambda m: m.text == "⚙️ تنظیمات سیستم")(
            self.handle_system_settings)
        self.bot.message_handler(func=lambda m: m.text == "🔧 ابزارها")(
            self.handle_system_tools)

        # Content addition handlers
        self._setup_content_handlers()

        # File handlers
        self.bot.message_handler(content_types=[
                                 'audio', 'document'], func=self._is_admin_adding_music)(self.handle_admin_music)

        # Admin text input handlers
        self.bot.message_handler(func=self._is_admin_adding_text)(
            self.handle_admin_text)

        # Admin ID input handler
        self.bot.message_handler(func=self._is_admin_inputting_id)(
            self.handle_admin_id_input)

        # Callback query handlers for user management
        self.bot.callback_query_handler(func=lambda call: call.data.startswith(
            'user_list_'))(self.handle_user_list_callback)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith(
            'user_detail_'))(self.handle_user_detail_callback)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith(
            'ban_user_'))(self.handle_ban_user_callback)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith(
            'unban_user_'))(self.handle_unban_user_callback)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith(
            'make_admin_'))(self.handle_make_admin_callback)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith(
            'make_user_'))(self.handle_make_user_callback)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith(
            'user_stats_'))(self.handle_user_stats_callback)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith(
            'message_user_'))(self.handle_message_user_callback)
        self.bot.callback_query_handler(func=lambda call: call.data == 'user_search')(
            self.handle_user_search_callback)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith(
            'search_by_'))(self.handle_search_type_callback)

        # Search input handlers
        self.bot.message_handler(func=self._is_admin_searching)(
            self.handle_search_input)

        # Admin message input handler
        self.bot.message_handler(func=self._is_admin_sending_message)(
            self.handle_admin_message_input)

        # Default handler
        self.bot.message_handler(func=lambda m: True)(self.handle_default)

    def _setup_content_handlers(self):
        """Setup content addition handlers for new professional layout"""
        # Content addition handlers for the new menu structure
        content_actions = [
            # Top tracks content
            ("افزودن موزیک به پر بازدید ترین ترک ها 🎵🔥",
             ContentCategory.TOP_TRACKS, "music"),
            ("افزودن متن به پر بازدید ترین ترک ها 📝🔥",
             ContentCategory.TOP_TRACKS, "text"),
            # Economic package content
            ("افزودن موزیک به پکیج اقتصادی 🎵💰",
             ContentCategory.ECONOMIC_PACKAGE, "music"),
            ("افزودن متن به پکیج اقتصادی 📝💰",
             ContentCategory.ECONOMIC_PACKAGE, "text"),
            # VIP package content
            ("افزودن موزیک به پکیج مگاهیت VIP 🎵👑",
             ContentCategory.VIP_PACKAGE, "music"),
            ("افزودن متن به پکیج مگاهیت VIP 📝👑",
             ContentCategory.VIP_PACKAGE, "text"),
        ]

        for button_text, category, content_type in content_actions:
            def handler_func(
                m, c=category, t=content_type): return self.handle_add_content(m, c, t)
            self.bot.message_handler(
                func=lambda m, text=button_text: m.text == text)(handler_func)

    def _is_registration_step(self, step: str):
        """Check if user is in specific registration step"""
        def check(message):
            session = self.session_manager.db.get_session(
                message.from_user.id) or {}
            return session.get('step') == step
        return check

    def _is_admin_adding_music(self, message):
        """Check if admin is adding music"""
        session = self.session_manager.get_admin_session(message.from_user.id)
        return (session.get('admin_action') == 'add_music' and
                session.get('step') == 'music' and
                self.db.is_admin(message.from_user.id))

    def _is_admin_adding_text(self, message):
        """Check if admin is adding text"""
        session = self.session_manager.get_admin_session(message.from_user.id)
        return (session.get('admin_action') == 'add_text' and
                session.get('step') == 'text' and
                self.db.is_admin(message.from_user.id))

    def _is_admin_inputting_id(self, message):
        """Check if admin is inputting user ID"""
        session = self.session_manager.get_admin_session(message.from_user.id)
        return (session.get('admin_action') == 'add_admin' and
                session.get('step') == 'input' and
                self.db.is_admin(message.from_user.id))

    def _is_admin_searching(self, message):
        """Check if admin is searching for users"""
        session = self.session_manager.get_admin_session(message.from_user.id)
        return (session.get('admin_action') == 'search_users' and
                session.get('step') == 'input' and
                self.db.is_admin(message.from_user.id))

    def _is_admin_sending_message(self, message):
        """Check if admin is sending a message to a user"""
        session = self.session_manager.get_admin_session(message.from_user.id)
        return (session.get('admin_action') == 'send_message' and
                session.get('step') == 'message' and
                self.db.is_admin(message.from_user.id))

    # Command handlers
    def handle_start(self, message):
        """Handle /start command"""
        try:
            user_id = message.from_user.id

            # Check if user is admin
            if self.db.is_admin(user_id):
                self.bot.send_message(
                    message.chat.id,
                    Messages.WELCOME,
                    reply_markup=self.keyboard_manager.get_admin_choice_keyboard()
                )
                return

            # Check if user exists
            user = self.db.get_user(user_id)
            if user:
                self.bot.send_message(
                    message.chat.id,
                    Messages.WELCOME,
                    reply_markup=self.keyboard_manager.get_main_menu_keyboard()
                )
                return

            # Start registration
            self.session_manager.start_registration_session(user_id)
            self.bot.send_message(
                message.chat.id,
                Messages.PHONE_REQUEST,
                reply_markup=self.keyboard_manager.get_phone_request_keyboard()
            )

        except Exception as e:
            logger.error(f"Error in handle_start: {e}")
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message())

    def handle_help(self, message):
        """Handle /help command"""
        self.bot.send_message(message.chat.id, Messages.HELP_TEXT)

    def handle_make_admin(self, message):
        """Handle /makeadmin command"""
        try:
            user_id = message.from_user.id
            success = self.db.update_user_role(user_id, UserRole.SUPER_ADMIN)

            if success:
                self.bot.send_message(
                    message.chat.id, "شما به عنوان ادمین اصلی اضافه شدید. ✅")
            else:
                self.bot.send_message(
                    message.chat.id, self.formatter.format_error_message())

        except Exception as e:
            logger.error(f"Error in handle_make_admin: {e}")
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message())

    def handle_my_id(self, message):
        """Handle /myid command"""
        try:
            user_id = message.from_user.id
            user = self.db.get_user(user_id)

            if user:
                user_name = f"{user.get('first_name', 'نامشخص')} {user.get('last_name', 'نامشخص')}"
                role_text = {
                    'super_admin': '👑 ادمین اصلی',
                    'admin': '🛡️ ادمین',
                    'user': '👤 کاربر عادی'
                }.get(user.get('role', 'user'), '👤 کاربر عادی')

                self.bot.send_message(
                    message.chat.id,
                    f"🆔 شناسه کاربری شما:\n\n"
                    f"`{user_id}`\n\n"
                    f"👤 نام: {user_name}\n"
                    f"👑 نقش: {role_text}\n"
                    f"📅 تاریخ ثبت نام: {user.get('created_at', 'نامشخص')}\n\n"
                    f"💡 این شناسه برای افزودن شما به عنوان ادمین استفاده می‌شود.",
                    parse_mode='Markdown'
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    f"🆔 شناسه کاربری شما: `{user_id}`\n\n"
                    f"⚠️ شما هنوز در سیستم ثبت نام نکرده‌اید.\n"
                    f"لطفا ابتدا با دستور /start ثبت نام کنید.",
                    parse_mode='Markdown'
                )

        except Exception as e:
            logger.error(f"Error in handle_my_id: {e}")
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message())

    def handle_send_command(self, message):
        """Handle /send command for messaging users"""
        try:
            if not self.db.is_admin(message.from_user.id):
                self.bot.send_message(
                    message.chat.id, self.formatter.format_error_message("permission_denied"))
                return

            # Parse command arguments
            command_parts = message.text.split()
            if len(command_parts) < 2:
                self.bot.send_message(
                    message.chat.id,
                    "💬 ارسال پیام به کاربر\n\n"
                    "استفاده: `/send [user_id]`\n\n"
                    "مثال: `/send 77126477`\n\n"
                    "💡 ابتدا شناسه کاربری را با دستور /myid دریافت کنید.",
                    parse_mode='Markdown'
                )
                return

            try:
                target_user_id = int(command_parts[1])
            except ValueError:
                self.bot.send_message(
                    message.chat.id, "❌ شناسه کاربری باید عدد باشد.")
                return

            # Check if target user exists
            target_user = self.db.get_user(target_user_id)
            if not target_user:
                self.bot.send_message(
                    message.chat.id,
                    f"❌ کاربر با شناسه {target_user_id} در سیستم یافت نشد.\n\n"
                    f"لطفا ابتدا کاربر را با دستور /start ثبت نام کنید."
                )
                return

            # Start message session
            self.session_manager.start_admin_action(
                message.from_user.id, 'send_message')
            self.session_manager.update_admin_session(message.from_user.id, {
                'target_user_id': target_user_id,
                'step': 'message'
            })

            target_name = f"{target_user.get('first_name', 'نامشخص')} {target_user.get('last_name', 'نامشخص')}"

            self.bot.send_message(
                message.chat.id,
                f"💬 ارسال پیام به کاربر\n\n"
                f"👤 گیرنده: {target_name}\n"
                f"🆔 شناسه: {target_user_id}\n"
                f"📞 شماره: {target_user.get('phone', 'نامشخص')}\n\n"
                f"لطفا پیام خود را ارسال کنید:"
            )

        except Exception as e:
            logger.error(f"Error in handle_send_command: {e}")
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message())

    def handle_contact(self, message):
        """Handle contact sharing"""
        try:
            if not message.contact:
                return

            user_id = message.from_user.id
            phone = message.contact.phone_number

            if not self.validator.validate_phone_number(phone):
                self.bot.send_message(
                    message.chat.id, self.formatter.format_error_message("invalid_input"))
                return

            # Update registration data
            self.session_manager.update_registration_data(
                user_id, {'phone': phone})
            self.session_manager.update_registration_step(
                user_id, 'first_name')

            self.bot.send_message(message.chat.id, Messages.PHONE_RECEIVED)

        except Exception as e:
            logger.error(f"Error in handle_contact: {e}")
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message())

    def handle_first_name(self, message):
        """Handle first name input"""
        try:
            user_id = message.from_user.id
            first_name = self.validator.sanitize_text(message.text)

            if not self.validator.validate_name(first_name):
                self.bot.send_message(
                    message.chat.id, self.formatter.format_error_message("invalid_input"))
                return

            self.session_manager.update_registration_data(
                user_id, {'first_name': first_name})
            self.session_manager.update_registration_step(user_id, 'last_name')

            self.bot.send_message(
                message.chat.id, Messages.FIRST_NAME_RECEIVED)

        except Exception as e:
            logger.error(f"Error in handle_first_name: {e}")
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message())

    def handle_last_name(self, message):
        """Handle last name input"""
        try:
            user_id = message.from_user.id
            last_name = self.validator.sanitize_text(message.text)

            if not self.validator.validate_name(last_name):
                self.bot.send_message(
                    message.chat.id, self.formatter.format_error_message("invalid_input"))
                return

            self.session_manager.update_registration_data(
                user_id, {'last_name': last_name})
            self.session_manager.update_registration_step(user_id, 'province')

            self.bot.send_message(
                message.chat.id,
                Messages.LAST_NAME_RECEIVED,
                reply_markup=self.keyboard_manager.get_province_keyboard()
            )

        except Exception as e:
            logger.error(f"Error in handle_last_name: {e}")
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message())

    def handle_province(self, message):
        """Handle province selection"""
        try:
            user_id = message.from_user.id
            province = message.text

            if not self.validator.validate_province(province):
                self.bot.send_message(
                    message.chat.id, self.formatter.format_error_message("invalid_input"))
                return

            # Get city for province
            city = PROVINCE_CITIES.get(province, 'نامشخص')

            # Get registration data
            reg_data = self.session_manager.get_registration_data(user_id)

            # Create user
            success = self.db.create_user(
                user_id=user_id,
                phone=reg_data.get('phone', ''),
                first_name=reg_data.get('first_name', ''),
                last_name=reg_data.get('last_name', ''),
                province=province,
                city=city
            )

            if success:
                # Complete registration
                self.session_manager.complete_registration(user_id)

                # Send confirmation
                user_info = {
                    'phone': reg_data.get('phone', ''),
                    'first_name': reg_data.get('first_name', ''),
                    'last_name': reg_data.get('last_name', ''),
                    'province': province,
                    'city': city
                }

                self.bot.send_message(
                    message.chat.id,
                    f"{Messages.REGISTRATION_COMPLETE}\n\n{self.formatter.format_user_info(user_info)}",
                    reply_markup=self.keyboard_manager.get_main_menu_keyboard()
                )
            else:
                self.bot.send_message(
                    message.chat.id, self.formatter.format_error_message("database_error"))

        except Exception as e:
            logger.error(f"Error in handle_province: {e}")
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message())

    # Professional menu handlers
    def handle_home(self, message):
        """Handle home page request"""
        if self.db.is_admin(message.from_user.id):
            self.bot.send_message(
                message.chat.id,
                "🏠 صفحه اصلی\n\nبه پنل مدیریت خوش آمدید!",
                reply_markup=self.keyboard_manager.get_admin_choice_keyboard()
            )
        else:
            self.bot.send_message(
                message.chat.id,
                "🏠 صفحه اصلی\n\nبه تکست بخر خوش آمدید!",
                reply_markup=self.keyboard_manager.get_main_menu_keyboard()
            )

    def handle_about_us(self, message):
        """Handle about us request"""
        about_text = """ℹ️ درباره تکست بخر

تکست بخر معتبرترین پلتفرم ترانه، ملودی و تنظیم آهنگسازی در ایران است.

🎯 ویژگی‌های ما:
• سابقه کاری درخشان ۱۰ ساله
• همکاری با اکثر خوانندگان مطرح کشور
• کیفیت بالای محتوا
• پشتیبانی حرفه‌ای

📞 برای اطلاعات بیشتر با ما تماس بگیرید."""

        self.bot.send_message(message.chat.id, about_text)

    def handle_welcome(self, message):
        """Handle welcome request"""
        self.bot.send_message(
            message.chat.id,
            "👋 خوش آمدید!\n\nلطفا پنل مورد نظر خود را انتخاب کنید.",
            reply_markup=self.keyboard_manager.get_admin_choice_keyboard()
        )

    def handle_general_stats(self, message):
        """Handle general statistics request"""
        if not self.db.is_admin(message.from_user.id):
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message("permission_denied"))
            return

        try:
            users = self.db.get_all_users()
            total_users = len(users)
            active_users = len([u for u in users if u.get('is_active', 1)])
            admins = len([u for u in users if u['role']
                         in ['admin', 'super_admin']])

            stats_text = f"""📊 آمار کلی سیستم

👥 کاربران:
• کل کاربران: {total_users} نفر
• کاربران فعال: {active_users} نفر
• ادمین‌ها: {admins} نفر

📁 محتوا:
• پر بازدید ترین ترک ها: در حال بروزرسانی
• پکیج اقتصادی: در حال بروزرسانی
• پکیج مگاهیت VIP: در حال بروزرسانی

🔄 آخرین بروزرسانی: {self._get_current_time()}"""

            self.bot.send_message(message.chat.id, stats_text)

        except Exception as e:
            logger.error(f"Error in handle_general_stats: {e}")
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message())

    def handle_user_management(self, message):
        """Handle user management request"""
        if not self.db.is_admin(message.from_user.id):
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message("permission_denied"))
            return

        self.bot.send_message(
            message.chat.id,
            "👥 مدیریت کاربران\n\nلطفا عملیات مورد نظر را انتخاب کنید:",
            reply_markup=self.keyboard_manager.get_admin_panel_keyboard()
        )

    def handle_content_management(self, message):
        """Handle content management request"""
        if not self.db.is_admin(message.from_user.id):
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message("permission_denied"))
            return

        self.bot.send_message(
            message.chat.id,
            "📁 مدیریت محتوا\n\nلطفا دسته‌بندی مورد نظر را انتخاب کنید:",
            reply_markup=self.keyboard_manager.get_content_management_keyboard()
        )

    def handle_add_music_menu(self, message):
        """Handle add music menu request"""
        if not self.db.is_admin(message.from_user.id):
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message("permission_denied"))
            return

        self.bot.send_message(
            message.chat.id,
            "🎵 افزودن موزیک\n\nلطفا دسته‌بندی مورد نظر را انتخاب کنید:",
            reply_markup=self.keyboard_manager.get_content_management_keyboard()
        )

    def handle_add_text_menu(self, message):
        """Handle add text menu request"""
        if not self.db.is_admin(message.from_user.id):
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message("permission_denied"))
            return

        self.bot.send_message(
            message.chat.id,
            "📝 افزودن متن\n\nلطفا دسته‌بندی مورد نظر را انتخاب کنید:",
            reply_markup=self.keyboard_manager.get_content_management_keyboard()
        )

    def handle_system_settings(self, message):
        """Handle system settings request"""
        if not self.db.is_admin(message.from_user.id):
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message("permission_denied"))
            return

        self.bot.send_message(
            message.chat.id,
            "⚙️ تنظیمات سیستم\n\nلطفا بخش مورد نظر را انتخاب کنید:",
            reply_markup=self.keyboard_manager.get_system_settings_keyboard()
        )

    def handle_system_tools(self, message):
        """Handle system tools request"""
        if not self.db.is_admin(message.from_user.id):
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message("permission_denied"))
            return

        tools_text = """🔧 ابزارهای سیستم

در حال توسعه...

🔙 برای بازگشت از دکمه بازگشت استفاده کنید."""

        self.bot.send_message(message.chat.id, tools_text)

    # Main menu handlers
    def handle_top_tracks(self, message):
        """Handle top tracks request"""
        self._handle_content_request(message, ContentCategory.TOP_TRACKS)

    def handle_economic_package(self, message):
        """Handle economic package request"""
        self._handle_content_request(message, ContentCategory.ECONOMIC_PACKAGE)

    def handle_vip_package(self, message):
        """Handle VIP package request"""
        self._handle_content_request(message, ContentCategory.VIP_PACKAGE)

    def handle_contact_us(self, message):
        """Handle contact us request"""
        self.bot.send_message(message.chat.id, Messages.CONTACT_INFO)

    def _handle_content_request(self, message, category: str):
        """Handle content request for any category"""
        try:
            contents = self.db.get_content_by_category(category)
            category_display = self.db.get_category_display_name(category)

            if not category_display:
                self.bot.send_message(
                    message.chat.id, self.formatter.format_error_message())
                return

            # Send text content
            text_content = self.formatter.format_content_list(
                contents, category_display)
            self.bot.send_message(message.chat.id, text_content)

            # Send music files
            for music_content in contents.get('music', []):
                if music_content.get('file_id'):
                    try:
                        self.bot.send_document(
                            message.chat.id, music_content['file_id'])
                    except ApiTelegramException as e:
                        logger.error(f"Error sending music file: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error in _handle_content_request: {e}")
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message())

    # Admin panel handlers
    def handle_admin_panel(self, message):
        """Handle admin panel request"""
        if not self.db.is_admin(message.from_user.id):
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message("permission_denied"))
            return

        self.bot.send_message(
            message.chat.id,
            Messages.ADMIN_PANEL_WELCOME,
            reply_markup=self.keyboard_manager.get_admin_panel_keyboard()
        )

    def handle_user_panel(self, message):
        """Handle user panel request"""
        self.bot.send_message(
            message.chat.id,
            "👤 پنل کاربری\n\nبه پنل کاربری خوش آمدید! لطفا گزینه مورد نظر را انتخاب کنید.",
            reply_markup=self.keyboard_manager.get_user_panel_keyboard()
        )

    def handle_user_info(self, message):
        """Handle user information request"""
        user_id = message.from_user.id
        user_data = self.db.get_user(user_id)

        if not user_data:
            self.bot.send_message(
                message.chat.id,
                "لطفا از دستور /start استفاده کنید تا ثبت نام کنید. 🤖"
            )
            return

        info_text = self.formatter.format_user_info(user_data)
        self.bot.send_message(message.chat.id, info_text)

    def handle_user_stats(self, message):
        """Handle user stats request"""
        user_id = message.from_user.id
        user_data = self.db.get_user(user_id)

        if not user_data:
            self.bot.send_message(
                message.chat.id,
                "لطفا از دستور /start استفاده کنید تا ثبت نام کنید. 🤖"
            )
            return

        stats_text = self.formatter.format_user_stats(user_data)
        self.bot.send_message(message.chat.id, stats_text)

    def handle_user_settings(self, message):
        """Handle user settings request"""
        user_id = message.from_user.id
        user_data = self.db.get_user(user_id)

        if not user_data:
            self.bot.send_message(
                message.chat.id,
                "لطفا از دستور /start استفاده کنید تا ثبت نام کنید. 🤖"
            )
            return

        settings_text = """⚙️ تنظیمات کاربری

🔧 تنظیمات موجود:
• 📱 تغییر شماره تلفن
• 🗺️ تغییر استان
• 🏙️ تغییر شهر
• 🔔 تنظیمات اعلانات

برای تغییر هر یک از این موارد، لطفا با پشتیبانی تماس بگیرید."""

        self.bot.send_message(message.chat.id, settings_text)

    def handle_guide(self, message):
        """Handle guide request"""
        guide_text = """📋 راهنمای استفاده از تکست بخر

🎵 محتوای موزیک:
• 🔥 پر بازدید ترین ترک ها: محبوب‌ترین آهنگ‌ها
• 💰 پکیج اقتصادی: آهنگ‌های با قیمت مناسب
• 👑 پکیج مگاهیت VIP: آهنگ‌های ویژه و لوکس

👤 خدمات کاربری:
• 📞 ارتباط با ما: تماس با پشتیبانی
• ℹ️ درباره ما: اطلاعات بیشتر درباره تکست بخر
• 📋 راهنما: همین پیام
• ⚙️ تنظیمات: تنظیمات حساب کاربری

🔐 حساب کاربری:
• 👤 اطلاعات من: نمایش اطلاعات شخصی
• 📊 آمار من: آمار استفاده از ربات

💡 نکات مهم:
• برای دسترسی به محتوا ابتدا ثبت نام کنید
• از دکمه /start برای شروع استفاده استفاده کنید
• در صورت مشکل با پشتیبانی تماس بگیرید"""

        self.bot.send_message(message.chat.id, guide_text)

    def handle_back_to_main(self, message):
        """Handle back to main menu"""
        if self.db.is_admin(message.from_user.id):
            self.bot.send_message(
                message.chat.id,
                "🔙 بازگشت به صفحه اصلی\n\nبه پنل مدیریت خوش آمدید!",
                reply_markup=self.keyboard_manager.get_admin_choice_keyboard()
            )
        else:
            self.bot.send_message(
                message.chat.id,
                "🔙 بازگشت به صفحه اصلی\n\nبه تکست بخر خوش آمدید!",
                reply_markup=self.keyboard_manager.get_main_menu_keyboard()
            )

    def handle_list_users(self, message):
        """Handle list users request with professional interface"""
        if not self.db.is_admin(message.from_user.id):
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message("permission_denied"))
            return

        try:
            # Get first page of users
            result = self.db.get_users_paginated(page=1, per_page=10)
            users = result['users']
            total_users = result['total']
            total_pages = result['total_pages']

            # Format message and keyboard
            message_text = self.formatter.format_professional_user_list(
                users, 1, total_pages, total_users)
            keyboard = self.keyboard_manager.get_user_list_keyboard(
                users, 1, total_pages)

            self.bot.send_message(
                message.chat.id, message_text, reply_markup=keyboard, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error in handle_list_users: {e}")
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message())

    def handle_add_admin_prompt(self, message):
        """Handle add admin prompt"""
        if not self.db.is_admin(message.from_user.id):
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message("permission_denied"))
            return

        self.session_manager.start_admin_action(
            message.from_user.id, 'add_admin')
        self.bot.send_message(
            message.chat.id,
            "🛡️ افزودن ادمین جدید\n\n"
            "لطفا شناسه عددی کاربر را برای افزودن به عنوان ادمین وارد کنید.\n\n"
            "⚠️ توجه: کاربر باید ابتدا در ربات ثبت نام کرده باشد.\n"
            "🔢 شناسه کاربری را وارد کنید:"
        )

    def handle_admin_id_input(self, message):
        """Handle admin ID input"""
        try:
            user_id = message.from_user.id

            if not self.validator.validate_user_id(message.text):
                self.bot.send_message(
                    message.chat.id, self.formatter.format_error_message("invalid_input"))
                return

            admin_id = int(message.text)

            # Check if user exists first
            existing_user = self.db.get_user(admin_id)

            if not existing_user:
                self.bot.send_message(
                    message.chat.id,
                    f"❌ کاربر با شناسه {admin_id} در سیستم ثبت نام نکرده است.\n\n"
                    f"لطفا ابتدا کاربر را با دستور /start ثبت نام کنید، سپس دوباره تلاش کنید."
                )
                self.session_manager.clear_admin_session(user_id)
                return

            # Check if user is already an admin
            if existing_user['role'] in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                role_text = "ادمین اصلی" if existing_user['role'] == UserRole.SUPER_ADMIN else "ادمین"
                self.bot.send_message(
                    message.chat.id,
                    f"⚠️ کاربر با شناسه {admin_id} قبلاً به عنوان {role_text} تعریف شده است."
                )
                self.session_manager.clear_admin_session(user_id)
                return

            # Update user role to admin
            success = self.db.update_user_role(admin_id, UserRole.ADMIN)

            if success:
                user_name = f"{existing_user.get('first_name', 'نامشخص')} {existing_user.get('last_name', 'نامشخص')}"
                self.bot.send_message(
                    message.chat.id,
                    f"✅ کاربر {user_name} (شناسه: {admin_id}) با موفقیت به عنوان ادمین اضافه شد.\n\n"
                    f"🛡️ این کاربر اکنون دسترسی کامل به پنل ادمین دارد."
                )
            else:
                self.bot.send_message(
                    message.chat.id, self.formatter.format_error_message())

            self.session_manager.clear_admin_session(user_id)

        except Exception as e:
            logger.error(f"Error in handle_admin_id_input: {e}")
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message())

    def handle_add_content(self, message, category: str, content_type: str):
        """Handle add content request"""
        if not self.db.is_admin(message.from_user.id):
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message("permission_denied"))
            return

        self.session_manager.start_admin_action(
            message.from_user.id, f'add_{content_type}', category)

        if content_type == 'music':
            self.bot.send_message(
                message.chat.id, "لطفا فایل موزیک را ارسال کنید. 🎵")
        else:
            self.bot.send_message(
                message.chat.id, "لطفا متن اولیه را وارد کنید. 📝")

    def handle_admin_music(self, message):
        """Handle admin music upload"""
        try:
            user_id = message.from_user.id
            session = self.session_manager.get_admin_session(user_id)

            if not session or session.get('admin_action') != 'add_music':
                return

            # Get file info
            if message.audio:
                file_id = message.audio.file_id
                file_size = message.audio.file_size
            elif message.document:
                file_id = message.document.file_id
                file_size = message.document.file_size
            else:
                self.bot.send_message(
                    message.chat.id, "لطفا فایل موزیک ارسال کنید.")
                return

            # Update session
            self.session_manager.update_admin_session(user_id, {
                'file_id': file_id,
                'file_size': file_size,
                'step': 'text'
            })

            self.bot.send_message(
                message.chat.id, "موزیک دریافت شد. حالا لطفا متن اولیه را وارد کنید. 📝")

        except Exception as e:
            logger.error(f"Error in handle_admin_music: {e}")
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message())

    def handle_admin_text(self, message):
        """Handle admin text input"""
        try:
            user_id = message.from_user.id
            session = self.session_manager.get_admin_session(user_id)

            if not session:
                return

            text = self.validator.sanitize_text(message.text)

            if not self.validator.validate_content_text(text):
                self.bot.send_message(
                    message.chat.id, self.formatter.format_error_message("invalid_input"))
                return

            # Add content to database
            success = self.db.add_content(
                category_name=session.get('category', ''),
                content_type=session.get('admin_action').replace('add_', ''),
                content=text,
                file_id=session.get('file_id'),
                file_size=session.get('file_size'),
                created_by=user_id
            )

            if success:
                self.bot.send_message(
                    message.chat.id, self.formatter.format_success_message("content_added"))
            else:
                self.bot.send_message(
                    message.chat.id, self.formatter.format_error_message("database_error"))

            self.session_manager.clear_admin_session(user_id)

        except Exception as e:
            logger.error(f"Error in handle_admin_text: {e}")
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message())

    def handle_default(self, message):
        """Handle default messages"""
        self.bot.reply_to(
            message, "لطفا از دستور /start استفاده کنید تا ثبت نام کنید. 🤖")

    # Callback handlers for user management
    def handle_user_list_callback(self, call):
        """Handle user list pagination callbacks"""
        try:
            if not self.db.is_admin(call.from_user.id):
                self.bot.answer_callback_query(
                    call.id, "شما دسترسی لازم را ندارید. ❌")
                return

            data_parts = call.data.split('_')
            if len(data_parts) >= 3:
                page = int(data_parts[2])
                search = data_parts[3] if len(
                    data_parts) > 3 and data_parts[3] else None
            else:
                page = 1
                search = None

            result = self.db.get_users_paginated(
                page=page, per_page=10, search=search)
            users = result['users']
            total_users = result['total']
            total_pages = result['total_pages']

            message_text = self.formatter.format_professional_user_list(
                users, page, total_pages, total_users, search)
            keyboard = self.keyboard_manager.get_user_list_keyboard(
                users, page, total_pages, search)

            self.bot.edit_message_text(
                message_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            self.bot.answer_callback_query(call.id)

        except Exception as e:
            logger.error(f"Error in handle_user_list_callback: {e}")
            self.bot.answer_callback_query(call.id, "خطایی رخ داده است. ❌")

    def handle_user_detail_callback(self, call):
        """Handle user detail view callbacks"""
        try:
            if not self.db.is_admin(call.from_user.id):
                self.bot.answer_callback_query(
                    call.id, "شما دسترسی لازم را ندارید. ❌")
                return

            user_id = int(call.data.split('_')[2])
            user = self.db.get_user(user_id)

            if not user:
                self.bot.answer_callback_query(call.id, "کاربر یافت نشد. ❌")
                return

            message_text = self.formatter.format_user_detail(user)
            keyboard = self.keyboard_manager.get_user_detail_keyboard(
                user_id,
                user['role'],
                not user.get('is_active', 1)
            )

            self.bot.edit_message_text(
                message_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            self.bot.answer_callback_query(call.id)

        except Exception as e:
            logger.error(f"Error in handle_user_detail_callback: {e}")
            self.bot.answer_callback_query(call.id, "خطایی رخ داده است. ❌")

    def handle_ban_user_callback(self, call):
        """Handle ban user callback"""
        try:
            if not self.db.is_admin(call.from_user.id):
                self.bot.answer_callback_query(
                    call.id, "شما دسترسی لازم را ندارید. ❌")
                return

            user_id = int(call.data.split('_')[2])
            success = self.db.ban_user(user_id)

            if success:
                self.bot.answer_callback_query(call.id, "کاربر بن شد. 🚫")
                # Refresh the user detail view
                self.handle_user_detail_callback(call)
            else:
                self.bot.answer_callback_query(
                    call.id, "خطا در بن کردن کاربر. ❌")

        except Exception as e:
            logger.error(f"Error in handle_ban_user_callback: {e}")
            self.bot.answer_callback_query(call.id, "خطایی رخ داده است. ❌")

    def handle_unban_user_callback(self, call):
        """Handle unban user callback"""
        try:
            if not self.db.is_admin(call.from_user.id):
                self.bot.answer_callback_query(
                    call.id, "شما دسترسی لازم را ندارید. ❌")
                return

            user_id = int(call.data.split('_')[2])
            success = self.db.unban_user(user_id)

            if success:
                self.bot.answer_callback_query(call.id, "کاربر آزاد شد. ✅")
                # Refresh the user detail view
                self.handle_user_detail_callback(call)
            else:
                self.bot.answer_callback_query(
                    call.id, "خطا در آزاد کردن کاربر. ❌")

        except Exception as e:
            logger.error(f"Error in handle_unban_user_callback: {e}")
            self.bot.answer_callback_query(call.id, "خطایی رخ داده است. ❌")

    def handle_make_admin_callback(self, call):
        """Handle make admin callback"""
        try:
            if not self.db.is_admin(call.from_user.id):
                self.bot.answer_callback_query(
                    call.id, "شما دسترسی لازم را ندارید. ❌")
                return

            user_id = int(call.data.split('_')[2])
            success = self.db.update_user_role(user_id, UserRole.ADMIN)

            if success:
                self.bot.answer_callback_query(
                    call.id, "کاربر به ادمین تبدیل شد. 🛡️")
                # Refresh the user detail view
                self.handle_user_detail_callback(call)
            else:
                self.bot.answer_callback_query(
                    call.id, "خطا در تبدیل کاربر به ادمین. ❌")

        except Exception as e:
            logger.error(f"Error in handle_make_admin_callback: {e}")
            self.bot.answer_callback_query(call.id, "خطایی رخ داده است. ❌")

    def handle_make_user_callback(self, call):
        """Handle make user callback"""
        try:
            if not self.db.is_admin(call.from_user.id):
                self.bot.answer_callback_query(
                    call.id, "شما دسترسی لازم را ندارید. ❌")
                return

            user_id = int(call.data.split('_')[2])
            success = self.db.update_user_role(user_id, UserRole.USER)

            if success:
                self.bot.answer_callback_query(
                    call.id, "کاربر به کاربر عادی تبدیل شد. 👤")
                # Refresh the user detail view
                self.handle_user_detail_callback(call)
            else:
                self.bot.answer_callback_query(
                    call.id, "خطا در تبدیل کاربر به کاربر عادی. ❌")

        except Exception as e:
            logger.error(f"Error in handle_make_user_callback: {e}")
            self.bot.answer_callback_query(call.id, "خطایی رخ داده است. ❌")

    def handle_user_stats_callback(self, call):
        """Handle user stats callback"""
        try:
            if not self.db.is_admin(call.from_user.id):
                self.bot.answer_callback_query(
                    call.id, "شما دسترسی لازم را ندارید. ❌")
                return

            user_id = int(call.data.split('_')[2])
            user = self.db.get_user(user_id)

            if not user:
                self.bot.answer_callback_query(call.id, "کاربر یافت نشد. ❌")
                return

            message_text = self.formatter.format_user_stats(user)
            keyboard = self.keyboard_manager.get_user_detail_keyboard(
                user_id,
                user['role'],
                not user.get('is_active', 1)
            )

            self.bot.edit_message_text(
                message_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            self.bot.answer_callback_query(call.id)

        except Exception as e:
            logger.error(f"Error in handle_user_stats_callback: {e}")
            self.bot.answer_callback_query(call.id, "خطایی رخ داده است. ❌")

    def handle_message_user_callback(self, call):
        """Handle message user callback"""
        try:
            if not self.db.is_admin(call.from_user.id):
                self.bot.answer_callback_query(
                    call.id, "شما دسترسی لازم را ندارید. ❌")
                return

            user_id = int(call.data.split('_')[2])
            target_user = self.db.get_user(user_id)

            if not target_user:
                self.bot.answer_callback_query(call.id, "کاربر یافت نشد. ❌")
                return

            # Start message session
            self.session_manager.start_admin_action(
                call.from_user.id, 'send_message')
            self.session_manager.update_admin_session(call.from_user.id, {
                'target_user_id': user_id,
                'step': 'message'
            })

            target_name = f"{target_user.get('first_name', 'نامشخص')} {target_user.get('last_name', 'نامشخص')}"

            self.bot.edit_message_text(
                f"💬 ارسال پیام به کاربر\n\n"
                f"👤 گیرنده: {target_name}\n"
                f"🆔 شناسه: {user_id}\n"
                f"📞 شماره: {target_user.get('phone', 'نامشخص')}\n\n"
                f"لطفا پیام خود را ارسال کنید:",
                call.message.chat.id,
                call.message.message_id
            )
            self.bot.answer_callback_query(
                call.id, "حالا پیام خود را ارسال کنید")

        except Exception as e:
            logger.error(f"Error in handle_message_user_callback: {e}")
            self.bot.answer_callback_query(call.id, "خطایی رخ داده است. ❌")

    def handle_user_search_callback(self, call):
        """Handle user search callback"""
        try:
            if not self.db.is_admin(call.from_user.id):
                self.bot.answer_callback_query(
                    call.id, "شما دسترسی لازم را ندارید. ❌")
                return

            keyboard = self.keyboard_manager.get_user_search_keyboard()

            self.bot.edit_message_text(
                "🔍 جستجوی کاربران\n\nلطفا نوع جستجو را انتخاب کنید:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard
            )
            self.bot.answer_callback_query(call.id)

        except Exception as e:
            logger.error(f"Error in handle_user_search_callback: {e}")
            self.bot.answer_callback_query(call.id, "خطایی رخ داده است. ❌")

    def handle_search_type_callback(self, call):
        """Handle search type selection callback"""
        try:
            if not self.db.is_admin(call.from_user.id):
                self.bot.answer_callback_query(
                    call.id, "شما دسترسی لازم را ندارید. ❌")
                return

            # name, phone, province, role
            search_type = call.data.split('_')[2]

            # Start search session
            self.session_manager.start_admin_action(
                call.from_user.id, 'search_users')
            self.session_manager.update_admin_session(call.from_user.id, {
                'search_type': search_type,
                'step': 'input'
            })

            search_prompts = {
                'name': 'لطفا نام یا نام خانوادگی کاربر را وارد کنید:',
                'phone': 'لطفا شماره تلفن کاربر را وارد کنید:',
                'province': 'لطفا نام استان را وارد کنید:',
                'role': 'لطفا نقش کاربر را وارد کنید (user, admin, super_admin):'
            }

            prompt = search_prompts.get(
                search_type, 'لطفا عبارت جستجو را وارد کنید:')

            self.bot.edit_message_text(
                f"🔍 جستجوی کاربران\n\n{prompt}",
                call.message.chat.id,
                call.message.message_id
            )
            self.bot.answer_callback_query(call.id)

        except Exception as e:
            logger.error(f"Error in handle_search_type_callback: {e}")
            self.bot.answer_callback_query(call.id, "خطایی رخ داده است. ❌")

    def handle_search_input(self, message):
        """Handle search input from admin"""
        try:
            user_id = message.from_user.id
            session = self.session_manager.get_admin_session(user_id)

            if not session or session.get('admin_action') != 'search_users':
                return

            search_term = message.text.strip()
            search_type = session.get('search_type', 'name')

            # Perform search based on type
            if search_type == 'role':
                # For role search, we need to modify the database query
                result = self.db.get_users_paginated(
                    page=1, per_page=50, search=None)
                # Filter by role
                filtered_users = [
                    user for user in result['users'] if user['role'] == search_term]
                result['users'] = filtered_users
                result['total'] = len(filtered_users)
            else:
                result = self.db.get_users_paginated(
                    page=1, per_page=50, search=search_term)

            users = result['users']
            total_users = result['total']
            total_pages = result['total_pages']

            if not users:
                self.bot.send_message(
                    message.chat.id,
                    f"🔍 هیچ کاربری با '{search_term}' یافت نشد.",
                    reply_markup=self.keyboard_manager.get_user_search_keyboard()
                )
            else:
                message_text = self.formatter.format_professional_user_list(
                    users, 1, total_pages, total_users, search_term)
                keyboard = self.keyboard_manager.get_user_list_keyboard(
                    users, 1, total_pages, search_term)

                self.bot.send_message(
                    message.chat.id, message_text, reply_markup=keyboard, parse_mode='Markdown')

            # Clear search session
            self.session_manager.clear_admin_session(user_id)

        except Exception as e:
            logger.error(f"Error in handle_search_input: {e}")
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message())

    def handle_admin_message_input(self, message):
        """Handle admin message input to send to user"""
        try:
            user_id = message.from_user.id
            session = self.session_manager.get_admin_session(user_id)

            if not session or session.get('admin_action') != 'send_message':
                return

            target_user_id = session.get('target_user_id')
            message_text = message.text.strip()

            if not message_text:
                self.bot.send_message(
                    message.chat.id, "❌ پیام نمی‌تواند خالی باشد.")
                return

            # Get admin info
            admin_user = self.db.get_user(user_id)
            admin_name = f"{admin_user.get('first_name', 'ادمین')} {admin_user.get('last_name', '')}"

            # Format message for target user
            formatted_message = f"📨 پیام از ادمین\n\n"
            formatted_message += f"👤 فرستنده: {admin_name}\n"
            formatted_message += f"📅 تاریخ: {self._get_current_time()}\n\n"
            formatted_message += f"💬 پیام:\n{message_text}\n\n"
            formatted_message += f"📞 برای پاسخ، با ادمین تماس بگیرید."

            try:
                # Send message to target user
                self.bot.send_message(target_user_id, formatted_message)

                # Confirm to admin
                target_user = self.db.get_user(target_user_id)
                target_name = f"{target_user.get('first_name', 'نامشخص')} {target_user.get('last_name', 'نامشخص')}"

                self.bot.send_message(
                    message.chat.id,
                    f"✅ پیام با موفقیت ارسال شد!\n\n"
                    f"👤 گیرنده: {target_name}\n"
                    f"🆔 شناسه: {target_user_id}\n"
                    f"📞 شماره: {target_user.get('phone', 'نامشخص')}\n\n"
                    f"💬 پیام ارسالی:\n{message_text}"
                )

            except Exception as e:
                logger.error(
                    f"Error sending message to user {target_user_id}: {e}")
                self.bot.send_message(
                    message.chat.id,
                    f"❌ خطا در ارسال پیام به کاربر {target_user_id}.\n\n"
                    f"ممکن است کاربر ربات را بلاک کرده باشد یا از ربات خارج شده باشد."
                )

            # Clear session
            self.session_manager.clear_admin_session(user_id)

        except Exception as e:
            logger.error(f"Error in handle_admin_message_input: {e}")
            self.bot.send_message(
                message.chat.id, self.formatter.format_error_message())

    def _get_current_time(self):
        """Get current time in Persian format"""
        try:
            from datetime import datetime
            now = datetime.now()
            return now.strftime('%Y/%m/%d %H:%M')
        except:
            return "نامشخص"

    def run(self):
        """Start the bot"""
        try:
            logger.info("Starting bot...")
            self.bot.polling(none_stop=True)
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            raise
