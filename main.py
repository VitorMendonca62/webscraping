import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

request_headers = {'User-Agent': 'Chrome/126.0.0.0' }

class System:
  def __init__(self, date):
    self.html = self.take_html()
    self.df = self.take_df()
    
    self.date = date
  
  def take_html(self):
    html = requests.get('https://fundamentus.com.br/fii_resultado.php', headers=request_headers).content
    return BeautifulSoup(html, 'html.parser')
  
  def take_texts(self, tag):
    return tag.text
  
  def take_headers(self):
    headers_tag = self.html.find(id='tabelaResultado').find('thead').find("tr").find_all("a")
    headers =  list(map(self.take_texts, headers_tag))
    headers.insert(5, "Dividendos")
    headers.insert(7, "Bola de neve")
    return headers
  
  def take_df(self):
    data_tags =  self.html.find(id='tabelaResultado').find('tbody').find_all("tr")

    data = []

    for row in data_tags:
      row = list(map(self.take_texts, row))
      row = list(filter(self.remove_jmp_line, row))
      row = self.format_row(row)
      data.append(row)
      self.add_infos(row)
      
    return pd.DataFrame(data, columns= self.take_headers())
  
  def remove_dot_comma(self, text):
    return float(text.replace("%", "").replace(".", "").replace(",", "."))
  
  def format_row(self, row):
    row[2] = self.remove_dot_comma(row[2])
    row[3] = round(self.remove_dot_comma(row[3]) / 100, 4)
    row[4] = round((self.remove_dot_comma(row[4]) / 12) / 100, 6)
    row[5] = self.remove_dot_comma(row[5])
    row[6] = self.remove_dot_comma(row[6])
    row[7] = self.remove_dot_comma(row[7])
    row[8] = int(row[8])
    row[9] = self.remove_dot_comma(row[9])
    row[10] = self.remove_dot_comma(row[10])
    row[11] = self.remove_dot_comma(row[11]) / 100
    row[12] = self.remove_dot_comma(row[12]) / 100
    
    return row
  def add_infos(self, row):
    stock = row[2]
    
    dividend_yields = row[4]
    dividend = round(stock * dividend_yields, 2) 
    
    magic_number = int(stock / dividend) + 1 if dividend != 0 else 0
    
    row.insert(5, dividend)
    row.insert(7, magic_number)
    
    return row
    
  def remove_jmp_line(self, elem):
    return elem != "\n"
    
class Filter:
  def __init__(self):
    self.pvp = 0.007
    self.dividend_yield = 0.005
    self.vacancy = 0.10
    self.min_stock = 7
    self.max_stock = 20
    self.value = 1000000
    
  def filter_fiis(self, fiis):
    fiis = fiis[fiis["P/VP"] > self.pvp]
    fiis = fiis[fiis["Dividend Yield"] > self.dividend_yield]
    fiis = fiis[fiis["Vacância Média"] < self.dividend_yield]
    fiis = fiis[fiis["Cotação"] < self.max_stock]
    fiis = fiis[fiis["Cotação"] > self.min_stock]
    fiis = fiis[fiis["Valor de Mercado"] > self.value]
    
    return fiis
  
  def remove_dot(self, series):
    
    return series.astype(str).str.replace(".", ",")
  
  def format_market_value(self, value):
    if value >= 1000000000: return f"R$ {int(value / 1000000000)} B"
    if value >= 1000000: return f"R$ {int(value / 1000000)} M"
    if value >= 1000: return f"R$ {int(value / 1000)} mil"
  
  def format_df(self, fiis):
    fiis["Cotação"] = self.remove_dot(fiis["Cotação"])
    fiis["FFO Yield"] = self.remove_dot(fiis["FFO Yield"])
    fiis["Dividend Yield"] = self.remove_dot(fiis["Dividend Yield"])
    fiis["Dividendos"] = self.remove_dot(fiis["Dividendos"])
    fiis["P/VP"] = self.remove_dot(fiis["P/VP"])
    fiis["Cap Rate"] = self.remove_dot(fiis["Cap Rate"])
    fiis["Vacância Média"] = self.remove_dot(fiis["Vacância Média"])
    fiis["Aluguel por m2"] = self.remove_dot(fiis["Aluguel por m2"])
    fiis["Preço do m2"] = self.remove_dot(fiis["Preço do m2"])
    fiis["Valor de Mercado"] = fiis["Valor de Mercado"].apply(self.format_market_value)
    return fiis
    
date_now = datetime.now().strftime("%d-%m-%Y")
system = System(date_now)
filtered = Filter()
fiis_filtered = filtered.filter_fiis(system.df)
fiis_formated = filtered.format_df(fiis_filtered)

fiis_filtered.to_csv(f"fiis-{date_now}.csv", sep=";")