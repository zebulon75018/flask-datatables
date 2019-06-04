# -*- coding:utf-8 -*-

import json
import random 
from flask import Flask, request, render_template
app = Flask(__name__)

app.debug = True

class ElemInterface:
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

    def match(self, value):
        if  self._filter =="":
            return False
        if self._filter == value:
            return True
        else:
            return False

class requestBuilder:
    def __init__(self,elems, globalsearch):
        self.elems = elems
        self.globalsearch = globalsearch

    def getRequest(self):
        return ""
        
    def filterData(self, data, columns):
        aaData_row = []
        found = False
        for i in range(len(columns)):
                #data = rb.filterData(data[ columns[i]], i )
                for elem in self.elems:
                    if elem.match(data[columns[i]]):
                        found = True

                if  self.globalsearch =="":
                    found = True
                else:
                    if  str(data[columns[i]]) == self.globalsearch :
                        found = True
                aaData_row.append(str(data[columns[i]]).replace('"','\\"'))
        if found:
            return aaData_row
        else: 
            return None

class BaseDataTables:
    
    def __init__(self, request, columns, collection,elems):
        
        self.columns = columns

        self.collection = collection
        self.elems = elems
         
        # values specified by the datatable for filtering, sorting, paging
        #self.request_values = request.values
        self.request = request
        self.initRequest()
        for idx,e in enumerate(elems):
            e.setRequest(request,idx)
        #print(self.request_values)
 
        # results from the db
        self.result_data = None
        # total in the table after filtering 
        self.cardinality_filtered = 0
        # total in the table unfiltered
        self.cadinality = 0
        self.run_queries()
    
    def initRequest(self):
        self.globalsearch = self.request.args.get("sSearch")
        self.nbColumn = self.request.args.get("iColumns")
    
    def output_result(self):
        output = {}
        # print(self.columns)
        # output['sEcho'] = str(int(self.request_values['sEcho']))
        # output['iTotalRecords'] = str(self.cardinality)
        # output['iTotalDisplayRecords'] = str(self.cardinality_filtered)
        aaData_rows = []
        rb = requestBuilder(self.elems,self.globalsearch) 
        # print(self.result_data)
        for row in self.result_data:
            aaData_row = rb.filterData( row,self.columns )
            if aaData_row is not None:
                aaData_rows.append(aaData_row)
            
        output['aaData'] = aaData_rows
        return output
    
    def run_queries(self):        
         self.result_data = self.collection
         self.cardinality_filtered = len(self.result_data)
         self.cardinality = len(self.result_data)

columns = [ 'column_1', 'column_2', 'column_3', 'column_4']

@app.route('/')
def index():
    return render_template('index.html', columns=columns)

@app.route('/_server_data')
def get_server_data():
    elems = [ ElemInterface(1),ElemInterface(2),ElemInterface(3),ElemInterface(4)]
    collection = []
    for n in range(10):
        collection.append(dict(zip(columns, [n,n+1,n+2,n+3])))
    #[dict(zip(columns, [1,2,3,4])), dict(zip(columns, [5,5,5,5]))]
    """collection = []
    collection.append([random.random() for _ in range(4)])
    collection.append([random.random() for _ in range(4)])
    collection.append([random.random() for _ in range(4)])
    collection.append([random.random() for _ in range(4)])
    """
    results = BaseDataTables(request, columns, collection,elems).output_result()
    
    # return the results as a string for the datatable
    return json.dumps(results)

if __name__ == '__main__':
    app.run()