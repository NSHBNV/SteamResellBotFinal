import steam.webauth as wa
import base64
import hmac
import struct
import time
from hashlib import sha1
import urllib.request
import requests
import json
import re
import telebot

import confirmation
import cfg

def bot_output(bot, infoMessage, tNum, sNum, loop):
	tempStr = 'Total number of Cases: ' + str(tNum) + '\n'
	tempStr += 'Cases sold: ' + str(sNum) + '\n'
	tempStr += 'Cases left: ' + str(tNum - sNum) + '\n'
	tempStr += 'Loop: ' + str(loop) + '\n'
	tempStr += '--------------------------------------------------------------------\n'
	tempStr += '\nIf any errors would occured, they will appear below.'
	bot.edit_message_text(
		text=str(tempStr),
		chat_id=infoMessage.chat.id,
		message_id=infoMessage.message_id,
	)

def go(bot, message):
	if cfg.stop_flag != 1:
		bot.send_message(message.from_user.id, 'Login in accounts...\n------------------------------------')

	tempStr = ''

	f = open('./config/accounts.cfg', 'r', encoding='utf-8')
	passwordsList = f.read()
	f.close()
	passwordsList = str(passwordsList)
	passwordsList = passwordsList.split()

	loginArray = []
	passwordsArray = []
	rsaKeyArray = []
	identityKeyArray = []
	steamID32Array = []
	steamID64Array = []

	i = 0
	while i < len(passwordsList):
		if i % 6 == 0:
			loginArray.append(passwordsList[i])
		elif i % 6 == 1:
			passwordsArray.append(passwordsList[i])
		elif i % 6 == 2:
			rsaKeyArray.append(passwordsList[i])
		elif i % 6 == 3:
			identityKeyArray.append(passwordsList[i])
		elif i % 6 == 4:
			steamID32Array.append(passwordsList[i])
		else:
			steamID64Array.append(passwordsList[i])
		i += 1

	accountArray = []
	i = 0
	while i < len(loginArray):
		accountArray.append(
							Account(
									login=loginArray[i],
									password=passwordsArray[i],
									steamID32=steamID32Array[i],
									steamID64=steamID64Array[i],
									sharedSecret=rsaKeyArray[i],
									identitySecret=identityKeyArray[i],
									botPtr=bot,
									messagePtr=message,
									)
							)
		i += 1

	i = 0
	print('list of passwords:')
	while i < len(passwordsArray):
		print(accountArray[i].login + ' ' + accountArray[i].password + ' ' + accountArray[i].sharedSecret + ' ' +
			  accountArray[i].steamID32 + ' ' + accountArray[i].steamID64)
		i += 1

	for j in range(len(accountArray)):
		accountArray[j].get_SessionID()

	priceArray = getFileInfo('./config/pricelist.cfg')
	caseNameArray = getFileInfo('./config/caselist.cfg')

	tempStr = 'Your case price list:\n\n'
	if cfg.stop_flag != 1:
		for i in range(len(caseNameArray)):
			tempStr += caseNameArray[i] + ' - '
			tempStr += priceArray[i] + '\n'

		bot.send_message(message.from_user.id, tempStr)

	counter = 1
	temp = 0
	total_num = 0
	infoMessage = bot.send_message(message.from_user.id, '...')

	while True:
			CasesObjArr = []
			print('loop: ' + str(counter))
			for j in range(len(accountArray)):
				while True:
					accountArray[j].get_InvData()
					if accountArray[j].invData != '{"error": "EYldRefreshAppIfNecessary failed with EResult 55"}':
						break
				for i in range(len(accountArray[j].invData['assets'])):
					CasesObjArr.append(accountArray[j].get_CaseData(i))

			for i in range(len(accountArray)):
				for j in accountArray[i].invData['descriptions']:
					for b in range(len(CasesObjArr)):
						if CasesObjArr[b].classID == j['classid']:
							CasesObjArr[b].name = j['name']

			total_num += len(CasesObjArr)
			total_num -= len(accountArray)

			bot_output(bot, infoMessage, total_num, temp, counter)
			print(len(CasesObjArr))

			for i in range(len(CasesObjArr)):
				for j in range(len(caseNameArray)):
					if CasesObjArr[i].name == caseNameArray[j]:
						if cfg.stop_flag == 1:
							break
						try:
							CasesObjArr[i].price = priceArray[j]
							CasesObjArr[i].sell()

							temp += 1
							bot_output(bot, infoMessage, total_num, temp, counter)
							break
						except Exception as e:
							total_num -= 1
							temp -= 1
							bot.send_message(message.from_user.id, 'An error occured.\n\n' + str(e))
							continue
				if cfg.stop_flag == 1:
					break

			if cfg.stop_flag == 1:
				print('Terminated.')
				cfg.stop_flag = 0
				break

			counter += 1
			time.sleep(60)



	cfg.stop_permission_flag = 1

def getFileInfo(filepath):
	f = open(filepath, 'r', encoding='utf-8')
	temp = f.read()
	f.close()
	temp = temp.split('\n')
	return temp

class Case:
	def __init__(self, assetID, session, sessionID, classID, steamID, sessionCookies, confirmation):
		self.name = ''
		self.assetID = assetID
		self.session = session
		self.sessionID = sessionID
		self.classID = classID
		self.steamID = steamID
		self.sessionCookies = sessionCookies
		self.confirmation = confirmation
		self.price = -1
		self.URL_INVENTORY_PAGE = 'https://steamcommunity.com/profiles/%s/inventory/' % self.steamID


	def sell(self):
		self.data = dict(
			sessionid=str(self.sessionID),
			appid=730,
			contextid=2,
			assetid=int(self.assetID),  # Номер уникальной копии
			amount=1,
			price=int(self.price)
		)

		self.headers = {
			'Referer': self.URL_INVENTORY_PAGE,
			'DNT': '1'
		}

		try:
			res = requests.post(
								"https://steamcommunity.com/market/sellitem/",
								self.data,
								cookies=self.sessionCookies,
								headers=self.headers
								).json()
			print('\n'+str(res)+'\n')
			if res['requires_confirmation'] == 1:
				self.confirmation.confirm_sell_listing(self.assetID)
		except Exception as e:
			if e == '\'requires_confirmation\'':
				self.confirmation.confirm_sell_listing(self.assetID)

		print(self.data)
		print(self.headers)
		print(self.assetID)
		print(self.classID)
		print(self.sessionID)
		print(self.steamID)
		print(self.URL_INVENTORY_PAGE)
		print(self.price)


class Account:
	def __init__(self, login, password, steamID32, steamID64, sharedSecret, identitySecret, botPtr, messagePtr):
		self.login = login
		self.password = password
		self.steamID32 = steamID32
		self.steamID64 = steamID64
		self.sharedSecret = sharedSecret
		self.identitySecret = identitySecret
		self.botPtr = botPtr
		self.messagePtr = messagePtr
		self.user = wa.WebAuth(self.login, self.password)
		self.session = requests.session()
		self.sessionID = ''
		self.invDataArr = []
		self.invData = ''

		self.tempStr = ''


	def get_TwoFACode(self):
		timestamp = int(time.time())
		time_buffer = struct.pack('>Q', timestamp // 30)  # pack as Big endian, uint64
		time_hmac = hmac.new(base64.b64decode(self.sharedSecret), time_buffer, digestmod=sha1).digest()
		begin = ord(time_hmac[19:20]) & 0xf
		full_code = struct.unpack('>I', time_hmac[begin:begin + 4])[0] & 0x7fffffff  # unpack as Big endian uint32
		chars = '23456789BCDFGHJKMNPQRTVWXY'
		code = ''
		for _ in range(5):
			full_code, i = divmod(full_code, len(chars))
			code += chars[i]
		return code

	def get_InvData(self):
		url = 'https://steamcommunity.com/inventory/%s/730/2?l=english&count=5000' % self.steamID64
		print(url)
		self.invData = requests.get(url)

		f = open('.\\config\\inventories\\' + self.login + '.txt', 'w')
		self.invData = json.loads(self.invData.text)

		f.write(str(json.dumps(self.invData, sort_keys=True, indent=4)))
		f.close()


	def get_CaseData(self, i):
		return Case(
					assetID=self.invData['assets'][i]['assetid'],
					session=self.session,
					sessionID=self.sessionID,
					classID=self.invData['assets'][i]['classid'],
					steamID=self.steamID64,
					sessionCookies=self.sessionCookies,
					confirmation=self.confirmation,
					)

	def get_SessionID(self):
		try:
			self.user.login(twofactor_code=self.get_TwoFACode(), language='russian')
		except wa.CaptchaRequired:
			print(self.user.captcha_url)
			self.botPtr.send_message(self.messagePtr.from_user.id, 'Error: Captcha required\n--------------------------')
		except wa.EmailCodeRequired:
			print('Error: Email Code Required\n--------------------------')
		except wa.TwoFactorCodeRequired:
			self.botPtr.send_message(self.messagePtr.from_user.id, 'Error: Wrong 2FA\n--------------------------')
		except wa.LoginIncorrect:
			print('Error: Login incorrect\n--------------------------')
		except wa.HTTPError as err:
			self.botPtr.send_message(self.messagePtr.from_user.id, 'Error: HTTPError\n--------------------------')
			print(err)
		except Exception as e:
			print(e + '\n--------------------------')
		else:
			if cfg.stop_flag != 1:
				self.tempStr = '------------------------------------\n'
				self.tempStr += 'Login successful\n' + self.login
				self.tempStr += '\n2FA Code = ' + str(self.get_TwoFACode())
				self.tempStr += '\n------------------------------------'

				self.botPtr.send_message(self.messagePtr.from_user.id, self.tempStr)
		self.session = self.user.login()
		self.sessionID = str(self.session.cookies)
		self.sessionCookies = self.session.cookies
		print(self.sessionID)
		print(self.identitySecret)
		print(self.steamID32)
		print(self.session)
		self.confirmation = confirmation.ConfirmationExecutor(
															identity_secret=self.identitySecret,
		                                                      my_steam_id=self.steamID64,
		                                                      session=self.session,
		                                                      )


		count = 0
		startPos = 0
		endPos = 0

		for s in re.finditer(' for steamcommunity.com/', self.sessionID):
			count += 1
			# print(' for steamcommunity.com/', s.start(), s.end())
			if count == 3:
				endPos = s.start()
				break

		count = 0

		for s in re.finditer('Cookie sessionid=', self.sessionID):
			count += 1
			# print('Cookie sessionid=', s.start(), s.end())
			if count == 2:
				startPos = s.end()
				break

		print("SessionID = " + self.sessionID[startPos:endPos])
		self.sessionID = self.sessionID[startPos:endPos]