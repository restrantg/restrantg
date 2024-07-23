import json
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.command import Command
import os
import sys
from config import BOT_TOKEN, RESTRAN_ID

if not BOT_TOKEN or not RESTRAN_ID:
    print("错误：缺少必要的环境变量。请确保设置了 BOT_TOKEN 和 RESTRAN_ID。")
    sys.exit(1)

# 设置日志级别
logging.basicConfig(level=logging.INFO)

# 创建机器人和调度器实例
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# 定义用户状态
class UserState(StatesGroup):
    language = State()
    waiting_for_question = State()

# 加载语言文件
with open('langs/chn_lang.json', 'r', encoding='utf-8') as f:
    chn_lang = json.load(f)

with open('langs/eng_lang.json', 'r', encoding='utf-8') as f:
    eng_lang = json.load(f)

# 处理 /start 命令
@dp.message(Command("start"))
async def start_command(message: types.Message):
    # 创建内联键盘
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🇨🇳", callback_data="lang_cn"),
         types.InlineKeyboardButton(text="🇺🇸", callback_data="lang_en")]
    ])
    await message.answer("中文: 选择机器人语言:\nENG: Choose Lang in bot:", reply_markup=keyboard)

# 处理语言选择
@dp.callback_query(F.data.startswith('lang_'))
async def process_language_selection(callback_query: types.CallbackQuery, state: FSMContext):
    lang = callback_query.data.split('_')[1]
    await state.update_data(language=lang)
    
    # 根据选择的语言设置文本
    if lang == 'cn':
        text = chn_lang['portfolio']
        button_text = chn_lang['ask_question']
    else:
        text = eng_lang['portfolio']
        button_text = eng_lang['ask_question']
    
    # 创建"提问"按钮
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=button_text, callback_data="ask_question")]
    ])
    
    # 更新消息
    await callback_query.message.edit_text(text=text, reply_markup=keyboard)

# 处理"提问"按钮
@dp.callback_query(F.data == 'ask_question')
async def process_ask_question(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get('language', 'en')
    
    # 根据语言选择提示文本
    if lang == 'cn':
        text = chn_lang['ask_question_prompt']
    else:
        text = eng_lang['ask_question_prompt']
    
    # 更新消息并设置状态
    await callback_query.message.edit_text(text=text)
    await state.set_state(UserState.waiting_for_question)

# 处理用户问题
@dp.message(UserState.waiting_for_question)
async def process_user_question(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get('language', 'en')
    
    # 发送消息给管理员
    await bot.send_message(RESTRAN_ID, f"发件人：@{message.from_user.username}\n\n留言：{message.text}")
    
    # 删除用户消息
    await message.delete()
    
    # 根据语言选择确认文本
    if lang == 'cn':
        text = chn_lang['message_sent']
    else:
        text = eng_lang['message_sent']
    
    # 更新消息并结束状态
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message.message_id - 1,
                                text=text)
    
    await state.clear()

# 启动机器人
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())