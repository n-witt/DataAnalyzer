'''
Created on 17.07.2014

@author: user
'''
from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError 
from os import listdir
from os.path import isfile, join
import requests
from pdf2txt import pdf_to_txt
import re
from fuzzywuzzy import process
import bisect

def main():
   mypath = u'../../samples'
   min_tokens = 2
   onlypdfFiles = [ f for f in listdir(mypath) if isfile(join(mypath,f)) ]
   for f in onlypdfFiles:
      print "currently in progress: " + f
      try:
         pdfFile = PdfFileReader(open(mypath + '/' + f, "rb"))
         metainfo = pdfFile.getDocumentInfo()
         #in case there are autor and title information in the metadata
         if metainfo.author != None or metainfo.title != None:
            res = searchDataprovider("search", "title", metainfo.title)
            printEconbizOutput(res)
         #when there is no metadata available
         else:
            hits = []
            s = pdf_to_txt(mypath + '/' + f, 0, 0)
            paragraphs = re.split(' *\n+ *', s)
            paragraphs = removeShortTerms(paragraphs, 5)
            end = min(5, len(paragraphs))
            for a in range(0, end):
               #search only if there are more than min_tokens words
               if len(paragraphs[a].split()) > min_tokens:
                  res = searchDataprovider("search", "title", paragraphs[a])
                  hit = selectBestMatch(paragraphs, res['hits']['hits'], 50)
                  if hit != None:
                     bisect.insort_left(hits, hit)
            if len(hits) > 0:
               bestHit = hits[-1]
               print "quality: " + str(bestHit[0])
               #printEconbizOutput([bestHit[-1]])
            else:
               print "no hit"
            print "\n"
      except (AttributeError, TypeError, PdfReadError, IOError, AssertionError) as e:
         continue
   print("done.")

def removeShortTerms(l, length=5): 
   l = uniqify(l)
   removeCandidates = []
   for s in l:
      if len(s) < length:
         removeCandidates.append(s)
   for s in removeCandidates:
      l.remove(s)
   return l

def uniqify(seq): 
   seen = {}
   result = []
   for item in seq:
      if item in seen: continue
      seen[item] = 1
      result.append(item)
   return result
   
def selectBestMatch(tokens, hits, qualityThreshold=50, creatorWeight=2, titleWeight=1):
   results = []
   for hit in hits:
      try:
         persons = set()
         normalizedScore = 0
         creatorScore = 0
         score = 0
         if hit.has_key('title'):
            foo = process.extractBests(hit['title'], tokens)
            if len(foo) > 0:
               score += foo[0][1] * titleWeight
         if hit.has_key('creator'):
            persons = persons.union(set(hit['creator']))
         if hit.has_key('person'):
            persons = persons.union(set(hit['person']))
         if hit.has_key('contributor'):
            persons = persons.union(set(hit['contributor']))
            
         if len(persons) > 0:
            for person in persons:
               foo = process.extractBests(person, tokens)
               if foo != None:
                  creatorScore += foo[0][1]
            score += (creatorScore/len(persons)) * creatorWeight

         normalizedScore = score/(creatorWeight+titleWeight)   
         if normalizedScore >= qualityThreshold:
            bisect.insort_left(results, (normalizedScore, hit))
      except UnicodeDecodeError as e:
         continue
   if len(results) > 0:
      return results[-1]
   return None

def min(max, objectLen):
   if objectLen > max:
      end = max
   else:
      end = objectLen
   return end
   
def printEconbizOutput(res):
   if res != None:
      for r in res:
         if r.has_key('title'):
            print "title: " + r['title']
         if r.has_key('creator'):
            for s in r['creator']:
               print "creator: " + s


def searchDataprovider(action="search", field="text", query=""):
   assert (action == "search" or action == "suggest")
   if action == "search":
      response = requests.get('https://api.econbiz.de/v1/search?q=' +field + ':' + query +'&echo=on')
   if action == "suggest":
      #response = requests.get('https://api.econbiz.de/v1/suggest/' + field + '/' + query + '&echo=on')
      response = requests.get('https://api.econbiz.de/v1/suggest/' + query + '&echo=on')
      
   if response.status_code == 200:
      return response.json()
   else:
      return None
   
if __name__ == "__main__":
   main()