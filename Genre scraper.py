# -*- coding: utf-8 -*-
"""
Created on Mon Mar  1 08:14:19 2021

@author: Wallac_A
"""

from selenium import webdriver
import time
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import wikipedia
from urllib.request import urlopen
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from matplotlib import pyplot as plt
import sqlite3
import numpy as np
import sys

def genreFind(driver):
    
    genre = "not found"
    found = False
    if found == False:
        try:
            box = driver.find_element_by_xpath('/html/body/div[7]/div/div[6]/div/div/div/div[1]/div/div[1]/g-scrolling-carousel/div[1]/div/div/a[1]/div/div/div/div')
            genre=box.text
            found = True
        except:
            found = False
            print("yes")
    if found == False: 
        try:
            box = driver.find_element_by_xpath('//*[@id="rso"]/div[1]/div/div[1]/div[1]/div[1]/div/div[2]/div/div/div/div[1]')
            genre=box.text
            found = True
        except:
            found = False
            print("yes")
    if found == False:   
        try:
            box = driver.find_element_by_xpath('//*[@id="rso"]/div[1]/div/div[1]/div[1]/div[1]/div/div[2]/div/div/div/div[1]/a')
            genre=box.text
            found = True
            
        except:
            found = False
            print("yes")
        #genre = "Not Found"
    return genre

def doSearch(song,lenprev,driver):
    search = driver.find_element_by_name('q')
    for j in range(lenprev):
        search.send_keys(Keys.BACKSPACE)
    search.send_keys(song)
    search.send_keys(Keys.ENTER)
    
def getYear(cur,year,rank=1):    
    cur.execute("SELECT DISTINCT song, SUBSTR(date,0,5) AS year,artist FROM tracks WHERE rank='"+str(rank)+"'  AND year = '"+str(year)+"' ;")
    row = cur.fetchall()
    return row


def completeScrape(r,driver,lenprev):
    song = r[0] +" "+str(r[2])+" genre"
    doSearch(song,lenprev,driver)
    lenprev = len(song)
    #time.sleep(0.5)
    #driver.find_element_by_xpath('/html/body/div[1]/div[3]/form/div[1]/div[1]/div[3]/center/input[1]').click()
    #time.sleep(2)
    genre = genreFind(driver)
    print(genre)

            
    if genre=="not found":
        song = r[0] +" song genre"
        doSearch(song,lenprev,driver)
        lenprev = len(song)
        #time.sleep(1)
        #driver.find_element_by_xpath('/html/body/div[1]/div[3]/form/div[1]/div[1]/div[3]/center/input[1]').click()
        # time.sleep(0.5)
        genre = genreFind(driver)
        print(genre)
    if genre=="not found":
        if "/" in r[0]:
            song = r[0]
            k=song.find("/")
            song = song[:k]+" genre"
        elif "(" in r[0]:
            song = r[0]
            k=song.find("(")
            song = song[:k]+" genre"
        
        doSearch(song,lenprev,driver)
        lenprev = len(song)
        genre = genreFind(driver)
        print(genre)
    #genre = box.getAttribute("value")
    return genre,lenprev

def genreClean(genre):
    if " music" in genre:
        genre = genre.replace(" music","")   
    return genre
    
def autoClean(final):
    final = final.copy()
    final = final.reset_index()
    final = final.drop_duplicates("Song")
    final = final.drop("index",axis=1)
    corrections = pd.read_csv("Logged Changes")
    for col in corrections.columns:
        bad = final.loc[final["Genre"]==col]
        final.loc[bad.index,"Genre"]=corrections.loc[0,col]
    return final

def manualClean(final):
    final = final.copy()
    final = final.reset_index()
    final = final.drop("index",axis=1)
    genres = set(final["Genre"])
    print(genres)
    acceptedgenres = []
    if "not found" in genres:
       genres.remove("not found")
    savedchanges = {}
    for genre in genres:
        check = False
        while check==False:
            print(f"is {genre} acceptable?")
            print("1 for Yes 2 for No q for quit")
            x=input()
            if x=="1":
                acceptedgenres.append(genre)
                check = True
                continue
            elif x=="2":
                thisgenre = final.loc[final["Genre"]==genre]
                songs = list(thisgenre["Song"])
                print("Songs with this genre:")
                print(",".join(songs))
                print("Please insert new correct genre" )
                newgenre = input()
                final.loc[thisgenre.index,"Genre"]=newgenre
                savedchanges[genre]= newgenre
                check = True
            elif x=="q":
                sys.exit()
            else:
                print("Bad input")
    notfounds = final.loc[final["Genre"]=="not found"]
    for i in notfounds.index:
        song = final.loc[i,"Song"]
        print(f"Genre for {song} not found, input its actual genre")
        newgenre = input()
        final.loc[i,"Genre"]=newgenre
                          
    return final,acceptedgenres,savedchanges
            
   #%%         
            
            
def createStackplot(final,interval=5,bestx=10):
    years = list(set(final["Year"]))
    years.sort()
    years = range(int(min(years)),int(max(years))+1+interval,interval)
    genres = list(set(final["Genre"]))
    stack = pd.DataFrame(np.zeros([len(genres),len(years)]),index = genres,columns=years)
        
    for year in years:
        frame = final.loc[final["Year"]>=str(year)  ]
        frame = frame.loc[frame["Year"]<str(year+interval)]
        counts=frame["Genre"].value_counts(normalize=True)
        for i in counts.index:
            stack.loc[i,year]=counts[i]
    sums=stack.sum(axis=1).sort_values(ascending = False)
    bestfive = sums[:bestx].index
    stack = stack.loc[bestfive,:]
    fig, ax = plt.subplots()
    ax.stackplot(stack.columns, stack,labels = stack.index)
    ax.legend(loc='upper left')
    ax.set_title('Genres over the years')
    plt.show()
    
def saveTable(final,cur,name="genres"):
    cur.execute("DROP TABLE IF EXISTS genres;")
    final = final.reset_index()
    final = final.drop("index",axis=1)
    final["Year"]=final["Year"].astype(str)
    final = final.drop_duplicates()
    create_table = """
                    CREATE TABLE IF NOT EXISTS """+name+"""  (
                        id INTEGER PRIMARY KEY,
                        song TEXT NOT NULL,
                        year TEXT,
                        genre TEXT
                    );
                """
    cur.execute(create_table)
    for i in final.index:
        row = tuple(final.loc[i,:])
        cur.execute("INSERT INTO " + name + " (song,year,genre) VALUES (?, ?, ?)", row)
        
def getTable(name,cur):
    cur.execute("PRAGMA table_info(genres);")
    cols = cur.fetchall()
    cols = [x[1] for x in cols]
    cur.execute("SELECT * FROM genres")
    row = cur.fetchall()
    table = pd.DataFrame(row,columns = cols)  
    return table

def main():
    db = sqlite3.connect("Music.db")
    #Connect to Music Database
    cur = db.cursor()
    #Create dataframe to store output data
    final=pd.DataFrame(columns = ["Song","Year","Genre"])
    
    for year in range(1958,2022):
        #Have to scrape through one year at a time to avoid being flagged as a bot
        row = getYear(cur,year,rank=1)
        #Get the number one hits from this year
        for r in row:
            print(r)
        
        
        driver = webdriver.Chrome(r'C:\Users\wallac_a\Downloads\chromedriver_win32\chromedriver')
        driver.get('https://www.google.co.uk/')
        
        time.sleep(1)
        driver.find_element_by_xpath('/html/body/div[2]/div[2]/div[3]/span/div/div/div[3]/button[2]/div').click()
        genrestore = []
        lenprev=0
        for r in row:
            genre,lenprev = completeScrape(r,driver,lenprev)
    
            genre = genreClean(genre)  
            genrestore.append((r[0],r[1],genre))
        df=pd.DataFrame(genrestore)
        df.columns = ["Song","Year","Genre"]
    
        final=pd.concat([final,df])
        driver.close()
        
    final = autoClean(final)
    createStackplot(final,interval=5)
    saveTable(final,cur)
    df = getTable("genres",cur)
    print(df) 
    cur.close()
    db.close()
    return final
    
if __name__ == "__main__":
    final=main()
    
    final,good,changes = manualClean(final)
