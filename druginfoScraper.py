from urllib.request import *
from urllib.parse import *
import re, os, sys
from os.path import splitext, basename
from bs4 import BeautifulSoup
import csv



class DrugInfoScraper:
	host = 'http://www.druginfo.co.kr'
	query_url = 'https://www.druginfo.co.kr/search2/search.aspx?q='	
	Cookie = 'ASP.NET_SessionId=scqnaj55dafokh551xpock45; userId=4b41bfdbce851c5c6054cb1cd08652039d8ee2ba4667212a3e60f477e41bf5a86a2bf9a3502bb31e56c9df50c4840d48; userIp=9ba91e4438eee45af0b3b1894b0c8275c7f7b9cb37f15852d47890dde19ba157591c2f11e027b27d95770e9c44a183ab; userName=4b41bfdbce851c5c6054cb1cd08652039d8ee2ba4667212a3e60f477e41bf5a86a2bf9a3502bb31e56c9df50c4840d48; userPid=821eb4cc42c9e7cf78e862ba364c0f7ec2ae58e3d5f020cb6f88445f715f9def2474b752c2f8c56cfa9b3d35b50793cd; userRole=29c54268c67af58cc7a52cb43b6e6f9fdb06a52942fdb8bb7abdd02b2a8b37e05bfebe9d097cafe2e4e5abfa29d45f84; userTime=6d062f244f9375adf43370ba9f6035fa65b836afe5e9a9d5cd5f903f0f196919893b79108d76f34c0cfeebbfb24e88ce; userJobSort=ee09654fd166be3a1edbd355910e162380ca9d56a7b5168adf9f9b851a90d8f8; userPoint=fe6c737e30d8212f60774d6f8906fcea5497b00e09df2ee3056008c9cc6414a6; userTel=dd2af4acba624126d1d1d3423ecd5fb503656272a3602d6f94d9dbf2010ee9246f616b17f670969125cd8de3ac8dc199; userEmail=b56ee86ed55f5cf1e2ee3b7a7ab57e138d03144e78deed3df75249b2c0efa021ba0c71c2d49221b0dbff2abc0e4a3d8c; userSummits=63909e4b140e52b890502e3f1e2bc6a64c6391fc8f99bd8dd393ec82097afb05; companyName=63909e4b140e52b890502e3f1e2bc6a64c6391fc8f99bd8dd393ec82097afb05; prevUrl=http://www.druginfo.co.kr/detail/product.aspx?pid=5939&; _ga=GA1.3.302705196.1464690478; __utma=133333467.302705196.1464690478.1464693111.1464697480.3; __utmb=133333467.3.10.1464697480; __utmc=133333467; __utmz=133333467.1464690478.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)'
	def GetSoupParserFromQueryPage(self, query):
		if not isinstance(query,str): query = str(query)
		url = self.query_url + quote(query.encode('cp949'))
		rsp = urlopen(url)
		return BeautifulSoup(rsp.read(),'html.parser')
	def GetDrugInfoHtml(self, drug_url):
		req = Request(drug_url)
		req.add_header('Cookie', self.Cookie)
		return urlopen(req).read()

	def GetDrugSearchTable(self, keyWord, bHeader = True):
		obj_soup = self.GetSoupParserFromQueryPage(keyWord)
		div_res = obj_soup.findAll('div',class_='res table-res')
		header = tables = []
		tbl_struct = {
			0  : lambda x : urljoin(self.host, x.text.split(',')[1]) if x.a else '',
			1  : lambda x : x.a.string,
			2  : lambda x : splitext(basename(x.img.get('src')))[0] if x.img else '',
			10 : lambda x :urljoin(self.host, x.a.get('href'))
		}
		for div in div_res:
			table = []
			for r, tr in enumerate(div.table('tr')):
				row = []
				td_data = None
				for c, td in enumerate(tr('td')):
					if r and c in tbl_struct:
						td_data = tbl_struct[c](td)
					else:
						td_data = td.text
					row.append(td_data.strip())
				table.append(row)
				
			if "제품명" in table[0]:
				 header, *tuples = table
				 tables += tuples
		if bHeader:
			ret = [header] + tables if header else [keyWord, "검색어 오류"]
		else:
			ret = tables if header else [keyWord, "검색어 오류"]
		return  ret
	def GetDrugUrlFromEDICode(self, EDI_CODE):
		szCode = str(EDI_CODE)
		obj_soup = self.GetSoupParserFromQueryPage(szCode)
		if len(szCode) == 9 and szCode.isdigit():
			if obj_soup.find_all('div',id='msg-no-results'):
				return "about:blank"
			else:
				return self.host + obj_soup.find_all('a',class_='product-link preview-product')[0]['href']
		else: 
			return 'EDI code format error'
	def GetDrugImgUrlAndIDFromEDICode(self, EDI_CODE):
		imgUrlPath = "https://www.druginfo.co.kr/drugimg/"
		szCode = str(EDI_CODE)
		obj_soup = self.GetSoupParserFromQueryPage(szCode)
		try:
			imglnk = obj_soup.find_all('a',class_='pro-img-link')[0]
		except IndexError:
			return 0, 0
		else:
			imgfile = imglnk.text.split(',')
			return imgUrlPath + imgfile[1], imgfile[0]
	def GetDrugNameFromEDI(self, EDI_CODE):
		tbl = self.GetDrugSearchTable(EDI_CODE,False)
		if tbl: return tbl[0][1]



def WriteToCSV(tbl, csvFile):
	with open(csvFile,'wt', newline ='') as fp:
		wtr = csv.writer(fp)
		for row in tbl:
			wtr.writerow(row)

if len(sys.argv) >1:
	edis = ' '.join(sys.argv[1:])

d = DrugInfoScraper()
edis = edis.split()
ret = []
for i in range(0, len(edis),100):
	fld = rec = []
	kw = ' '.join(edis[i:i+100])
	ret += d.GetDrugSearchTable(kw, not i)

WriteToCSV(ret,'result.csv')
os.startfile('result.csv')