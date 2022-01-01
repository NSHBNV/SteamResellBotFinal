import telebot
import os
import shutil
import threading
import datetime
import mysql.connector

import go
import cfg

#изменить в get inv data urlopen на что-то из requests ✔
#Проблема не в этом, теперь выскакивает keyerror, разобраться с ключами✔
#Стим ебёт мозги, в ответ на запрос приходит такая хуйня {"error": "EYldRefreshAppIfNecessary failed with EResult 55"}✔

#Сделать автоматическое подтверждение офферов продаж ✔
#https://github.com/bukson/steampy/blob/master/steampy/confirmation.py✔

#Сделать отображение баланса в account actions

#Сделать нормальное игнорирование ошибок(особенно HTTP)

#Оптимизировать код и устранить утечки памяти

#Сделать автоматическую отмену всех sell offers
#Здесь методы парсящие
#https://github.com/bukson/steampy/blob/master/steampy/utils.p y
#Здесь метод cancel_sell_order
#https://github.com/bukson/steampy/blob/master/steampy/market.py

#Сделать покупку кейсов непосредственно в боте
#кнопка пересчитать продажу

bot = telebot.TeleBot('826815843:AAFEmdmwzLZoUG1yqid7cDT3ZcXjD_qv8nk')
global noneKeyboard
noneKeyboard = telebot.types.ReplyKeyboardRemove()
global user

mydb = mysql.connector.connect(
	host='localhost',
	user='root',
	passwd='root123',
	database='tgsteamdb'
)

global cursor
cursor = mydb.cursor()


@bot.message_handler(commands=['start'])
def start_message(message):
	keyboard = telebot.types.ReplyKeyboardMarkup(True)
	keyboard.row('Actions on Cases', 'Account actions').add('GO/STOP')
	tempStr = '--------------------------------------------------------------------'
	tempStr += '\nMAIN MENU.\n\nWelcome!\nPls, use the keyboard below.\n'
	tempStr += '--------------------------------------------------------------------'
	send = bot.send_message(message.from_user.id, tempStr, reply_markup=keyboard)

	user = message

	bot.register_next_step_handler(send, second)


def second(message):
	keyboard = telebot.types.ReplyKeyboardMarkup(True)
	if message.text == 'Actions on Cases':
		keyboard.row('<-Discard', '<-Save').add('Cancel case(s) sell orders')
		keyboard.add('Add Case')
		tempStr = '----------------------------------------'
		tempStr += '\nCASES ACTIONS MENU.\n\nCases list:\n'
		tempStr += '----------------------------------------'
		bot.send_message(message.from_user.id, tempStr, reply_markup=keyboard)

		inlineKB = telebot.types.InlineKeyboardMarkup()
		btn1 = telebot.types.InlineKeyboardButton(text='Change price', callback_data='Change price')
		btn2 = telebot.types.InlineKeyboardButton(text='Rename', callback_data='Rename')
		btn3 = telebot.types.InlineKeyboardButton(text='Remove', callback_data='RemoveCase')

		inlineKB.row(btn1, btn2, btn3)

		sql = 'SELECT * FROM pricelist'
		cursor.execute(sql)
		counter = 0

		while True:
			counter+=1

			res = cursor.fetchone()
			if res == None:
				break
			temp = res[0] + ' - ' + res[1]
			bot.send_message(message.from_user.id, text=str(str(counter) + '. ' + temp), reply_markup=inlineKB)

		tempStr = '-----------------------------------------------------------------------'
		tempStr += '\nIf you want add a new case use \'Add Case\' button below.\n\n'
		tempStr += 'If you need to change price or rename case send value in the chat and press button that you need:\n'
		tempStr += '-----------------------------------------------------------------------'
		bot.send_message(message.from_user.id, text=tempStr)

		f = open('./config/temp/buffer.cfg', 'w', encoding='utf-8')
		f.write('Empty')
		f.close()
		send = bot.send_message(message.chat.id, 'Current Buffer: Empty')

		bot.register_next_step_handler(send, third)

	elif message.text == 'Account actions':
		keyboard.row('<-Discard', 'Save<-').add('Add Account', 'Cancel all orders on Account(s)')
		tempStr = '--------------------------------------------------------------------'
		tempStr += '\nACCOUNT ACTIONS MENU.\n\nAccounts List:\n'
		tempStr += '--------------------------------------------------------------------'
		bot.send_message(message.from_user.id, tempStr, reply_markup=keyboard)

		accountArray = getFileInfo('./config/temp/accountsTemp.cfg')

		for i in range(len(accountArray)):
			accountArray[i] = accountArray[i].split(' ')
			tempStr = str(i+1) + '. ' + accountArray[i][0]
			tempStr += '\n     - pwd: ' + accountArray[i][1] + '\n'
			tempStr += '\n     - rsa: \n       ' + accountArray[i][2]
			tempStr += '\n     - idkey: \n       ' + accountArray[i][3] + '\n'
			tempStr += '\n     - ID32: ' + accountArray[i][4]
			tempStr += '\n     - ID64: ' + accountArray[i][5]

			inventory_URL = 'https://steamcommunity.com/profiles/%s/inventory/' % accountArray[i][5]

			inlineKB = telebot.types.InlineKeyboardMarkup()
			btn1 = telebot.types.InlineKeyboardButton(text='Inventory', url=inventory_URL)
			btn2 = telebot.types.InlineKeyboardButton(text='Remove', callback_data='RemoveAcc')
			inlineKB.row(btn1, btn2)


			send = bot.send_message(message.from_user.id, tempStr, reply_markup=inlineKB)

		bot.register_next_step_handler(send, third)

	elif message.text == 'GO/STOP':
		keyboard = telebot.types.ReplyKeyboardMarkup(True)
		keyboard.add('GO/STOP')
		send = bot.send_message(message.from_user.id,
		                        'Started.\nIf u want terminate program, use GO/STOP button again',
		                        reply_markup=keyboard)

		t = threading.Thread(target=go.go, args=(bot, message))
		t.start()
		bot.register_next_step_handler(send, waiting)
	else:
		bot.send_message(message.from_user.id, 'Pls, use the keyboard below.')
		start_message(message)

def waiting(message):
	if message.text == 'GO/STOP':
		send = bot.send_message(message.from_user.id, 'Terminated. Pls, wait a bit...', reply_markup=noneKeyboard)

		cfg.stop_flag = 1
		while cfg.stop_permission_flag != 1:
			pass

		cfg.stop_permission_flag = 0
		start_message(message)
	else:
		send = bot.send_message(message.from_user.id, 'Program is working.\nPress \'GO/STOP\' button again.')
		bot.register_next_step_handler(send, waiting)

def third(message):
	if message.text == 'Add Case':
		send = bot.send_message(message.from_user.id, 'Input name and price of Case with ONE whitespace.', reply_markup=noneKeyboard)
		bot.register_next_step_handler(send, addCase)
	elif message.text == 'Cancel case(s) sell orders':
		pass
	elif message.text == 'Add Account':
		tempStr = '--------------------------------------------------------------------'
		tempStr += '\nFormalize info about account in this way and send it in the chat:\n'
		tempStr += '\nLogin'
		tempStr += '\nPassword'
		tempStr += '\nRSA key'
		tempStr += '\nIdentity key'
		tempStr += '\nSteamID32'
		tempStr += '\nSteamID64\n'
		tempStr += '\nUseful links:\n'
		tempStr += '<a href="https://steamid.xyz/">Steam ID Finder</a> \n'
		tempStr += '--------------------------------------------------------------------'
		send = bot.send_message(message.from_user.id, tempStr, parse_mode='HTML', disable_web_page_preview=True, reply_markup=noneKeyboard)
		bot.register_next_step_handler(send, addAccount)

	elif message.text == 'Cancel all orders on Account(s)':
		keyboard = telebot.types.ReplyKeyboardMarkup()
		send = bot.send_message(message.from_user.id, 'This button don`t work now :)', reply_markup=keyboard)

	getBuffer(message)

def addCase(message):
	caseName = '\n'
	temp = message.text.split(' ')
	for i in range(len(temp)-1):
		caseName += temp[i]
		if i != len(temp) - 2:
			caseName += ' '

	casePrice = '\n'
	casePrice += temp[len(temp)-1]

	f1 = open('./config/temp/pricelistTemp.cfg', 'a', encoding='utf-8')
	f1.write(casePrice)
	f1.close()

	f2 = open('./config/temp/caselistTemp.cfg', 'a', encoding='utf-8')
	f2.write(caseName)
	f2.close()

	message.text = 'Actions on Cases'
	second(message)

def addAccount(message):
		acc = '\n'
		temp = message.text.split('\n')
			if len(temp) != 6:
				bot.send_message(message.from_user.id, 'An error in input occured, pls, try again.')
			message.text = 'Add Account'
			third(message)
		else:
			for i in range(len(temp)):
				acc += temp[i]
				if i != len(temp) - 1:
					acc += ' '


			f = open('./config/temp/accountsTemp.cfg', 'a', encoding='utf-8')
			f.write(acc)
			f.close()

			message.text = 'Account actions'
			second(message)

@bot.message_handler(content_types=['text'])
def text_message(message):
	if message.text == 'GO/STOP':
		pass
	getBuffer(message)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
	f = open('./config/temp/buffer.cfg', 'r', encoding='utf-8')
	txt = f.read()
	f.close()

	if txt == 'Empty' and call.data != 'RemoveCase' and call.data != 'RemoveAcc':
		bot.send_message(call.message.chat.id, 'Empty Buffer. Type value in a message.')
	else:
		if call.message:
			priceArray = getFileInfo('./config/temp/pricelistTemp.cfg')
			caseNameArray = getFileInfo('./config/temp/caselistTemp.cfg')


			num = int(call.message.text[:call.message.text.find('.')])
			tStr = ''

			inlineKB = telebot.types.InlineKeyboardMarkup()
			btn1 = telebot.types.InlineKeyboardButton(text='Change price', callback_data='Change price')
			btn2 = telebot.types.InlineKeyboardButton(text='Rename', callback_data='Rename')
			btn3 = telebot.types.InlineKeyboardButton(text='Remove', callback_data='RemoveCase')

			inlineKB.row(btn1, btn2, btn3)
			if call.data == 'Change price':
				bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
										text=str(str(num) + '. ' + caseNameArray[num - 1] + ' - ' + txt),
										parse_mode='Markdown', reply_markup=inlineKB)
				priceArray[num-1] = txt

				f1 = open('./config/temp/pricelistTemp.cfg', 'w', encoding='utf-8')
				for i in range(len(priceArray)):
					tStr += priceArray[i]
					if i != len(priceArray) - 1:
						tStr+='\n'
				f1.write(tStr)
				f1.close()

			elif call.data == 'Rename':
				bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
										text=str(str(num) + '. ' + txt + ' - ' + priceArray[num - 1]),
										parse_mode='Markdown', reply_markup=inlineKB)
				caseNameArray[num-1] = txt

				f2 = open('./config/temp/caselistTemp.cfg', 'w', encoding='utf-8')
				for i in range(len(caseNameArray)):
					tStr += caseNameArray[i]
					if i != len(caseNameArray) - 1:
						tStr+='\n'
				f2.write(tStr)
				f2.close()

			elif call.data == 'RemoveCase':
				bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
										text=str(str(num) + '. ' + 'REMOVED'),
										parse_mode='Markdown', reply_markup=inlineKB)
				#Ошибка если удалить все элементы массива
				priceArray.pop(num-1)
				caseNameArray.pop(num-1)

				f1 = open('./config/temp/pricelistTemp.cfg', 'w', encoding='utf-8')
				for i in range(len(priceArray)):
					tStr += priceArray[i]
					if i != len(priceArray) - 1:
						tStr+='\n'
				f1.write(tStr)
				f1.close()

				tStr = ''

				f2 = open('./config/temp/caselistTemp.cfg', 'w', encoding='utf-8')
				for i in range(len(caseNameArray)):
					tStr += caseNameArray[i]
					if i != len(caseNameArray) - 1:
						tStr+='\n'
				f2.write(tStr)
				f2.close()

			elif call.data == 'RemoveAcc':
				bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
										text=str(str(num) + '. ' + 'REMOVED'),
										parse_mode='Markdown')

				accountArray = getFileInfo('./config/temp/accountsTemp.cfg')
				# Ошибка если удалить все элементы массива
				accountArray.pop(num-1)

				f = open('./config/temp/accountsTemp.cfg', 'w', encoding='utf-8')

				tStr = ''

				for i in range(len(accountArray)):
					tStr += accountArray[i]
					if i != len(accountArray) - 1:
						tStr+='\n'
				f.write(tStr)
				f.close()


def getFileInfo(filepath):
	f = open(filepath, 'r', encoding='utf-8')
	temp = f.read()
	f.close()
	temp = temp.split('\n')
	return temp


def getBuffer(message):
	if message.text == '<-Discard':
		bot.send_message(message.from_user.id, text='Exited with no changes.')
		start_message(message)
	elif message.text == '<-Save':
		bot.send_message(message.from_user.id, text='Saved.')
		shutil.copyfile('.\\config\\temp\\caselistTemp.cfg', '.\\config\\caselist.cfg')
		shutil.copyfile('.\\config\\temp\\pricelistTemp.cfg', '.\\config\\pricelist.cfg')
		start_message(message)
	elif message.text == 'Save<-':
		bot.send_message(message.from_user.id, text='Saved.')
		shutil.copyfile('.\\config\\temp\\accountsTemp.cfg', '.\\config\\accounts.cfg')
		start_message(message)
	elif message.text == 'Add Case':
		pass
	elif message.text == 'Add Account':
		pass
	elif message.text == 'Cancel all orders on Account(s)':
		pass
	elif message.text == 'GO/STOP':
		pass
	else:
		f = open('./config/temp/buffer.cfg', 'w', encoding='utf-8')
		f.write(message.text)
		f.close()
		bot.send_message(message.chat.id, 'Current Buffer: ' + message.text)

#while True:
try:
	bot.polling(none_stop=True, interval=1)

except Exception as e:
	print(e)
	date = datetime.datetime.now()
	path = './debug/%d-%d-%d %dd%dm' % (date.hour,
	                    date.minute,
	                    date.second,
	                    date.day,
	                    date.month)
	os.mkdir(path)
	f = open('%s/errorLogs.txt' % path, 'w', encoding='utf-8')
	f.write(str(e))
	f.close()

	shutil.copytree('.\\config', path + '/config')

	#bot.send_message(user.from_user.id, 'An error occured.\n\n' + str(e) + '\n\nBack to the main menu...')


