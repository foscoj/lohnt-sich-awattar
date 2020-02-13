from flask import Flask
import pandas as pd
import glob
import sqlite3
app = Flask(__name__)

@app.route("/")
def hello():
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
  df.rename(columns={"": "a", "B": "c"})
  df = df.drop(['mtu'], axis=1)
  df = df.set_index('mtu_start')
  # ---------------- #
  #write data to sqlite database
  conn = sqlite3.connect('.data/entsoe.db')
  c = conn.cursor()
  c.execute('CREATE TABLE PRICES (timestamp, price_kwh)')
  conn.commit()
  
  df.to_sql('PRICES', conn, if_exists='replace', index = False)
  
  return df.to_html()

if __name__ == "__main__":
  app.run()
