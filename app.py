# -*- coding:utf-8 -*-

import json
import random 
import sqlite3
from flask import Flask, request, render_template
app = Flask(__name__)

app.debug = True


class ElemInterface:
    '''
       Row object interface for filter.
    '''
    def __init__(self, name ):
        self._name = name
        self._filter = None

    def setFilter(self, filter):
        self._filter = filter

    def setRequest(self, request, n):
        self.setFilter(request.args.get("sSearch_%d" % n)) 
        self.bRegex      = request.args.get("bRegex_%d" % n) 
        self.bSearchable = request.args.get("bSearchable_%d" % n)
        self.bSortable   = request.args.get("bSortable_%d" % n)

    def isFilterSet(self):
        if  self._filter =="":
            return False
	else:
            return True

    def sqlRepr(self):
        if self._filter[0] == '-':
            return self._name +" not like '%"+ self._filter[1:] +"%' "
        elif self._filter[0] == '<' or self._filter[0] == '>':
            return " %s %s %s " % (self._name,self._filter[0], self._filter[1:])
        else:
            return self._name +" like '%"+ self._filter +"%' "

    def match(self, value):
        if  self._filter =="":
            return False
        if self._filter == str(value):
            return True
        else:
            return False

class requestBuilder:
    def __init__(self,elems, globalsearch):
        self.elems = elems
        self.globalsearch = globalsearch
        self.isFilterEmpty = self.filterEmpty()
        self.displayLength   = request.args.get("iDisplayLength")
        self.displayStart   = request.args.get("iDisplayStart")
        
    def getRequest(self):
        return ""

    def filterEmpty(self):
        if self.globalsearch !="":
            return False
        for elem in self.elems:
            if elem._filter != "":
                return False
        return True
        
    def filterMatch(self, data, columns):
        for i in range(len(columns)):
            if self.globalsearch == str(data[columns[i]]):
                return True
        allFilter=True
        for i in range(len(columns)):
            if self.elems[i]._filter != "" and self.elems[i].match(data[columns[i]]) is False:
                allFilter= False 
        
        return allFilter

    def copyRow(self,data,columns):
        aaData_row=[]
        for i in range(len(columns)):
            aaData_row.append(str(data[columns[i]]).replace('"','\\"'))
        return aaData_row

    def filterRow(self,data,columns):
        if self.filterMatch(data,columns):
            return self.copyRow(data,columns)
        else:
            return None
    
    
    def filterData(self, data, columns):
        return self.filterRow(data,columns)

class BaseDataTables:
    
    def __init__(self, request, columns,elems):
        
        self.columns = columns
        self.elems = elems
         
        # values specified by the datatable for filtering, sorting, paging
        self.request = request
        self.initRequest()
        for idx,e in enumerate(elems):
            e.setRequest(request,idx)
 
        # results from the db
        self.result_data = None
    
    def initRequest(self):
        self.globalsearch = self.request.args.get("sSearch")
        self.nbColumn = self.request.args.get("iColumns")
    
    def buildRequestBuilder(self):
        return requestBuilder(self.elems,self.globalsearch) 

    def output_result(self):
        output = {}
        aaData_rows = []
        rb = self.buildRequestBuilder()
        for row in self.result_data:
            if rb.isFilterEmpty:
                aaData_rows.append(rb.copyRow(row,self.columns))
            else:
                aaData_row = rb.filterData( row,self.columns )
                if aaData_row is not None:
                    aaData_rows.append(aaData_row)
            
        output['aaData'] = aaData_rows
        output['iTotalDisplayRecords'] = len(aaData_rows)
        return output

class requestBuilderSql(requestBuilder):

    def copyRow(self,data,columns):
        aaData_row=[]
        for i in range(len(columns)):
            aaData_row.append(str(data[i]).replace('"','\\"'))
        return aaData_row

    def getTable(self):
        return "test"

    def getWhere(self):
        where = ""
        globalwhere = ""
        if self.globalsearch!="":
            for e in self.elems:
                if globalwhere != "":
                    globalwhere = "%s  OR " % globalwhere
                globalwhere = globalwhere + " "+ e._name +" like '%"+ self.globalsearch +"%' " 

        for e in self.elems:
            if e.isFilterSet() is False:
                continue

            if where != "":
                where = "%s  AND " % where
            where = where + " "+e.sqlRepr()
            
        if where != "" or globalwhere !="":
            if where == "":
                where = "WHERE "+ globalwhere
            else:
                if globalwhere !="":
                    where = "WHERE (%s) AND (%s) " % ( globalwhere, where)
                else:
                    where = "WHERE "+where

        return where

    def getRequest(self):
    	fields = ','.join(str(e._name) for e in self.elems)
        where = self.getWhere()
        return "SELECT %s from %s  %s limit %s offset %s " % ( fields,self.getTable(), where, self.displayLength, self.displayStart )

    def getRequestCount(self):
        where = self.getWhere()
        return "SELECT count(%s) from %s  %s  " % ( self.elems[0]._name,self.getTable(), where)

class SqlDataTables(BaseDataTables):

    def buildRequestBuilder(self):
    	print("buildRequestBuilder")
        return requestBuilderSql(self.elems,self.globalsearch) 

    def getNbCount(self, request, cur):
        cur.execute(request)
        tmp = cur.fetchall()
        return tmp[0][0]

    def output_result(self):
        output = {}
        aaData_rows = []
        rb = self.buildRequestBuilder()
        conn = sqlite3.connect("test.db", timeout=1)
        cur = conn.cursor()
        totalrows = self.getNbCount("select count(*) as total from %s " % rb.getTable(), cur)
        totalrowsfilter = self.getNbCount(rb.getRequestCount(), cur)

        cur.execute(rb.getRequest())
        rows = cur.fetchall()
    	for n in range(len(rows)):
		aaData_rows.append(rb.copyRow(rows[n],self.columns))

        output['aaData'] = aaData_rows
        output['iTotalDisplayRecords'] = totalrowsfilter
        output['iTotalRecords'] = str(totalrows)
        return output

 


columns = [ 'column_1', 'column_2', 'column_3', 'column_4']

@app.route('/')
def index():
    return render_template('index.html', columns=columns)

@app.route('/_server_data')
def get_server_data():

    elems = []
    for c in columns:
        elems.append(ElemInterface(c))
    results = SqlDataTables(request, columns,elems).output_result()
    
    # return the results as a string for the datatable
    return json.dumps(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5550, debug=True)

