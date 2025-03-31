import json
import logging
import os

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackContext

# 加载 .env 文件
load_dotenv()

# 读取环境变量
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
URL = os.environ.get("URL")
API_KEY = os.environ.get("API_KEY")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        '欢迎使用图床Bot！请直接发送图片以获取返回链接，使用 /help 查看所有命令。')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    commands_text = (
        "/start - 开始使用\n"
        "/help - 显示帮助信息\n"
    )
    await update.message.reply_text(commands_text)


def upload(photo_path):
    headers = {
        'Authorization': f'Bearer {API_KEY}'
    }
    with open(photo_path, 'rb') as f:
        files = {
            'images[]': f
        }
        response = requests.post(f'{URL}/api/upload', files=files, headers=headers)
        # 检查响应
        if response.status_code == 200:
            try:
                response_data = response.json()
                logging.info(f"上传成功: {photo_path} - 响应: {response_data}")
                return response_data['results'][0]
            except json.JSONDecodeError:
                logging.info(f"上传成功: {photo_path} - 响应不是JSON格式")
        else:
            logging.error(f"上传失败: {photo_path} - 状态码: {response.status_code}, 响应: {response.text}")
            raise Exception(f"上传失败: {photo_path} - 状态码: {response.status_code}, 响应: {response.text}")


async def download_and_upload(update: Update,photo_file) -> None:
    # 保存文件路径
    photo_path = os.path.basename(photo_file.file_path)
    await photo_file.download_to_drive(photo_path)

    try:
        result = upload(photo_path)

        if result['status'] == 'success':
            urls = result['urls']
            avif = urls['avif']
            original = urls['original']
            webp = urls['webp']
            markdown_link = f"![image]({URL}/{webp})"

            await update.message.reply_html(
                f"<b>上传成功！</b>\n\n"
                f"<b>原始图片链接</b><pre>{URL}/{original}</pre>\n\n"
                f"<b>AVIF图片链接</b><pre>{URL}/{avif}</pre>\n\n"
                f"<b>WebP图片链接</b><pre>{URL}/{webp}</pre>\n\n"
                f"<b>Markdown</b><pre>{markdown_link}</pre>\n\n",
            )
        else:
            await update.message.reply_text(f"图片上传失败：{result['status']}")
    except Exception as e:
        logging.error(f'Error during image uploading: {e}')
        await update.message.reply_text(f'图片上传过程中出现错误。{e}')
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo_file = await context.bot.get_file(update.message.photo[-1].file_id)
    await download_and_upload(update, photo_file)


async def handle_non_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.delete()

async def handle_document_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await context.bot.get_file(update.message.document.file_id)
    await download_and_upload(update, photo_file)

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.IMAGE, handle_document_image))
    application.add_handler(MessageHandler(~filters.PHOTO & ~filters.COMMAND & filters.Document.IMAGE, handle_non_photo))

    application.run_polling()


if __name__ == '__main__':
    main()
