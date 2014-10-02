#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json, time, string, tfidf
from geopy.geocoders import GoogleV3
from nameparser import HumanName
import sexmachine.detector as gender
from nltk.corpus import stopwords
from textblob import Word, TextBlob
from bs4 import BeautifulSoup
import xml.etree.ElementTree as etree

class knightEnrich:


	data = None


	def __init__(self):

		

		with open('data.json') as aFile:
			data = aFile.read()

			self.data = json.loads(data)

			print (len(self.data['entries']))


		self.geolocator = GoogleV3()


		#self.enrichLocation()

		#self.enrichNames()

		#self.enrichData()
		
		#self.enrichURL()

		#self.outPutMapFile()

		self.outPutGender()

		self.buildGexf()

		self.writeDataOut()


	def outPutGender(self):

		total = 0
		male = 0
		female = 0
		dontknow = 0

		for entry in self.data['entries']:


			total += 1

			if entry['nameGender'].find('female') > -1:
				female+=1
			elif entry['nameGender'].find('male') > -1:
				male+=1
			else:
				dontknow+=1


		

		print(json.dumps({ "total" : total, "female" : female, "femalePercent" : female/total*100,  "male" : male, "malePercent" : male/total*100, "male" : male, "dontknowPercent" : dontknow/total*100,  "dontknow" : dontknow } , indent=4, separators=(',', ': ')))


	def buildGexf(self):




		header = '<?xml version="1.0" encoding="UTF-8"?>'

		gexf = etree.Element('gexf', xmlns='http://www.gexf.net/1.2draft', version='1.2')

		graph = etree.Element('graph', mode='static', defaultedgetype='undirected')

		nodes = etree.Element('nodes')

		edges = etree.Element('edges')

		addedNodes = {}

		titles = {}

		for entry in self.data['entries']:

			titles[entry['id']] = entry['title']

		edgesCount = 0

		for entry in self.data['entries']:



			if len(entry['similar']) > 0:

				for x in entry['similar']:

					if x[0] not in addedNodes:
						addedNodes[x[0] ] = True
						nodes.append(etree.Element('node', id=str(x[0]), label=titles[x[0]]))
					

				if entry['id'] not in addedNodes:
					addedNodes[entry['id'] ] = True
					nodes.append(etree.Element('node', id=str(entry['id']), label=titles[entry['id']]))
				

				for x in entry['similar']:

					edgesCount+= 1

					edges.append(etree.Element('edge', id=str(edgesCount), weight=str(x[1]), source=str(entry['id']), target=str( x[0] )))


				#if addedNodes[]


				#nodes.append(etree.Element('node', id=str(self.globalSubjects[x]['id']), label=self.globalSubjects[x]['subject'], weight=str(self.globalSubjects[x]['count'])))

				#print ( entry['similar'])


		graph.append(nodes)

		graph.append(edges)


		gexf.append(graph)

		s = etree.tostring(gexf, 'utf-8')
		#s = xml.dom.minidom.parseString(s)
		#s = s.toprettyxml(indent="\t")
		
		gefxFile = open("output.gexf", "w")
		gefxFile.write(header)
		gefxFile.close()


		gefxFile = open("output.gexf", "ab")
		gefxFile.write(s)
		gefxFile.close()



	def outPutMapFile(self):

		output = []

		for entry in self.data['entries']:



			if (entry['latlong'] != None):

				feature = {

					"type": "Feature",
					"properties": {
						"name": entry['title'],
						"show_on_map": True,
						"url" : entry['url'],
						"location" : entry['location'],
					},
					"geometry": {
						"type": "Point",
						"coordinates": [entry['latlong']['long'],entry['latlong']['lat']]
					}

				}

				output.append(feature)

		with open("features.json",'w') as aFile:
			aFile.write(json.dumps(output))		





	def enrichNames(self):

		d = gender.Detector()

		for entry in self.data['entries']:

			entry['name'] = entry['name'].strip().replace("\n","")

			entry['nameGender'] = None



			if (entry['name'] != ""):

				name = HumanName(entry['name'])


				print (name.first, d.get_gender(name.first) )



				entry['nameGender'] = d.get_gender(name.first)



	def enrichURL(self):

		for entry in self.data['entries']:

			print("Doing",entry['id'])


			with open('pages/' + entry['id'] + '.html', encoding='utf-8') as aFile:
				html = aFile.read()

				soup = BeautifulSoup(html)

				meta = soup.find('meta', {'property': 'og:url'})

				print (meta['content'])
				entry['url'] = meta['content']




	def enrichData(self):

		s=set(stopwords.words('english'))

		exclude = set(string.punctuation)

		docs = tfidf.tfidf()

		allDocs = {}

		allNounPhrases = {}
		allNouns = {}
		allVerbs = {}
		for entry in self.data['entries']:

			print("Doing",entry['id'])

			allText = ""

			if entry['description']:
				allText += " " + entry['description']

			if entry['need']:
				allText += " " + entry['need']

			if entry['oneSentence']:
				allText += " " + entry['oneSentence']

			if entry['outcome']:
				allText += " " + entry['outcome']

			if entry['progress']:
				allText += " " +  entry['progress']

			if entry['summary']:
				allText += " " + entry['summary']

			if entry['team']:
				allText += " " + entry['team']

			if entry['title']:
				allText += " " + entry['title']

			allText = allText.replace("\n",' ').replace("\t",' ').replace("\"",'').lower()


			#get the nouns
			
			blob = TextBlob(allText)

			nounPhrases = blob.noun_phrases

			for np in nounPhrases:

				if np in allNounPhrases:
					allNounPhrases[np] += 1
				else:
					allNounPhrases[np] = 1






			allText = ''.join(ch for ch in allText if ch not in exclude)

			words = list(filter(lambda w: not w in s and len(w) > 2,allText.split())) 

			newWords = []

			for z in words:



				w = Word(z)


				newWords.append(str(w.singularize().lemmatize()))


			docs.addDocument(entry['id'],newWords)

			allDocs[entry['id']] = newWords

			sentences = ' '.join(newWords)


			blob = TextBlob(sentences)

			tags = blob.tags

			for t in tags:

				if len(t[0]) > 2:

					if t[1].find('NN') > -1:

						
						if t[0] in allNouns:
							allNouns[t[0] ] += 1
						else:
							allNouns[t[0]] = 1


					if t[1].find('VB') > -1:

						
						if t[0] in allVerbs:
							allVerbs[t[0] ] += 1
						else:
							allVerbs[t[0]] = 1


		count = 0

		freqOutput = { "nounPhrases" : {}, "nouns" : {}, "verbs": {} }

		for w in sorted(allNounPhrases, key=allNounPhrases.get,reverse=True):
			print (w, allNounPhrases[w])
			freqOutput['nounPhrases'][w] = allNounPhrases[w]
			count+=1
			if count>150:
				break
		
		count = 0
		for w in sorted(allNouns, key=allNouns.get,reverse=True):
			print (w, allNouns[w])
			freqOutput['nouns'][w] = allNouns[w]
			count+=1
			if count>150:
				break

		count = 0
		for w in sorted(allVerbs, key=allVerbs.get,reverse=True):
			print (w, allVerbs[w])
			freqOutput['verbs'][w] = allVerbs[w]
			count+=1
			if count>150:
				break



		with open("frequency.json",'w') as aFile:
			aFile.write(json.dumps(freqOutput, indent=4, separators=(',', ': ')))		



		for x in allDocs:

			print (x)

			sim = docs.similarities(allDocs[x])

			sim.sort(key=lambda x: x[1], reverse=True)

			similarIds = []

			if sim[1][1] > 0.009:
				print ("most Similar to", sim[1])
				similarIds.append(sim[1])
			if sim[2][1] > 0.009:
				print ("most Similar to", sim[2])
				similarIds.append(sim[2])
			if sim[3][1] > 0.009:
				print ("most Similar to", sim[3])
				similarIds.append(sim[3])


			for entry in self.data['entries']:

				if (entry['id'] == x):

					entry['similar'] = similarIds



			print("~~~~~~~~~")










	def enrichLocation(self):


		for entry in self.data['entries']:

			
			if entry['location'] != None:

				if entry['location'].strip() != '':

					entry['location'] = entry['location'].replace("\n",' ')

					if 'latlong' in entry:

						if entry['latlong'] == None:

							location = self.geolocator.geocode(entry['location'])
							time.sleep(1)
							if location != None:
								entry['latlong'] = {'lat' : location.latitude, 'long' : location.longitude}
							else:
								entry['latlong'] = None
								print ("Error with this location")
								print (entry['location'])


					else:

						location = self.geolocator.geocode(entry['location'])
						print ("doing ", entry['location'])
						time.sleep(1)
						if location != None:
							entry['latlong'] = {'lat' : location.latitude, 'long' : location.longitude}
							self.writeDataOut()
						else:
							entry['latlong'] = None
							print ("Error with this location")
							print (entry['location'])
			else:

				entry['latlong'] = None



	def writeDataOut(self):

		with open("data.json",'w') as aFile:
			aFile.write(json.dumps(self.data, sort_keys=True, indent=4, separators=(',', ': ')))		



if __name__ == "__main__":

	ke = knightEnrich()
