#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from os import listdir
from os.path import isfile, join
import requests,sys, string, json, time


class knightScrape:


	firstPage = "https://newschallenge.org/challenge/libraries/submissions/centralize-government-customer-service"
	baseUrl = "https://newschallenge.org"
	dataDir = "pages/"
	activeUrl = ""
	activeSoup = None

	def __init__(self):

		pass


	def storePages(self):

		print ("Starting...")
		print (self.firstPage)

		html = self.downloadPage(self.firstPage)

		if (html!=False):


			id = self.extractID()

			nextLink = self.extractNextLink()


			if id and nextLink:

				#save the first one
				self.savePage(id+'.html',html)

				#loop through the rest
				while nextLink != False:

					html = self.downloadPage(self.baseUrl + nextLink)

					if (html!=False):

						id = self.extractID()

						nextLink = self.extractNextLink()


						if id and nextLink:

							self.savePage(id+'.html',html)
					else:

						print("Error, HTML == false")
						break






	def processPages(self):

		files = [ f for f in listdir(self.dataDir) if isfile(join(self.dataDir,f)) and str(f).find('.html') > -1 ]

		datas = []

		for file in files:


			dataDict = {}

			

			with open(self.dataDir + file, encoding='utf-8') as aFile:
				html = aFile.read()

			self.activeSoup = BeautifulSoup(html)	

			id = self.extractID()
			print (id)


			nextLink = self.extractNextLink()

			title = self.extractTitle()
			summary = self.extractSummary()


			answers = self.extractAnswers()

			description = self.extractDescription()

			name = self.extractName()

						

			# print (id)
			# print (nextLink)
			# print (title)
			# print (summary)
			# print (answers)
			# print (description)
			# print (name)

			dataDict['id'] = id
			dataDict['title'] = title
			dataDict['summary'] = summary
			dataDict['description'] = description
			dataDict['name'] = name
			dataDict['oneSentence'] = answers['oneSentence']
			dataDict['need'] = answers['need']
			dataDict['progress'] = answers['progress']
			dataDict['outcome'] = answers['outcome']
			dataDict['team'] = answers['team']
			dataDict['location'] = answers['location']

			datas.append(dataDict)


		with open("data.json",'w') as aFile:
			aFile.write(json.dumps({"entries" : datas, "dateGenerated" : time.strftime("%c")}, sort_keys=True, indent=4, separators=(',', ': ')))		





	def downloadPage(self,url):

		print("Downloading",url)

		time.sleep(5)

		r = requests.get(url)

		self.activeUrl = url


		if r.status_code == 200:	
			self.activeSoup = BeautifulSoup(r.text)		
			return r.text
		else:
			print ("There was an error with", url)
			self.activeSoup = BeautifulSoup("")	

			return False

	def savePage(self,file,html):

		with open(self.dataDir + file, 'w') as newfile:
			 newfile.write(html)




	def extractID(self):


		soup = self.activeSoup

		voteSpan = soup.find_all('span', {'class': 'votes'})

		if len(voteSpan) > 0:

			#first one, doesn't matter
			voteSpan = voteSpan[0]

			id = str(voteSpan).split('contribution_')
			id = id[1].split('">')[0]

			if (id.isdigit()):
				return id
			else:
				print ("could not extract the ID from",self.activeUrl)
				return False


	def extractNextLink(self):

		soup = self.activeSoup
		nextLink = soup.find("a", {"id": "next-concept-inspiration"})

		if len(nextLink) > 0:
			return nextLink['href']
		else:
			return False


	def extractTitle(self):
		soup = self.activeSoup		
		title = soup.find("h2", {"class": "item-title"})

		if len(title) > 0:
			return title.text.strip()
		else:
			return False

	def extractSummary(self):
		soup = self.activeSoup		
		summary = soup.find("div", {"class": "summary"})

		if len(summary) > 0:
			return summary.text.strip()
		else:
			return False

	def extractDescription(self):
		soup = self.activeSoup		
		description = soup.find("div", {"class": "description"})

		if len(description) > 0:
			return description.text.strip()
		else:
			return False

	def extractName(self):


		soup = self.activeSoup		
		#texts = soup.find_all("div", {"class": "text"})
		texts =soup.select('.text a')

		for link in texts:

			if str(link).find('s profile') > -1:

				return link.text.strip()



	def extractAnswers(self):

		soup = self.activeSoup		
		answers = soup.find_all("div", {"class": "contribution-answer"})

		question = soup.find_all("div", {"class": "question"})

		result = {"oneSentence" : None, "need" : None, "progress" : None, "outcome" : None, "team" : None, "location" : None }

		for x in range(len(question)):


			thisQuestion = question[x].text.strip()

			if (thisQuestion == 'In one sentence, describe your idea as simply as possible.'):
				result['oneSentence'] = answers[x].text.strip()

			if (thisQuestion == 'Briefly describe the need that you’re trying to address.'):
				result['need'] = answers[x].text.strip()

			if (thisQuestion == 'What progress have you made so far?'):
				result['progress'] = answers[x].text.strip()

			if (thisQuestion == 'What would be a successful outcome for your project?'):
				result['outcome'] = answers[x].text.strip()

			if (thisQuestion == 'Please list your team members and their relevant experiences/skills.'):
				result['team'] = answers[x].text.strip()

			if (thisQuestion == 'Location'):
				result['location'] = answers[x].text.strip()


		return result




if __name__ == "__main__":

	ks = knightScrape()

	#ks.storePages()
	ks.processPages()