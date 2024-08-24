# SIADS593_Project_Russian_Propaganda

########  How to run Scraping Python Script  ########  
File name: scraping_script_v1.py

1. Save the file in your preferite folder
2. In this folder create a folder named: html_files
3. Open Anaconda Terminal or other terminal 
2. Set the location where your script is located
	cd "C:\Users\riccardoricci\OneDrive - KPMG\Documents\GitHub\SIADS593_Project_Russian_Propaganda\01.Scraping"
3. Install all the dependencies. In Anaconda Terminal:
	pip install requests
	pip install scrapy
	pip install dateparser
	pip install pandas
  Optional: create a virtual environment to manage dependencies
	(Note for Riccardo: mine is named something like env_scraping1 --> 
	conda env list
	conda activate env_scraping)
4. Change the OFFSET settings (i.e. how many pages to retrieve). Open the script using a note editor and change here:
	(Line 72) OFFSET = 0  
	(Line 74) OFFSET_INTERRUPT_AT = 15000
In the first two runs I used:
	1) OFFSET = 0 
	   OFFSET_INTERRUPT_AT = 15000
	2) OFFSET = 15000 
	   OFFSET_INTERRUPT_AT = 30000
It scraped approximately 14 months

5. In Anaconda terminal (you can also use other terminal) type:
	python  scraping_script_v1.py

6. Wait for the scraping to finish

7. Rename the files using this convention:
	<start_offset>-<end_offset>__output_scraping.csv
	<start_offset>-<end_offset>_output_scraping_cleaned.csv

	e.g. 0-15_output_scraping.csv
	e.g. 0-15_output_scraping_cleaned.csv
