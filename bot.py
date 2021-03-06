from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import json
from PIL import Image
import io
import logging
import requests
from requests_toolbelt import MultipartEncoder
import os


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def send_tutorial(update):
    update.message.reply_text('用法:\n請把假新聞的連結發結Telegram bot，Telegram bot 會自動把新聞上載到伺服器(https://fakenews.g0vhk.io/)。')

def start(bot, update):
    """Send a message when the command /start is issued."""
    send_tutorial(update)




HOST = os.environ['HOST']
TOKEN = os.environ['TOKEN']
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']

def send_link_report(url):
    uri = '/api/upload_link_report'
    headers = {'Authorization': 'Token ' + TOKEN, 'Content-Type': 'application/json'}
    r = requests.post(HOST + uri, headers=headers, json={'url': url})
    logging.info(r.json())
    if r.status_code / 100 < 5:
        j = r.json()
        return j
    return None

def send_image_report(buf, description):
    uri = '/api/upload_image_report'
    m = MultipartEncoder(
            fields={'image':('a.jpg', buf, 'image/jpeg'), 'description': description}
            )
    headers = {'Authorization': 'Token ' + TOKEN, 'Content-Type': m.content_type}
    r = requests.post(HOST + uri, headers=headers, data=m)
    logging.info('status: %d' % r.status_code)
    if r.status_code == 201:
        j = r.json()
        return j
    if r.status_code / 100 < 5:
        return r.json()
    else:
        return None



def echo(bot, update):
    """Echo the user message."""
    message = update.message
    message_from = message.chat.id
    chat = message.chat
    if chat.type != 'private':
        return
    try:
        if len(message.photo) > 0:
            photo = message.photo[-1]
            print(photo)
            image_file = bot.getFile(photo.file_id)
            buf = image_file.download_as_bytearray()
            bio = io.BytesIO(buf)
            image = Image.open(bio)
            width, height = image.size
            logging.info('%d, %d' % (width, height))
            bio.seek(0)
            result = send_image_report(bio, message.caption)
            if result is not None:
                if 'reason' in result:
                    raise Exception(result['reason'])
                elif 'too_many' in result:
                    update.message.reply_text('今日的隊列已滿了。')
                elif result.get('result', '') == 'already_existed':
                    update.message.reply_text('已有相同的舉報 。')
                else:
                    update.message.reply_text('謝謝你，已新增了一個舉報。')
                return
        elif len(message.entities) > 0:
            urls = [e for e in message.entities if e.type == 'url']
            if len(urls) > 0:
                url_entity = urls[0]
                print(url_entity)
                logging.debug('full text' +  message.text)
                url = message.text[url_entity.offset: url_entity.length]
                logging.debug('url:' + url)
                result = send_link_report(url)
                print('result')
                print(result)
                if result is not None:
                    print('chckecing')
                    if result.get('result', '') == 'already_existed':
                        update.message.reply_text('已有相同的舉報 。')
                    elif 'too_many' in result:
                        update.message.reply_text('今日的隊列已滿了。')
                    else:
                        update.message.reply_text('謝謝你，已新增了一個舉報。')
                    return
        elif len(message.text) > 0:
            if len(message.text) <= 30:
                update.message.reply_text('文字最少要有30字。')
                return

        send_tutorial(update)
    except Exception as e:
        logging.error(e, exc_info=True)
        update.message.reply_text('發生異常，請重試。')

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text | Filters.photo | Filters.document, echo))
    while True:
        updater.start_polling(timeout=60)
        updater.idle()


if __name__ == '__main__':
    main()
