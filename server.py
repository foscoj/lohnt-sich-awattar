from flask import Flask, request
import pandas as pd
import glob
import sqlite3
app = Flask(__name__)

@app.route("/")
def base():
  
  conn = sqlite3.connect('.data/entsoe.db')
  c = conn.cursor()
  c.execute('''SELECT 'first',* FROM PRICES ORDER BY timestamp ASC LIMIT 1''')
  
  s='''<html><head><title>Dyncamic power contract calculator</title></head><body>
      <form action="/upload" method="post">
        Select .csv to upload:
        <input type="file" name="fileToUpload" id="fileToUpload" enctype=multipart/form-data>
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

@app.route("/upload",methods=['POST'])
def upload():
  if request.method == 'POST':
    print("post")
    print(request)
    file = request.files['file']
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        print("dateiname:"+str(file))
        data = pd.read_csv(file)
        print(data)
    
    
  return '<a href="/">back to homepage</a>'+data.to_html()

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
