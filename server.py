from flask import Flask
import pandas as pd
app = Flask(__name__)

@app.route("/")
def hello():
  df = pd.read_csv('entsoe_2019.csv',skiprows=1,names=['mtu','price_mwh'])
  df['price_kwh'] = df['price_mwh'] / 1000
  df = df.drop(['price_mwh'], axis=1)
  new = df['mtu'].str.split(' - ',n=1,expand=True)
  df['mtu_start'] = pd.to_datetime(new[0])
  #df['mtu_stop'] = pd.to_datetime(new[1])
  df = df.drop(['mtu'], axis=1)
  #df = df.drop(['mtu_stop'], axis=1)
  df = df.sort_index(axis=1)
  df = df.set_index('mtu_start')
  return df

if __name__ == "__main__":
  app.run()
