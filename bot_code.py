from typing import Final
import pytz
import datetime
import json

from telegram import (
    KeyboardButton,
    KeyboardButtonPollType,
    Poll,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update
)

from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PollAnswerHandler,
    PollHandler,
    filters,
    JobQueue
)



TOKEN: Final = '6863555451:AAExfjyZe7rLbPaWF2KYonH8O6HUs0yERDs' 
BOT_USERNAME: Final = '@worforgood_meet_manager_bot'

indexTimeMapper = {
    0 : 7,
    1 : 8,
    2 : 9,
    3 : 10,
    4 : 11,
    5 : 12,
    6 : 20,
    7 : 21,
    8 : 22,
    9 : 23
}
weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
poll_options = ["7-8","8-9","9-10","10-11","11-12","12-13","20-21","21-22","22-23","23-24"]
phasedays = ["Sunday", "Monday", 'Tuesday', 'Wednesday']

utc_now = datetime.datetime.utcnow()
india_timezone = pytz.timezone('Asia/Kolkata')
india_now = utc_now.astimezone(india_timezone)
weekday = weekdays[india_now.weekday()]

if weekday in phasedays:
    weekday = "Wednesday"
else:
    weekday = "Saturday"

polls = {}
poll_question = (
    f"What times are you available for the {weekday} meeting?\n"
    "Please select all that apply.\n"
    "***You can change your selections at any time (T&C apply).***\n"
    "***Please do not change your selections within 30 minutes of the scheduled time.***"
)

def get_data(key):
    filename = 'bot_memo.json'
    with open(filename, 'r') as file:
        data = json.load(file)
    return data[key]

def update_data(key, value):
    filename = 'bot_memo.json'
    with open(filename, 'r') as file:
        data = json.load(file)
        data[key] = value

    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

# Commands
############
# bot info (/help /start)
##########################################################################################################
async def start_command(update: Update, context: ContextTypes):
    await update.message.reply_text('Hello! I am the Meet Manager Bot. Created by workforgood Members.  I can help you manage your meetings. Type /help to see the list of commands.')    
async def help_command(update: Update, context: ContextTypes):
    await update.message.reply_text('The following commands are available:\n\n'
                                    '/start - Get bot information\n'
                                    '/help  - Show the list of commands\n'
                                    '/snml  - Set New Meet Link\n'
                                    '/dml   - Display Meet Link\n'
                                    '/fmts  - fetch meet time slot\n')       

#poll manager (/ffts)
##########################################################################################################
async def fetch_meet_time_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(reply_to_message_id=get_data("message_id"),chat_id=update.effective_chat.id, text="Here is Poll ↑↑↑")
   
async def calc_poll_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    user_data = get_data("user_data")
    current_voted_data = get_data("voting_data")
    selected_options = answer.option_ids
    user_id = answer.user.id
    print(user_id)
    print(user_data)
    print(200)
    if user_data.get(str(user_id)) == None:
        print(1001)
        for i in selected_options:
            current_voted_data[str(i)] = current_voted_data.get(str(i), 0) + 1
        user_data[user_id] = selected_options
        update_data("user_data", user_data)
        update_data("voting_data", current_voted_data)
    else : 
        print(100)
        for i in user_data[str(user_id)]:
            current_voted_data[str(i)] = current_voted_data.get(str(i), 0) - 1
        for i in selected_options:
            current_voted_data[str(i)] = current_voted_data.get(str(i), 0) + 1
        user_data[user_id] = selected_options
        update_data("voting_data", current_voted_data)
        update_data("user_data", user_data)
    
    
  
    
async def send_poll(context: ContextTypes.DEFAULT_TYPE,update : None):
    hour = datetime.datetime.now().hour
    message_id = get_data("message_id")
    if(((weekday == "Wednesday" or weekday == "Saturday") and hour >= 23) or message_id == -1):
        chat_id = get_data("chat_id")
        new_poll = await context.bot.send_poll(
            chat_id = chat_id,
            question=poll_question,
            options=poll_options,
            is_anonymous=False,
            allows_multiple_answers=True,
            disable_notification=True
        )
        update_data("is_meeting_done", False)
        update_data("user_data", {})
        update_data("voting_data", {"0":0,"1":0,"2":0,"3":0,"4":0,"5":0,"6":0,"7":0,"8":0,"9":0})
        update_data("message_id", new_poll['message_id'])
        
#Data Saver (/snml) 
############################################################################################################
async def display_meet_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    meet_link = get_data("current_meet_link")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=meet_link)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text
    if 'meet:' in text:
        update_data("current_meet_link", text)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Meet Link Successfully Update\n new Meet Up link\n" +  f"{text}")

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} cause erorr {context.error}')


#Cron Jobs
############################################################################################################
async def every_day_caller(context: ContextTypes.DEFAULT_TYPE):
    chat_id = get_data("chat_id")
    user_data = get_data("user_data")
    if len(user_data) < 4:
       await context.bot.send_message(chat_id=chat_id, text="Please vote for the poll!\n you can fetch the poll by command 'fmts' \n some of the member are not voted \n if voted please ignore")
    await send_poll(context)
    
async def every_hour_caller(context: ContextTypes.DEFAULT_TYPE):
    user_data = get_data("user_data")
    chat_id = get_data("chat_id")
    is_meeting_done = get_data("is_meeting_done")
    if user_data.length == 4 and (weekday == 'Saturday' or weekday == 'Wednesday') and is_meeting_done == False :
        voting_data = get_data("voting_data")
        for i in range(0, 10):
            z = voting_data.get(str(i))
            if z == 4:
                meet_link = get_data("current_meet_link")
                await context.bot.send_message(chat_id=chat_id, text=meet_link + f"\n please join at {indexTimeMapper[i]}:00")
                update_data("is_meeting_done", True)
                return
            else : 
                print(z)

async def my_filter():
    return 

#Main
############################################################################################################
def main() -> None:
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('fmts', fetch_meet_time_slot))
    app.add_handler(CommandHandler('dml', display_meet_link))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_error_handler(error)
    app.add_handler(PollHandler(send_poll))
    app.add_handler(PollAnswerHandler(calc_poll_result))
    print('Polling...')
    
    #every one hour caller
    ################################################################################
    currentTime = datetime.datetime.now()
    minutes = currentTime.minute    
    if minutes > 0 and minutes < 30:
        minutes = 30 - minutes
    else:
        minutes = 90 - minutes 
    app.job_queue.run_repeating(every_hour_caller, interval=30, first=5)  
    
    #every day caller
    ###############################################################################
    currentTime = datetime.datetime.now()
    hour = currentTime.hour
    if(hour < 23):
        hour = 23 - hour
    else:
        hour = 24 - hour + 23
      
    app.job_queue.run_repeating(every_day_caller, interval=86400, first=hour*3600)
    ###############################################################################
    app.run_polling(allowed_updates=Update.ALL_TYPES)
    

if __name__ == '__main__':
    main()
