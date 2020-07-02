from telegram.ext import Updater, Filters, CommandHandler, MessageHandler, ConversationHandler
from telegram.ext import InlineQueryHandler, CallbackQueryHandler, CallbackContext
from telegram import ReplyKeyboardRemove, ReplyKeyboardMarkup, ParseMode, ChatAction, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup
import json
import requests
from scrapping import get_price, get_site_name, search_unknown_site_tag, site_price_tags, save_new_tag
import data_manager as dm


def check_for_updates(context: CallbackContext):
    copy_info = dm.info.copy()
    for user_id in copy_info:
        for item_name in copy_info[user_id]['items']:
            url = copy_info[user_id]['items'][item_name]['https']
            saved_price = dm.get_saved_price(str(user_id), item_name)
            try:
                new_price = get_price(url)
            except Exception:
                print(f'Some error while parsing {get_site_name(url)}. We will get another try later.')
                tag_type, tag_arg, tag_name = search_unknown_site_tag(url, saved_price)

                if tag_name is not None: 
                    site_price_tags[get_site_name(url)] = [tag_name, tag_type, tag_arg]
                    save_new_tag(site_price_tags)
                try:
                    new_price = get_price(url)
                except:
                    context.bot.send_message(user_id, text=f'Sorry, but your item [{item_name}]({url}) has been deleted and need to be readded, beacause site changed price tag name, please add this item with actual price again, if you want to watch this item further', parse_mode=ParseMode.MARKDOWN, disable_web_page_preview = True)
                    del copy_info[user_id]['items'][item_name]
                    dm.save(copy_info)
                    continue
            if new_price == saved_price:
                print('Equal')
            else:
                dm.info[user_id]['items'][item_name]['price'] = new_price
                dm.save(dm.info)
                context.bot.send_message(user_id, text=f'Item *{item_name}* change the price: *{saved_price} → {new_price}*', parse_mode=ParseMode.MARKDOWN)


def get_user_items_handler(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    user_lists = dm.get_user_items(str(user_id))
    update.message.delete()
    if user_lists:
        update.message.reply_text(f"*Your items:* \n{chr(10).join(' - '.join(sl) for sl in user_lists)}", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview = True)
    else:
        update.message.reply_text(f"*You do not have items, feel free to add some.*", parse_mode=ParseMode.MARKDOWN)


def delete_item_handler(update, context):
    user_id = update.message.from_user.id
    arguments = context.args
    if dm.check_user_exist(str(user_id)) is True:
        if len(arguments) > 0:
            name = ' '.join(arguments)
            deleted = dm.delete_item(str(user_id), name)
            update.message.delete()
            if deleted is True:
                update.message.reply_text(f'*Item {name} deleted*', parse_mode=ParseMode.MARKDOWN)
            else:
                update.message.reply_text(f"*Item {name} doesn't exist*", parse_mode=ParseMode.MARKDOWN)
        else:
            update.message.delete()
            update.message.reply_text(f'*You should type correct name*', parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text(f'You are new here, *{update.message.from_user.username}*, type */start* first', parse_mode=ParseMode.MARKDOWN)
def delete_all_item_handler(update, context):
    user_id = update.message.from_user.id
    if dm.check_user_exist(str(user_id)) is True:
        dm.delete_all_item(str(user_id))
        update.message.reply_text(f'All your items has been deleted.', parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text(f'You are new here, *{update.message.from_user.username}*, type */start* first', parse_mode=ParseMode.MARKDOWN)


def add_item_handler(update, context):
    user_id = update.message.from_user.id
    arguments = context.args
    if dm.check_user_exist(str(user_id)) is True:
        if len(arguments) > 1:
            name = ' '.join(arguments[:-1])
            url = arguments[-1]
            if 'https://' in url or 'http://' in url:
                try:
                    r = requests.head(url)
                    added = dm.add_item(str(user_id), name, url)
                    if added is True:
                        update.message.reply_text(f'Item *{name}* added.', parse_mode=ParseMode.MARKDOWN)
                    elif added is None:
                        update.message.reply_text(f'Unknown site or site change his price tag info. Please, add site by /new command, or type /help to get info.', parse_mode=ParseMode.MARKDOWN)
                    else:
                        update.message.reply_text(f'Item *{name}* already exist.', parse_mode=ParseMode.MARKDOWN)
                except requests.exceptions.ConnectionError:
                    update.message.reply_text(f'Site is not responding, check if site is working or url is correct.', parse_mode=ParseMode.MARKDOWN)
            else:
                update.message.reply_text(f'Url not valid. Example: *https://example.com*', parse_mode=ParseMode.MARKDOWN)
        else:
            update.message.reply_text(f'*You should type correct name and url*', parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text(f'You are new here, *{update.message.from_user.username}*, type */start* first', parse_mode=ParseMode.MARKDOWN)
    update.message.delete()


def add_unknown_site_handler(update, context):
    user_id = update.message.from_user.id
    arguments = context.args
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    if dm.check_user_exist(str(user_id)) is True:
        if len(arguments) > 1:
            url = arguments[0]
            price = ' '.join(arguments[1:])
            site_name = get_site_name(url)
            if 'https://' in url or 'http://' in url:
                try:
                    r = requests.head(url)
                    tag_type, tag_arg, tag_name, json_key = search_unknown_site_tag(url, price)
                    if tag_name is not None:
                        site_price_tags[site_name] = [tag_name, tag_type, tag_arg, json_key]
                        save_new_tag(site_price_tags)
                        update.message.reply_text(f'New site: *{site_name}* has been added. Now, You can add your items on this site. Not need to use /new on this site anymore.', parse_mode=ParseMode.MARKDOWN)
                    else:
                        update.message.reply_text(f'Cannot add site: *{site_name}*, check if you type correct price and url. If so, sorry, but for now, we cannot add this site.', parse_mode=ParseMode.MARKDOWN)
                except requests.exceptions.ConnectionError:
                    update.message.reply_text(f'Site is not responding, check if site is working or url is correct.', parse_mode=ParseMode.MARKDOWN)
            else:
                update.message.reply_text(f'Url not valid. Example: *https://example.com*', parse_mode=ParseMode.MARKDOWN)
        else:
            update.message.delete()
            update.message.reply_text(f'*You should type correct name and url*', parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text(f'You are new here, *{update.message.from_user.username}*, type */start* first', parse_mode=ParseMode.MARKDOWN)
    # update.message.delete()


def help_handler(update, context):
    update.message.delete()
    help_strings = ['*/start* - show menu',
                    '*/add* name url - to add new item - \n_example:_ /add mybackpack https://somesite.com',
                    '*/items* - to show your items',
                    '*/delete* name - to delete item - \n_example:_ /delete mybackpack',
                    '*/deleteall* - to delete all items',
                    '''*/new* - to add new unknown site - \n_example:_ /new https://somesite.com/ 300
    If shop, from where you want to add product is not in available list(To check list, type /start and choose endeed button), you should add that shop to available list. 
    To do that chose product in online store, find price of this product and type command to chat /new *link to product *price.
    Price must be without money symbol. Price must be exacly the same as in shop page. If adding new shop failed, try to type price without penny part.
    For example:
    /new https://www.x-kom.pl/p/498795-telewizor-44-55-philips-55pus7504.html 2 899,00
    or
    /new https://www.x-kom.pl/p/498795-telewizor-44-55-philips-55pus7504.html 2 899''']
    update.message.reply_text(f" \n{chr(10).join(help_strings)}", parse_mode=ParseMode.MARKDOWN)


def get_users(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    # bot.send_photo(chat_id=chat_id, photo=url)
    user_info = dict()
    user_info.update({'id': update.message.from_user.id})
    user_info.update({'name': update.message.from_user.name})
    user_info.update({'lists': [{'list_name': "List1", 'items': [{'item': "Item1", 'url': 'url1'},
                                                                 {'item': "Item2", 'url': 'url2'}]},
                                {'list_name': "List2", 'items': [{'item': "Item1", 'url': 'url1'},
                                                                 {'item': "Item2", 'url': 'url2'}]}]})
    # setUser('data.json', user_id)
    print(getUser(getJsonData(), user_id))

    if getUser(getJsonData(), user_id) == False:
        setUser('data.json', user_info)
    bot.sendMessage(chat_id=chat_id, text=f"Hello, {user_info.get('name')}!")


def get_url():
    contents = requests.get('https://x-kom.pl')
    url = contents.text
    return url


def conversation_keyboard():
    keyboard = ReplyKeyboardMarkup[['Add new item']]


def start(update, context):
    user_id = update.message.from_user.id
    user_name = update.message.from_user.name

    if dm.check_user_exist(str(user_id)) is False:
        # dm.add_new_user(str(user_id), user_name)
        update.message.reply_text('Welcome to pricewatcher bot.\nThis is a few steps, how to use bot:\n1. Check if store, from where you want to add product is exist in Available shops, if so go to step 3.\n2. If you do not see your shop in list, then you need to add new shop to app by using /new command. Type /help to get info.\n3. Add your product by using /add command, type /help to get info.\n4. If you do not know what to do just type /help.',)
        print(f'New user {user_name} added!')

    keyboard = [[InlineKeyboardButton("My items", callback_data='myitems'),
                InlineKeyboardButton("Available shops", callback_data='sites')],
                [InlineKeyboardButton("How to use bot", callback_data='usage'),
                 InlineKeyboardButton("Help", callback_data='help')],
                ]
    

    reply_markup = InlineKeyboardMarkup(keyboard)

    

    update.message.reply_text('Please choose:', reply_markup=reply_markup)


def button(update, context):
    query = update.callback_query

    help_strings = ['*/start* - show menu',
                    '*/add* name url - to add new item - \n_example:_ /add mybackpack https://somesite.com',
                    '*/items* - to show your items',
                    '*/delete* name - to delete item - \n_example:_ /delete mybackpack',
                    '*/deleteall* - to delete all items',
                    '''*/new* - to add new unknown site - \n_example:_ /new https://somesite.com/ 300
    If shop, from where you want to add product is not in available list(To check list, type /start and choose endeed button), you should add that shop to available list. 
    To do that chose product in online store, find price of this product and type command to chat /new *link to product *price.
    Price must be without money symbol. Price must be exacly the same as in shop page. If adding new shop failed, try to type price without penny part.
    For example:
    /new https://www.x-kom.pl/p/498795-telewizor-44-55-philips-55pus7504.html 2 899,00
    or
    /new https://www.x-kom.pl/p/498795-telewizor-44-55-philips-55pus7504.html 2 899''']
    
    sites = dm.get_sites_list()
    user_id = query.message.chat_id
    if query.data == 'myitems':
        user_items = dm.get_user_items(str(user_id))
        if user_items:
            query.edit_message_text(text=f"*Your items:* \n{chr(10).join(' - '.join(sl) for sl in user_items)}", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview = True)
        else:
            query.edit_message_text(text=f"*You do not have items, feel free to add some.*", parse_mode=ParseMode.MARKDOWN)

    elif query.data == 'sites':
        query.edit_message_text(
            text=f" \n{chr(10).join(sites)}", parse_mode=ParseMode.MARKDOWN)
    elif query.data == 'usage':
        query.message.reply_text('This is a few steps, how to use bot:\n1.Check if store, from where you want to add product is exist in Available shops, if so go to step 3.\n2.If you do not see your shop in list, then you need to add new shop to app by using /new command. Type /help to get info.\n3.Add your product by using /add command, type /help to get info.\n4. If you do not know what to do just type /help.', parse_mode=ParseMode.MARKDOWN)
        # context.bot.sendAnimation(chat_id=user_id, animation=open('Be.gif', 'rb'))

    elif query.data == 'help':
        query.edit_message_text(
            text=f" \n{chr(10).join(help_strings)}", parse_mode=ParseMode.MARKDOWN)


def user_input(update, context):
    chat_id = update.effective_chat.id
    user_exist = dm.check_user_exist(str(chat_id))
    if user_exist is True:
        update.message.reply_text('Please, type correct command. For example: /help.', parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text('You are new here. Type /start command first.', parse_mode=ParseMode.MARKDOWN)



def main():
    updater = Updater(
        token="1059041729:AAF3xsWD5SpK8bevLXz87AedAdiXkzvxdCI", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('items', get_user_items_handler))
    dp.add_handler(CommandHandler('help', help_handler))
    dp.add_handler(CommandHandler('add', add_item_handler, pass_args=True))
    dp.add_handler(CommandHandler('new', add_unknown_site_handler, pass_args=True))
    dp.add_handler(CommandHandler('delete', delete_item_handler, pass_args=True))
    dp.add_handler(CommandHandler('deleteall', delete_all_item_handler))
    dp.add_handler(MessageHandler(Filters.text, user_input))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(ConversationHandler(entry_points=[],
                                    states={},
                                    fallbacks=[])
                                    )

    job = updater.job_queue
    t = 3600
    job_minute = job.run_repeating(check_for_updates, interval=t, first=0)

    updater.start_polling()
    updater.idle()


def getJsonData():
    with open(file_path, 'r') as dt:
        data = json.load(dt)
        return data


def getUser(user_json, user_id):
    try:
        return [obj for obj in user_json if obj['id'] == user_id][0]
    except Exception:
        print("User doesn't exist")
        return False  # user not found


if __name__ == '__main__':
    import logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    file_path = 'data.json'
    print('Start!')
    main()

