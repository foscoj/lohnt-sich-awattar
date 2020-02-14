from flask import Flask, request
import pandas as pd
import glob
import sqlite3
app = Flask(__name__)

def wh_to_kwh(x):
    return x/1000

@app.route("/")
def base():
  
  conn = sqlite3.connect('.data/entsoe.db')
  c = conn.cursor()
  c.execute('''SELECT 'first',* FROM PRICES ORDER BY timestamp ASC LIMIT 1''')
  
  s='''<html><head><title>Dyncamic power contract calculator</title></head><body>
      <form action="/upload" method="post" enctype = "multipart/form-data" >
        Select .csv to upload:
        <input type="file" name="file" id="file">
        <input type="submit" value="Upload Discovergy.csv" name="submit">
      </form>
      <h2>Current Data</h2>'''
  
  for row in c.fetchall():
    s+=str(row)+"<br>"
    
  c.execute('''SELECT 'last',* FROM PRICES ORDER BY timestamp DESC LIMIT 1''')
  
  for row in c.fetchall():
    s+=str(row)+"<br>"
    
  conn.close()
  
  s+='<br><a href="./initcsv">Initialize database from entsoe*.csv files (takes some time, only necessary once)</a></body></html>'
  
  return s

@app.route("/upload",methods=['GET','POST'])
def upload():
  if request.method == 'POST':
    # check if the post request has the file part
    if 'file' not in request.files:
        print('No file part')
        return "no file part"
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        print('No selected file')
        return "no selected file"
    if file:
        print("dateiname:"+str(file))
        dfup = pd.read_csv(file,skiprows=1,names=['timestamp','stand','w'], parse_dates=['timestamp'],usecols=['timestamp','w'],index_col=['timestamp'])
        #print(dfup)
        dfup['kwh']=dfup['w']/1000
        dfup = dfup.drop(['w'], axis=1)
        #dfup = dfup.rename(columns={"Zeit": "timestamp","kwh":"kwh"})
        #print(dfup.dtypes)
        print(dfup)
        conn = sqlite3.connect('.data/entsoe.db')
        df = pd.read_sql(
          '''select
          timestamp,
          price_kwh
          from PRICES''', conn,index_col=['timestamp'],parse_dates=['timestamp'])
        print(df)
        print(dfup.index)
        print(df.index)
        dfmerge = pd.merge(dfup, df, left_index=True, right_index=True)
        dfmerge['cost']=dfmerge['kwh']*(dfmerge['price_kwh']+0.2057)
        #print(dfmerge)
        monthly = dfmerge['cost'].groupby([lambda x: x.year, lambda x: x.month]).sum().round(2)
        
        print(monthly)
        conn.close()
    
  return '<a href="/">back to homepage</a><br>'+monthly.to_frame().to_html() +'<br>Dynamic cost: ' + str(monthly.sum().round(2)) + ' € <br><br>'

@app.route("/initcsv")
def init_csv():
  #read csv data (should only be read of db does not exist)
  extension = 'csv'
  all_files = glob.glob('entsoe*.{}'.format(extension))
  print(all_files)
  df = pd.concat((pd.read_csv(f,index_col=None,skiprows=1,names=['mtu','price_mwh'],na_values='n/e') for f in all_files),ignore_index=True)
  # ---------------- #  
  #create dataframe with all necessary inputs from entsoe
  df['price_kwh'] = df['price_mwh'] / 1000
  df = df.drop(['price_mwh'], axis=1)
  new = df['mtu'].str.split(' - ',n=1,expand=True)
  df['mtu_start'] = pd.to_datetime(new[0])
  df.rename(columns={"mtu_start": "timestamp","price_kwh":"price_kwh"},inplace=True)
  df = df.drop(['mtu'], axis=1)
  df = df.set_index('timestamp')
  # ---------------- #
  #write data to sqlite database
  conn = sqlite3.connect('.data/entsoe.db')
  c = conn.cursor()
  c.execute('CREATE TABLE IF NOT EXISTS PRICES (timestamp, price_kwh)')
  conn.commit()
  #execute the real write
  df.to_sql('PRICES', conn, if_exists='replace', index = True)
  #test sqlite content
  c.execute('''SELECT timestamp,price_kwh FROM PRICES LIMIT 10''')

  for row in c.fetchall():
    print (row)
    
  conn.close()
  return '<a href="/">back to homepage</a>'+df.to_html()

if __name__ == "__main__":
  app.run()
