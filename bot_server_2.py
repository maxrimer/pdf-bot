import os
import shutil
from config import token
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from gtts import gTTS
import pdfplumber
import aiofiles
import PyPDF2
from pathlib import Path


storage = MemoryStorage()
bot = Bot(token=token)
dp = Dispatcher(bot, storage=storage)
#temp_dest = r'C:\Users\PChelper\PycharmProjects\PDFBot\dowloaded_pdfs\documents'
temp_dest = r'/root/pdf_bot/downloaded_pdfs'


@dp.message_handler(commands=['start'])
async def start(message=types.Message):
    global start_keyboard
    start_buttons = ['Отправить документ', 'Помощь']
    start_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    start_keyboard.row(start_buttons[0], start_buttons[1])
    await bot.send_sticker(chat_id=message.from_user.id,
                           sticker='CAACAgIAAxkBAAEDOBZhhBihbfpvfcuhoOmTscQ1DKUqPwACVAADQbVWDGq3-McIjQH6IQQ')
    await bot.send_message(chat_id=message.from_user.id,
                           text='Приветствую! Меня зовут AudioBot\U0001F916. Отправь мне документ в pdf-формате и я верну его в mp3-формате.',
                           reply_markup=start_keyboard)


class FSMSReceive_Doc(StatesGroup):
    set_doc = State()
    set_lang = State()


@dp.message_handler(Text(equals='Помощь'))
async def get_pdf_file(message: types.Message):
    await bot.send_message(chat_id=message.from_user.id, text='Бот отправляет аудио версию присланного pdf-документа. '
                                                              'Для отправки документа необходимо сначала ввести команду "Отправить документ", далее выбрать нужный файл '
                                                              'и выбрать язык. В зависимости от размера документа, вывод результата может занять от одной до двадцати минут. '
                                                              'На данный момент бот поддерживает английский и русский языки. В связи с ограничениями по размеру отправляемых файлов, '
                                                              'максимальное количество страниц в файле не должно превышать 70',

                           reply_markup=start_keyboard)


@dp.message_handler(state='*', commands='отмена')
@dp.message_handler(Text(equals='❌ Отмена', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMSReceive_Doc):
    current_state = await state.get_state()
    if current_state is None:
        return
    #if os.path.exists(temp_dest) and os.listdir(temp_dest):
        #shutil.rmtree(temp_dest, ignore_errors=True)
    user_id = message.from_user.id
    user_dir = f'{user_id}_folder'
    destination_dir = os.path.join(temp_dest, user_dir)
    if os.path.exists(destination_dir) and os.listdir(destination_dir):
        shutil.rmtree(destination_dir, ignore_errors=True)
    await state.finish()
    await bot.send_sticker(chat_id=message.from_user.id, sticker='CAACAgIAAxkBAAEDaWRhqyZoAw1PM5lbG56lSPDcL4SBtAACVgADQbVWDNWTZQVPrTRWIgQ',
                           reply_markup=start_keyboard)


@dp.message_handler(Text(equals='Отправить документ'), state=None)
async def get_pdf_file(message: types.Message):
    global cancel_keyboard
    await FSMSReceive_Doc.set_doc.set()
    cancel_buttons = ['❌ Отмена']
    cancel_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    cancel_keyboard.add(*cancel_buttons)
    await bot.send_message(chat_id=message.from_user.id, text='Отправь документ в pdf-формате', reply_markup=cancel_keyboard)


@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def download_file(message: types.Message):
    await bot.send_message(chat_id=message.from_user.id, text='Для правильной работы бота необходимо отправить документ после отправки команды'
                                                              ' "Отправить документ"',
                           reply_markup=start_keyboard)


@dp.message_handler(content_types=types.ContentType.DOCUMENT, state=FSMSReceive_Doc.set_doc)
async def download_file(message: types.Message, state: FSMSReceive_Doc):
    global name_without_ext, destination_dir, destination_dir_new, complete_dest
    try:
        file = message.document
        file_name = file.file_name
        ext = len(file_name) - 4
        name_without_ext = file_name[:ext]
        if file_name[ext:] == '.pdf':
            user_id = message.from_user.id
            #destination_dir = r'C:\Users\PChelper\PycharmProjects\PDFBot\dowloaded_pdfs'
            user_dir = f'{user_id}_folder'
            destination_dir = os.path.join(temp_dest, user_dir)
            os.makedirs(destination_dir)
            await file.download(destination_dir=destination_dir)
            destination_dir_new = os.path.join(destination_dir, 'documents')
            file = os.listdir(destination_dir_new)[0]
            complete_dest = destination_dir_new + '/' + file
            doc = PyPDF2.PdfFileReader(open(complete_dest, mode='rb'))
            if doc.numPages <= 70:
                await FSMSReceive_Doc.next()
                lang_buttons = ['Русский', 'Английский', '❌ Отмена']
                lang_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                lang_keyboard.row(lang_buttons[0], lang_buttons[1]).add(lang_buttons[2])
                await bot.send_message(chat_id=message.from_user.id,
                                           text='Теперь выбери язык текста', reply_markup=lang_keyboard)
            else:
                await bot.send_message(chat_id=message.from_user.id,
                                       text='Превышено максимально допустимое количество страниц!',
                                       reply_markup=start_keyboard)
                await state.finish()
                shutil.rmtree(destination_dir, ignore_errors=True)
        else:
            await bot.send_message(chat_id=message.from_user.id,
                                           text='Неверный формат документа!', reply_markup=start_keyboard)
            await state.finish()
    except:
        if os.path.exists(destination_dir) and os.listdir(destination_dir):
            shutil.rmtree(destination_dir, ignore_errors=True)
        await bot.send_message(chat_id=message.from_user.id,
                               text='Упс! Что-то пошло не по плану... Попробуй отправить файл снова', reply_markup=start_keyboard)
        await state.finish()


@dp.message_handler(state=FSMSReceive_Doc.set_lang)
async def get_lang(message: types.Message, state: FSMSReceive_Doc):
    async with state.proxy() as data:
        data['lang'] = message.text
        if data.get('lang') not in ['Русский', 'Английский']:
            if os.path.exists(destination_dir) and os.listdir(destination_dir):
                shutil.rmtree(destination_dir, ignore_errors=True)
            await bot.send_message(chat_id=message.from_user.id,
                                       text='Неподдерживаемый язык!', reply_markup=start_keyboard)
            await state.finish()
        else:
            await bot.send_message(chat_id=message.from_user.id,
                                       text='Спасибо. Процесс займет от одной до двадцати минут в зависимости от размера документа', reply_markup=cancel_keyboard)
            # #temp_dest = r'C:\Users\PChelper\PycharmProjects\PDFBot\dowloaded_pdfs\documents'
            # #file = os.listdir(temp_dest)[0]
            # destination_dir_new = os.path.join(destination_dir, 'documents')
            # file = os.listdir(destination_dir_new)[0]
            # #complete_dest = temp_dest+'\\'+file
            # complete_dest = destination_dir_new + '/' + file
            with pdfplumber.PDF(open(file=complete_dest, mode='rb')) as pdf:
                pages = [page.extract_text() for page in pdf.pages]
            lang = data.get('lang')
            if lang == 'Английский':
                lang = 'en'
            else:
                lang = 'ru'
            text = ''.join(pages)
            text = text.replace('\n', '')
            my_audio = gTTS(text=text, lang=lang, slow=False)
            #comp_dest_new = temp_dest + '\\' + f'{name_without_ext}.mp3'
            comp_dest_new = destination_dir_new + '/' + f'{name_without_ext}.mp3'
            my_audio.save(comp_dest_new)
            async with aiofiles.open(comp_dest_new, mode='rb') as f:
                await bot.send_audio(chat_id=message.from_user.id, audio=f)
                await bot.send_message(chat_id=message.from_user.id,
                                       text='Результат готов', reply_markup=start_keyboard)
            await state.finish()
            #shutil.rmtree(temp_dest, ignore_errors=True)
            shutil.rmtree(destination_dir, ignore_errors=True)




if __name__ == '__main__':
    executor.start_polling(dp)