"""
Massive.com (formerly Polygon.io) API Client
Handles stocks, ETFs, and commodity ETFs
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import time
import config

class MassiveClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = config.MASSIVE_BASE_URL
        
    def get_weekly_data(self, symbol: str, weeks: int = 20) -> List[float]:
        """
        Get weekly closing prices for a symbol
        Returns list of closes, most recent first
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks + 30)
        
        url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/1/week/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        
        params = {
            'adjusted': 'true',
            'sort': 'desc',
            'limit': 50,
            'apiKey': self.api_key
        }
        
        try:
            all_closes = []
            current_url = url
            params_copy = params.copy()
            
            while current_url and len(all_closes) < weeks:
                response = requests.get(current_url, params=params_copy, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'results' not in data or not data['results']:
                    break
                
                closes = [bar['c'] for bar in data['results']]
                all_closes.extend(closes)
                
                if 'next_url' in data and data['next_url'] and len(all_closes) < weeks:
                    current_url = data['next_url']
                    params_copy = {'apiKey': self.api_key}
                else:
                    break
            
            if len(all_closes) < weeks:
                raise ValueError(f"Insufficient data: {len(all_closes)} weeks")
            
            return all_closes[:weeks]
            
        except Exception as e:
            raise
    
    def get_sp_1500_symbols(self) -> List[str]:
        """Complete S&P 1500 from official source"""
        return ['A','AA','AAL','AAMI','AAON','AAP','AAPL','AAT','ABBV','ABCB','ABG','ABM','ABNB','ABR','ABT','ACA','ACAD','ACGL','ACHC','ACI','ACIW','ACLS','ACM','ACMR','ACN','ACT','ADAM','ADBE','ADC','ADEA','ADI','ADM','ADMA','ADNT','ADP','ADSK','ADT','ADUS','AEE','AEIS','AEO','AEP','AES','AESI','AFG','AFL','AGCO','AGO','AGYS','AHCO','AHH','AHR','AIG','AIN','AIR','AIT','AIZ','AJG','AKAM','AKR','AL','ALB','ALEX','ALG','ALGM','ALGN','ALGT','ALK','ALKS','ALL','ALLE','ALLY','ALRM','ALV','AM','AMAT','AMCR','AMD','AME','AMG','AMGN','AMH','AMKR','AMN','AMP','AMPH','AMR','AMRX','AMSF','AMT','AMTM','AMWD','AMZN','AN','ANDE','ANET','ANF','ANGI','ANIP','AON','AORT','AOS','AOSL','APA','APAM','APD','APG','APH','APLE','APLS','APO','APOG','APP','APPF','APTV','AR','ARCB','ARE','ARES','ARI','ARLO','ARMK','AROC','ARR','ARW','ARWR','ASB','ASGN','ASH','ASO','ASTE','ASTH','ATEN','ATGE','ATI','ATO','ATR','AUB','AVA','AVAV','AVB','AVGO','AVNS','AVNT','AVT','AVTR','AVY','AWI','AWK','AWR','AX','AXON','AXP','AXTA','AYI','AZO','AZTA','AZZ','BA','BAC','BAH','BALL','BANC','BANF','BANR','BAX','BBT','BBWI','BBY','BC','BCC','BCO','BCPC','BDC','BDX','BEN','BF.B','BFH','BFS','BG','BGC','BHE','BHF','BIIB','BILL','BIO','BJ','BJRI','BK','BKE','BKH','BKNG','BKR','BKU','BL','BLD','BLDR','BLFS','BLK','BLKB','BLMN','BMI','BMRN','BMY','BOH','BOOT','BOX','BR','BRBR','BRC','BRK.B','BRKR','BRO','BROS','BRX','BSX','BSY','BTSG','BTU','BURL','BWA','BWXT','BX','BXMT','BXP','BYD','C','CABO','CACI','CAG','CAH','CAKE','CALM','CALX','CALY','CAR','CARG','CARR','CARS','CART','CASH','CASY','CAT','CATY','CAVA','CB','CBOE','CBRE','CBRL','CBSH','CBT','CBU','CC','CCI','CCK','CCL','CCOI','CCS','CDNS','CDP','CDW','CE','CEG','CELH','CENT','CENTA','CENX','CERT','CF','CFFN','CFG','CFR','CG','CGNX','CHCO','CHD','CHDN','CHE','CHEF','CHH','CHRD','CHRW','CHTR','CHWY','CI','CIEN','CINF','CL','CLB','CLF','CLH','CLSK','CLX','CMC','CMCSA','CME','CMG','CMI','CMS','CNC','CNH','CNK','CNM','CNMD','CNO','CNP','CNR','CNS','CNX','CNXC','CNXN','COF','COHR','COHU','COIN','COKE','COLB','COLL','COLM','CON','COO','COP','COR','CORT','COST','COTY','CPAY','CPB','CPF','CPK','CPRI','CPRT','CPRX','CPT','CR','CRBG','CRC','CRGY','CRH','CRI','CRK','CRL','CRM','CROX','CRS','CRSR','CRUS','CRVL','CRWD','CSCO','CSGP','CSGS','CSL','CSR','CSW','CSX','CTAS','CTKB','CTRA','CTRE','CTS','CTSH','CTVA','CUBE','CUBI','CURB','CUZ','CVBF','CVCO','CVI','CVLT','CVNA','CVS','CVX','CW','CWEN','CWEN.A','CWK','CWST','CWT','CXM','CXT','CXW','CYTK','CZR','D','DAL','DAN','DAR','DASH','DBX','DCH','DCI','DCOM','DD','DDOG','DE','DEA','DECK','DEI','DELL','DFH','DFIN','DG','DGII','DGX','DHI','DHR','DINO','DIOD','DIS','DKS','DLB','DLR','DLTR','DLX','DNOW','DOC','DOCN','DOCS','DOCU','DORM','DOV','DOW','DPZ','DRH','DRI','DT','DTE','DTM','DUK','DUOL','DV','DVA','DVN','DXC','DXCM','DXPE','DY','EA','EAT','EBAY','ECG','ECL','ECPG','ED','EEFT','EFC','EFX','EG','EGBN','EGP','EHC','EIG','EIX','EL','ELAN','ELF','ELS','ELV','EMBC','EME','EMN','EMR','ENOV','ENPH','ENR','ENS','ENSG','ENTG','ENVA','EOG','EPAC','EPAM','EPC','EPR','EPRT','EQH','EQIX','EQR','EQT','ERIE','ES','ESAB','ESE','ESI','ESNT','ESS','ETD','ETN','ETR','ETSY','EVR','EVRG','EVTC','EW','EWBC','EXC','EXE','EXEL','EXLS','EXP','EXPD','EXPE','EXPI','EXPO','EXR','EXTR','EYE','EZPW','F','FAF','FANG','FAST','FBIN','FBK','FBNC','FBP','FBRT','FCF','FCFS','FCN','FCPT','FCX','FDP','FDS','FDX','FE','FELE','FFBC','FFIN','FFIV','FHB','FHI','FHN','FIBK','FICO','FIS','FISV','FITB','FIVE','FIX','FIZZ','FLEX','FLG','FLO','FLR','FLS','FMC','FN','FNB','FND','FNF','FORM','FOUR','FOX','FOXA','FOXF','FR','FRPT','FRT','FSLR','FSS','FTDR','FTI','FTNT','FTRE','FTV','FUL','FULT','FUN','FWRD','G','GAP','GATX','GBCI','GBX','GD','GDDY','GDEN','GDYN','GE','GEF','GEHC','GEN','GEO','GEV','GFF','GGG','GHC','GIII','GILD','GIS','GKOS','GL','GLPI','GLW','GM','GME','GMED','GNL','GNRC','GNTX','GNW','GO','GOGO','GOLF','GOOG','GOOGL','GPC','GPI','GPK','GPN','GRBK','GRMN','GS','GSHD','GT','GTES','GTLS','GTM','GTY','GVA','GWRE','GWW','GXO','H','HAE','HAFC','HAL','HALO','HAS','HASI','HAYW','HBAN','HCA','HCC','HCI','HCSG','HD','HE','HFWA','HGV','HIG','HII','HIMS','HIW','HL','HLI','HLIT','HLNE','HLT','HLX','HMN','HNI','HOG','HOLX','HOMB','HON','HOOD','HOPE','HP','HPE','HPQ','HQY','HR','HRB','HRL','HRMY','HSIC','HST','HSTM','HSY','HTH','HTLD','HTO','HTZ','HUBB','HUBG','HUM','HWC','HWKN','HWM','HXL','HZO','IAC','IART','IBKR','IBM','IBOC','IBP','ICE','ICHR','ICUI','IDA','IDCC','IDXX','IEX','IFF','IIIN','IIPR','ILMN','INCY','INDB','INDV','INGR','INN','INSP','INSW','INTC','INTU','INVA','INVH','INVX','IOSP','IP','IPAR','IPGP','IQV','IR','IRDM','IRM','IRT','ISRG','IT','ITGR','ITRI','ITT','ITW','IVZ','J','JAZZ','JBGS','JBHT','JBL','JBLU','JBSS','JBTM','JCI','JEF','JHG','JJSF','JKHY','JLL','JNJ','JOE','JPM','JXN','KAI','KALU','KBH','KBR','KD','KDP','KEX','KEY','KEYS','KFY','KGS','KHC','KIM','KKR','KLAC','KLIC','KMB','KMI','KMPR','KMT','KMX','KN','KNF','KNSL','KNTK','KNX','KO','KOP','KR','KRC','KREF','KRG','KRYS','KSS','KTB','KTOS','KVUE','KW','KWR','L','LAD','LAMR','LBRT','LCII','LDOS','LEA','LECO','LEG','LEN','LFUS','LGIH','LGND','LH','LHX','LII','LIN','LITE','LIVN','LKFN','LKQ','LLY','LMAT','LMT','LNC','LNN','LNT','LNTH','LOPE','LOW','LPG','LPX','LQDT','LRCX','LRN','LSCC','LSTR','LTC','LULU','LUMN','LUV','LVS','LW','LXP','LYB','LYV','LZ','LZB','M','MA','MAA','MAC','MAN','MANH','MAR','MARA','MAS','MASI','MAT','MATW','MATX','MBC','MBIN','MC','MCD','MCHP','MCK','MCO','MCRI','MCW','MCY','MD','MDLZ','MDT','MDU','MEDP','MET','META','MGEE','MGM','MGY','MHK','MHO','MIDD','MIR','MKC','MKSI','MKTX','MLI','MLKN','MLM','MMI','MMM','MMS','MMSI','MNRO','MNST','MO','MOG.A','MOH','MORN','MOS','MP','MPC','MPT','MPWR','MRCY','MRK','MRNA','MRP','MRSH','MRTN','MS','MSA','MSCI','MSEX','MSFT','MSGS','MSI','MSM','MTB','MTCH','MTD','MTDR','MTG','MTH','MTN','MTRN','MTSI','MTUS','MTX','MTZ','MU','MUR','MUSA','MWA','MXL','MYGN','MYRG','MZTI','NABL','NATL','NAVI','NBHC','NBIX','NBTB','NCLH','NDAQ','NDSN','NE','NEE','NEM','NEO','NEOG','NEU','NFG','NFLX','NGVT','NHC','NI','NJR','NKE','NLY','NMIH','NNN','NOC','NOG','NOV','NOVT','NOW','NPK','NPO','NRG','NSA','NSC','NSIT','NSP','NTAP','NTCT','NTNX','NTRS','NUE','NVDA','NVR','NVRI','NVST','NVT','NWBI','NWE','NWL','NWN','NWS','NWSA','NX','NXPI','NXRT','NXST','NXT','NYT','O','OC','ODFL','OFG','OGE','OGN','OGS','OHI','OI','OII','OKE','OKTA','OLED','OLLI','OLN','OMC','OMCL','ON','ONB','ONTO','OPCH','OPLN','ORA','ORCL','ORI','ORLY','OSIS','OSK','OSW','OTIS','OTTR','OUT','OVV','OXM','OXY','OZK','PAG','PAHC','PANW','PARR','PATH','PATK','PAYC','PAYO','PAYX','PB','PBF','PBH','PBI','PCAR','PCG','PCRX','PCTY','PDFS','PEB','PECO','PEG','PEGA','PEN','PENG','PENN','PEP','PFBC','PFE','PFG','PFGC','PFS','PG','PGNY','PGR','PH','PHIN','PHM','PI','PII','PINS','PIPR','PJT','PK','PKG','PLAB','PLAY','PLD','PLMR','PLNT','PLTR','PLUS','PLXS','PM','PMT','PNC','PNFP','PNR','PNW','PODD','POOL','POR','POST','POWI','POWL','PPC','PPG','PPL','PR','PRA','PRAA','PRDO','PRG','PRGO','PRGS','PRI','PRIM','PRK','PRKS','PRLB','PRSU','PRU','PRVA','PSA','PSKY','PSMT','PSN','PSTG','PSX','PTC','PTCT','PTEN','PTGX','PVH','PWR','PYPL','PZZA','Q','QCOM','QDEL','QLYS','QNST','QRVO','QTWO','R','RAL','RAMP','RBA','RBC','RCL','RCUS','RDN','RDNT','REG','REGN','RES','REX','REXR','REYN','REZI','RF','RGA','RGEN','RGLD','RH','RHI','RHP','RJF','RL','RLI','RMBS','RMD','RNG','RNR','RNST','ROCK','ROG','ROIV','ROK','ROL','ROP','ROST','RPM','RRC','RRR','RRX','RS','RSG','RTX','RUN','RUSHA','RVTY','RWT','RXO','RYAN','RYN','SABR','SAFE','SAFT','SAH','SAIA','SAIC','SAM','SANM','SARO','SATS','SBAC','SBCF','SBH','SBRA','SBSI','SBUX','SCHL','SCHW','SCI','SCL','SCSC','SDGR','SEDG','SEE','SEIC','SEM','SEZL','SF','SFBS','SFM','SFNC','SGI','SHAK','SHC','SHEN','SHO','SHOO','SHW','SIG','SIGI','SITM','SJM','SKT','SKY','SKYW','SLAB','SLB','SLG','SLGN','SLM','SLVM','SM','SMCI','SMG','SMP','SMPL','SMTC','SNA','SNCY','SNDK','SNDR','SNEX','SNPS','SNX','SO','SOLS','SOLV','SON','SONO','SPG','SPGI','SPNT','SPSC','SPXC','SR','SRE','SRPT','SSB','SSD','SSTK','ST','STAA','STAG','STBA','STC','STE','STEL','STEP','STLD','STRA','STRL','STT','STWD','STX','STZ','SUPN','SW','SWK','SWKS','SWX','SXC','SXI','SXT','SYF','SYK','SYNA','SYY','T','TALO','TAP','TBBK','TCBI','TDC','TDG','TDS','TDW','TDY','TECH','TEL','TER','TEX','TFC','TFIN','TFX','TGNA','TGT','TGTX','THC','THG','THO','THRM','TILE','TJX','TKO','TKR','TLN','TMDX','TMHC','TMO','TMP','TMUS','TNC','TNDM','TNL','TOL','TPH','TPL','TPR','TR','TREX','TRGP','TRIP','TRMB','TRMK','TRN','TRNO','TROW','TRST','TRU','TRUP','TRV','TSCO','TSLA','TSN','TT','TTC','TTD','TTEK','TTMI','TTWO','TWI','TWLO','TWO','TXN','TXNM','TXRH','TXT','TYL','UA','UAA','UAL','UBER','UBSI','UCB','UCTT','UDR','UE','UFCS','UFPI','UFPT','UGI','UHS','UHT','ULS','ULTA','UMBF','UNF','UNFI','UNH','UNIT','UNM','UNP','UPBD','UPS','UPWK','URBN','URI','USB','USFD','USPH','UTHR','UTL','UVV','V','VAC','VAL','VC','VCEL','VCTR','VCYT','VECO','VFC','VIAV','VICI','VICR','VIR','VIRT','VITL','VLO','VLTO','VLY','VMC','VMI','VNO','VNOM','VNT','VOYA','VRE','VRRM','VRSK','VRSN','VRTS','VRTX','VSAT','VSCO','VSH','VSNT','VST','VSTS','VTOL','VTR','VTRS','VVV','VYX','VZ','WAB','WABC','WAFD','WAL','WAT','WAY','WBD','WBS','WCC','WD','WDAY','WDC','WDFC','WEC','WELL','WEN','WERN','WEX','WFC','WFRD','WGO','WH','WHD','WHR','WINA','WING','WKC','WLK','WLY','WM','WMB','WMG','WMS','WMT','WOR','WPC','WRB','WRLD','WS','WSC','WSFS','WSM','WSO','WSR','WST','WT','WTFC','WTRG','WTS','WTW','WU','WWD','WWW','WY','WYNN','XEL','XHR','XNCR','XOM','XPEL','XPO','XRAY','XYL','XYZ','YELP','YETI','YOU','YUM','ZBH','ZBRA','ZD','ZION','ZTS','ZWS']
    
    def get_sp500_symbols(self) -> List[str]:
        """Actual S&P 500 constituents (as of Feb 2026)"""
        return ['A','AAPL','ABBV','ABNB','ABT','ACGL','ACN','ADBE','ADI','ADM','ADP','ADSK','AEE','AEP','AES','AFL','AIG','AIZ','AJG','AKAM','ALB','ALGN','ALL','ALLE','AMAT','AMCR','AMD','AME','AMGN','AMP','AMT','AMZN','ANET','AON','AOS','APA','APD','APH','APO','APP','APTV','ARE','ARES','ATO','AVB','AVGO','AVY','AWK','AXON','AXP','AZO','BA','BAC','BALL','BAX','BBY','BDX','BEN','BF.B','BG','BIIB','BK','BKNG','BKR','BLDR','BLK','BMY','BR','BRK.B','BRO','BSX','BX','BXP','C','CAG','CAH','CARR','CAT','CB','CBOE','CBRE','CCI','CCL','CDNS','CDW','CEG','CF','CFG','CHD','CHRW','CHTR','CI','CIEN','CINF','CL','CLX','CMCSA','CME','CMG','CMI','CMS','CNC','CNP','COF','COIN','COO','COP','COR','COST','CPAY','CPB','CPRT','CPT','CRH','CRL','CRM','CRWD','CSCO','CSGP','CSX','CTAS','CTRA','CTSH','CTVA','CVNA','CVS','CVX','D','DAL','DASH','DD','DDOG','DE','DECK','DELL','DG','DGX','DHI','DHR','DIS','DLR','DLTR','DOC','DOV','DOW','DPZ','DRI','DTE','DUK','DVA','DVN','DXCM','EA','EBAY','ECL','ED','EFX','EG','EIX','EL','ELV','EME','EMR','EOG','EPAM','EQIX','EQR','EQT','ERIE','ES','ESS','ETN','ETR','EVRG','EW','EXC','EXE','EXPD','EXPE','EXR','F','FANG','FAST','FCX','FDS','FDX','FE','FFIV','FICO','FIS','FISV','FITB','FIX','FOX','FOXA','FRT','FSLR','FTNT','FTV','GD','GDDY','GE','GEHC','GEN','GEV','GILD','GIS','GL','GLW','GM','GNRC','GOOG','GOOGL','GPC','GPN','GRMN','GS','GWW','HAL','HAS','HBAN','HCA','HD','HIG','HII','HLT','HOLX','HON','HOOD','HPE','HPQ','HRL','HSIC','HST','HSY','HUBB','HUM','HWM','IBKR','IBM','ICE','IDXX','IEX','IFF','INCY','INTC','INTU','INVH','IP','IQV','IR','IRM','ISRG','IT','ITW','IVZ','J','JBHT','JBL','JCI','JKHY','JNJ','JPM','KDP','KEY','KEYS','KHC','KIM','KKR','KLAC','KMB','KMI','KO','KR','KVUE','L','LDOS','LEN','LH','LHX','LII','LIN','LLY','LMT','LNT','LOW','LRCX','LULU','LUV','LVS','LW','LYB','LYV','MA','MAA','MAR','MAS','MCD','MCHP','MCK','MCO','MDLZ','MDT','MET','META','MGM','MKC','MLM','MMM','MNST','MO','MOH','MOS','MPC','MPWR','MRK','MRNA','MRSH','MS','MSCI','MSFT','MSI','MTB','MTCH','MTD','MU','NCLH','NDAQ','NDSN','NEE','NEM','NFLX','NI','NKE','NOC','NOW','NRG','NSC','NTAP','NTRS','NUE','NVDA','NVR','NWS','NWSA','NXPI','O','ODFL','OKE','OMC','ON','ORCL','ORLY','OTIS','OXY','PANW','PAYC','PAYX','PCAR','PCG','PEG','PEP','PFE','PFG','PG','PGR','PH','PHM','PKG','PLD','PLTR','PM','PNC','PNR','PNW','PODD','POOL','PPG','PPL','PRU','PSA','PSKY','PSX','PTC','PWR','PYPL','Q','QCOM','RCL','REG','REGN','RF','RJF','RL','RMD','ROK','ROL','ROP','ROST','RSG','RTX','RVTY','SBAC','SBUX','SCHW','SHW','SJM','SLB','SMCI','SNA','SNDK','SNPS','SO','SOLV','SPG','SPGI','SRE','STE','STLD','STT','STX','STZ','SW','SWK','SWKS','SYF','SYK','SYY','T','TAP','TDG','TDY','TECH','TEL','TER','TFC','TGT','TJX','TKO','TMO','TMUS','TPL','TPR','TRGP','TRMB','TROW','TRV','TSCO','TSLA','TSN','TT','TTD','TTWO','TXN','TXT','TYL','UAL','UBER','UDR','UHS','ULTA','UNH','UNP','UPS','URI','USB','V','VICI','VLO','VLTO','VMC','VRSK','VRSN','VRTX','VST','VTR','VTRS','VZ','WAB','WAT','WBD','WDAY','WDC','WEC','WELL','WFC','WM','WMB','WMT','WRB','WSM','WST','WTW','WY','WYNN','XEL','XOM','XYL','XYZ','YUM','ZBH','ZBRA','ZTS']
    
    def get_major_etfs(self) -> List[str]:
        """Major ETF symbols"""
        return ['SPY','QQQ','DIA','IWM','VOO','VTI','IVV','VEA','IEFA','XLE','XLF','XLK','XLV','XLI','XLP','XLY','XLU','XLB','XLRE','XLC','VGT','VIG','VNQ','VWO','VT','EEM','EFA','AGG','BND','LQD','HYG','GLD','SLV','USO','UNG','DBC','CORN','WEAT','SOYB','GDX','IBIT','ETHA']
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            data = self.get_weekly_data('AAPL', weeks=5)
            return len(data) >= 5
        except:
            return False

if __name__ == '__main__':
    client = MassiveClient(config.MASSIVE_API_KEY)
    print("Testing Massive API connection...")
    if client.test_connection():
        print("✓ Connection successful!")
    else:
        print("✗ Connection failed")
