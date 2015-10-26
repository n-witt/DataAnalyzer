# DataAnalyzer
This prototype is based on the the BlogCrawler that can be found [here](https://github.com/n-witt/BlogCrawler). It searches hyperlinks to PDF-files and downloads them. In the next step it tries to find a matching document in [EconBiz](http://www.econbiz.de/) database.
It implements the following strategy:
  * The program checks whether the meta data fields author and text of the file contain any information. If so, it sends a query assembled from these strings to EconBiz. After fetching the result list, the length of the list is checked. In case the result list is longer than zero, all results are examined and assessed (details will be described in the next paragraph). When there is no result above a predefined quality threshold, the second stage is executed, otherwise the result is stored and the processing continues with the next document.
  * After the text of the first page of the file is retrieved, the text is divided into smaller chunks (using punctuation and newline-symbols for that). The processing of these parts of sentences is similar to the processing of the metadata in the previous section. They are passed to the EconBiz API and the results are examined. If there is no result above a predefined quality threshold, no match was found. Otherwise the list of potential matches is stored.

To assess the quality of the results, a fuzzy string comparison library called [fuzzywuzzy](https://pypi.python.org/pypi/fuzzywuzzy/0.2) is used. It contains a method that is invoked with an arbitrary string (selector) and a list of strings (choices). The method returns the choices sorted by closest match of the selector. Every item of the list also comes with a value from 0 to 100 which is the measure of quality. The following example illustrates that:
```
> choices = ["apple pie", "apples", "spaghetti"]
> process.extract("apple", choices)
[('apples', 91), ('apple pie', 90), ('spaghetti', 36)]
> process.extract("apples", choices)
[('apples', 100), ('apple pie', 74), ('spaghetti', 29)]}
```
The quality value is used to decide if a document matches the search query.

The limitation to the first page is due to the fact that extraction of the text is a computationally intensive task that can be mitigated by the limitation. Furthermore we assume that the first page contains the authors name and the title of the document, which is true for many scientific papers. And it is this information that are particularly valuable for descent search results.

## Requirements
  * Linux or Mac OS X
  * Python 2.7 or newer
  * fuzzywuzzy
  * PyPDF2
  * pdfminer
## Installation
The recommended installation preliminaries and procedure for the Data Analyzer are the same as for the Blog Crawler. The following was tested with Ubuntu 14.04. To install the dependencies, these commands should be used:
```
sudo apt-get install -y python python-pip git
sudo pip install fuzzywuzzy PyPDF2 pdfminer
```
Afterwards the repository can be cloned:
```
git clone purl.org/eexcess/components/research/bloganalyzer
```
Finally, the analyzer can started with these commands:
```
cd DataAnalyzer/eu/zbw/
python pdfMetadataExtractor.py
```
The script will analyze the File in the `samples` directory. The results will be printed when all the computation is done. Every file will be mentioned in the output. The output could look like this:
```
10. match: True
  quality: 90
  filename: bakken\_fullactivity\_Jan3-2013.pdf
  id: 10004941699
  title: Staff report Research Department of the Federal Reserve Bank of Minneapolis
  participant: Minneapolis, Minn. : Federal Reserve Bank of Minneapolis
```
`match: True` denotes that EconBiz found an entry. `quality` refers to the likelihood that the entry found by EconBiz and and file that has been processes correspond. `id, title` and `participant` refer to the entry found by EconBiz.
