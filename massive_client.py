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
        # Calculate date range (need extra weeks as buffer)
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks + 30)  # Increased buffer from 10 to 30
        
        url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/1/week/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        
        params = {
            'adjusted': 'true',  # Account for splits/dividends
            'sort': 'desc',  # Most recent first
            'limit': 50,  # Increased from weeks + 10
            'apiKey': self.api_key
        }
        
        try:
            print(f"    Fetching {symbol}: {url}")
            
            all_closes = []
            current_url = url
            params_copy = params.copy()
            
            # Fetch with pagination
            while current_url and len(all_closes) < weeks:
                response = requests.get(current_url, params=params_copy, timeout=10)
                print(f"    Response status: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                print(f"    Response keys: {data.keys()}")
                
                if 'results' not in data or not data['results']:
                    print(f"    Response data: {data}")
                    break
                
                # Extract closing prices from this page
                closes = [bar['c'] for bar in data['results']]
                all_closes.extend(closes)
                print(f"    Got {len(closes)} weeks (total: {len(all_closes)})")
                
                # Check for next page
                if 'next_url' in data and data['next_url'] and len(all_closes) < weeks:
                    current_url = data['next_url']
                    params_copy = {'apiKey': self.api_key}  # next_url already has other params
                    print(f"    Fetching next page...")
                else:
                    break
            
            if len(all_closes) < weeks:
                print(f"    ✗ {symbol}: only {len(all_closes)} weeks total")
                raise ValueError(f"Insufficient data: {len(all_closes)} weeks")
            
            print(f"    ✓ {symbol}: Got {len(all_closes)} weeks total")
            
            # Return most recent N weeks
            return all_closes[:weeks]
            
        except Exception as e:
            print(f"    ✗ {symbol}: ERROR - {str(e)}")
            raise
    
    def get_sp500_symbols(self) -> List[str]:
        """
        Complete S&P 500 stock list (all 500 companies)
        Organized by sector for maintainability
        """
        # INFORMATION TECHNOLOGY (67 stocks)
        tech = [
            'AAPL', 'MSFT', 'NVDA', 'AVGO', 'ORCL', 'CRM', 'ADBE', 'AMD', 'CSCO', 'ACN',
            'IBM', 'INTC', 'QCOM', 'TXN', 'INTU', 'NOW', 'AMAT', 'ADI', 'LRCX', 'SNPS',
            'CDNS', 'MRVL', 'KLAC', 'ANET', 'PANW', 'MU', 'NXPI', 'ADSK', 'CRWD', 'FTNT',
            'WDAY', 'ANSS', 'ROP', 'APH', 'MSI', 'DELL', 'HPQ', 'NTAP', 'STX', 'WDC',
            'SNDK', 'FFIV', 'JNPR', 'AKAM', 'KEYS', 'ZBRA', 'FICO', 'TYL', 'TRMB', 'CDW',
            'IT', 'GLW', 'HPE', 'MPWR', 'TDY', 'TER', 'SWKS', 'ENPH', 'QRVO', 'ON', 'GEN',
            'SMCI', 'CTSH', 'ACN', 'ORCL', 'CRM', 'ADBE', 'NOW'
        ]
        
        # FINANCIALS (71 stocks)
        financials = [
            'BRK.B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'MS', 'GS', 'BLK', 'AXP',
            'SPGI', 'SCHW', 'C', 'CB', 'PGR', 'MMC', 'ICE', 'USB', 'PNC', 'TFC',
            'CME', 'AON', 'AIG', 'AFL', 'MET', 'TRV', 'AJG', 'PRU', 'ALL', 'HIG',
            'BK', 'STT', 'TROW', 'MTB', 'FITB', 'KEY', 'CFG', 'RF', 'HBAN', 'CINF',
            'FIS', 'BRO', 'WRB', 'L', 'NTRS', 'FDS', 'IVZ', 'JKHY', 'CBOE', 'RJF',
            'DFS', 'SYF', 'COF', 'ALLY', 'KKR', 'APO', 'BX', 'ARES', 'CG', 'TPG',
            'WTW', 'MKTX', 'MSCI', 'MCO', 'EFX', 'TRU', 'GL', 'AIZ', 'RE', 'PFG', 'WBS'
        ]
        
        # HEALTH CARE (62 stocks)
        healthcare = [
            'LLY', 'UNH', 'JNJ', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'AMGN', 'ISRG',
            'VRTX', 'GILD', 'CI', 'ELV', 'BSX', 'REGN', 'ZTS', 'SYK', 'BDX', 'CVS',
            'HCA', 'MCK', 'COR', 'IDXX', 'HUM', 'EW', 'A', 'RMD', 'IQV', 'DXCM',
            'CNC', 'MTD', 'WAT', 'GEHC', 'ALGN', 'MRNA', 'BIIB', 'VTRS', 'HOLX', 'PODD',
            'STE', 'ZBH', 'LH', 'DGX', 'BAX', 'MOH', 'TECH', 'TFX', 'HSIC', 'INCY',
            'EXAS', 'COO', 'CTLT', 'RVTY', 'WST', 'SOLV', 'CRL', 'CAH', 'DVA', 'UHS', 'HWM', 'OGN'
        ]
        
        # CONSUMER DISCRETIONARY (51 stocks)
        consumer_disc = [
            'AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'LOW', 'BKNG', 'TJX', 'SBUX', 'CMG',
            'MAR', 'ORLY', 'GM', 'F', 'TGT', 'AZO', 'ROST', 'HLT', 'YUM', 'DHI',
            'LEN', 'APTV', 'GPC', 'EBAY', 'POOL', 'DG', 'DLTR', 'BBY', 'ULTA', 'LVS',
            'WYNN', 'MGM', 'GRMN', 'CZR', 'TPR', 'RL', 'HAS', 'MHK', 'WHR', 'LKQ',
            'NVR', 'PHM', 'BWA', 'EXPE', 'CCL', 'NCLH', 'RCL', 'KMX', 'DPZ', 'TSCO', 'AAP'
        ]
        
        # COMMUNICATION SERVICES (24 stocks)
        comm_services = [
            'GOOGL', 'META', 'NFLX', 'DIS', 'VZ', 'CMCSA', 'TMUS', 'T', 'CHTR', 'EA',
            'TTWO', 'LYV', 'PARA', 'FOXA', 'FOX', 'DISH', 'NWSA', 'NWS', 'OMC', 'IPG',
            'MTCH', 'PINS', 'SNAP', 'ROKU'
        ]
        
        # INDUSTRIALS (77 stocks)
        industrials = [
            'GE', 'UNP', 'HON', 'CAT', 'RTX', 'UPS', 'BA', 'LMT', 'DE', 'ADP',
            'ETN', 'TT', 'CARR', 'NOC', 'EMR', 'PH', 'WM', 'ITW', 'PCAR', 'GWW',
            'FI', 'TDG', 'CTAS', 'CMI', 'GD', 'RSG', 'NSC', 'EME', 'PAYX', 'FAST',
            'OTIS', 'VRSK', 'URI', 'PWR', 'AME', 'ODFL', 'DAL', 'UAL', 'LUV', 'CSX',
            'IR', 'SNA', 'CPRT', 'DOV', 'HUBB', 'J', 'LDOS', 'ROK', 'XYL', 'VLTO',
            'AXON', 'EFX', 'BR', 'EXPD', 'JBHT', 'CHRW', 'FDX', 'JCI', 'SWK', 'PKG',
            'BALL', 'AVY', 'SEE', 'NDSN', 'IEX', 'PNR', 'ROL', 'ALLE', 'MAS', 'AOS',
            'GGG', 'GNRC', 'ITT', 'RHI', 'TXT', 'HII', 'BLDR'
        ]
        
        # CONSUMER STAPLES (33 stocks)
        consumer_staples = [
            'WMT', 'PG', 'COST', 'KO', 'PEP', 'PM', 'MO', 'MDLZ', 'CL', 'KMB',
            'GIS', 'STZ', 'SYY', 'HSY', 'K', 'CHD', 'CLX', 'TSN', 'CAG', 'HRL',
            'MKC', 'CPB', 'LW', 'TAP', 'KVUE', 'EL', 'KDP', 'KR', 'SJM', 'ADM',
            'BG', 'MNST', 'DG'
        ]
        
        # ENERGY (23 stocks)
        energy = [
            'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'PXD', 'VLO', 'OXY',
            'WMB', 'KMI', 'HAL', 'HES', 'BKR', 'FANG', 'DVN', 'TRGP', 'OKE', 'MRO',
            'APA', 'CTRA', 'EQT'
        ]
        
        # UTILITIES (28 stocks)
        utilities = [
            'NEE', 'SO', 'DUK', 'CEG', 'SRE', 'AEP', 'D', 'PEG', 'VST', 'EXC',
            'XEL', 'ED', 'EIX', 'WEC', 'AWK', 'DTE', 'ES', 'FE', 'ETR', 'PPL',
            'AEE', 'CNP', 'CMS', 'NI', 'LNT', 'EVRG', 'AES', 'PNW'
        ]
        
        # REAL ESTATE (29 stocks)
        real_estate = [
            'PLD', 'AMT', 'EQIX', 'PSA', 'WELL', 'SPG', 'O', 'DLR', 'VICI', 'AVB',
            'EQR', 'SBAC', 'WY', 'INVH', 'ARE', 'MAA', 'KIM', 'DOC', 'REG', 'UDR',
            'HST', 'VTR', 'ESS', 'CPT', 'FRT', 'BXP', 'PEAK', 'CCI', 'EXR'
        ]
        
        # MATERIALS (28 stocks)
        materials = [
            'LIN', 'SHW', 'APD', 'FCX', 'ECL', 'NEM', 'CTVA', 'DD', 'NUE', 'DOW',
            'PPG', 'LYB', 'VMC', 'MLM', 'ALB', 'STLD', 'IFF', 'CE', 'EMN', 'FMC',
            'BALL', 'AVY', 'CF', 'MOS', 'IP', 'PKG', 'AMCR', 'SEE'
        ]
        
        # EMERGING TECH (not in S&P 500 - high growth sectors)
        emerging_tech = [
            # Bitcoin/Blockchain
            'MSTR', 'COIN', 'RIOT', 'MARA', 'CLSK', 'HUT', 'BITF',
            
            # AI/Data
            'PLTR', 'AI', 'BBAI', 'SOUN', 'SNOW', 'NET', 'DDOG', 'ZS', 'OKTA', 'MDB',
            
            # Quantum Computing
            'IONQ', 'RGTI', 'QUBT',
            
            # Space/Satellite
            'RKLB', 'SPCE', 'ASTS'
        ]
        
        # Combine all sectors
        all_stocks = (tech + financials + healthcare + consumer_disc + comm_services + 
                     industrials + consumer_staples + energy + utilities + real_estate + materials + emerging_tech)
        
        # Remove duplicates and return all
        return list(dict.fromkeys(all_stocks))
    
            'NVAX', 'NVCR', 'NVDA', 'NVEC', 'NVEE', 'NVEI', 'NVGS', 'NVMI', 'NVO', 'NVR',
            'NVRO', 'NVS', 'NVT', 'NVTA', 'NVTS', 'NWBI', 'NWE', 'NWFL', 'NWL', 'NWLI',
            'NWN', 'NWPX', 'NWS', 'NWSA', 'NX', 'NXE', 'NXGN', 'NXJ', 'NXN', 'NXP',
            'NXPI', 'NXRT', 'NXST', 'NXT', 'NXTC', 'NYCB', 'NYMT', 'NYT', 'O', 'OAS',
            'OBCI', 'OBE', 'OBLG', 'OBNK', 'OBOR', 'OBT', 'OC', 'OCC', 'OCCI', 'OCFC',
            'OCGN', 'OCN', 'OCSL', 'OCUL', 'OCX', 'ODC', 'ODFL', 'ODP', 'ODT', 'OEC',
            'OEG', 'OESX', 'OFC', 'OFG', 'OFIX', 'OFLX', 'OFS', 'OGE', 'OGEN', 'OGN',
            'OGS', 'OHI', 'OI', 'OIIM', 'OII', 'OIS', 'OKE', 'OKTA', 'OKYO', 'OLD',
            'OLED', 'OLLI', 'OLN', 'OLO', 'OLP', 'OM', 'OMAB', 'OMC', 'OMCL', 'OMER',
            'OMEX', 'OMF', 'OMI', 'ON', 'ONB', 'ONCS', 'ONCY', 'ONDS', 'ONEW', 'ONFO',
            'ONIC', 'ONL', 'ONLN', 'ONTO', 'ONTX', 'ONVO', 'OOMA', 'OPB', 'OPBK', 'OPEN',
            'OPFI', 'OPGN', 'OPHC', 'OPI', 'OPK', 'OPOF', 'OPRA', 'OPRT', 'OPRX', 'OPT',
            'OPTN', 'OPTT', 'OPY', 'OR', 'ORA', 'ORAN', 'ORC', 'ORCL', 'ORG', 'ORGO',
            'ORGS', 'ORI', 'ORIC', 'ORLY', 'ORMP', 'ORN', 'ORRF', 'ORTX', 'OSB', 'OSCR',
            'OSG', 'OSIS', 'OSK', 'OSPN', 'OSS', 'OST', 'OSTK', 'OSUR', 'OSW', 'OTEC',
            'OTEX', 'OTIC', 'OTIS', 'OTLK', 'OTLY', 'OTRK', 'OTTR', 'OUT', 'OVBC', 'OVID',
            'OVLY', 'OVV', 'OWL', 'OWLT', 'OXBR', 'OXFD', 'OXM', 'OXSQ', 'OXY', 'OZ',
            'OZK', 'OZON', 'PAA', 'PAAS', 'PAC', 'PACB', 'PACK', 'PACS', 'PACW', 'PAG',
            'PAGP', 'PAGS', 'PAHC', 'PAI', 'PAM', 'PANL', 'PANW', 'PAR', 'PARA', 'PARR',
            'PATH', 'PATK', 'PAVM', 'PAWZ', 'PAX', 'PAYA', 'PAYC', 'PAYO', 'PAYS', 'PAYX',
            'PB', 'PBA', 'PBAX', 'PBF', 'PBFS', 'PBH', 'PBHC', 'PBI', 'PBIP', 'PBPB',
            'PBR', 'PBT', 'PBTS', 'PBYI', 'PCAR', 'PCG', 'PCH', 'PCOR', 'PCRX', 'PCSA',
            'PCT', 'PCTI', 'PCTY', 'PCVX', 'PCY', 'PCYO', 'PD', 'PDCE', 'PDCO', 'PDD',
            'PDEX', 'PDFS', 'PDI', 'PDLB', 'PDM', 'PDOT', 'PDP', 'PDS', 'PE', 'PEBK',
            'PEBO', 'PECO', 'PED', 'PEG', 'PEGA', 'PEI', 'PEN', 'PENN', 'PEO', 'PEP',
            'PERI', 'PESI', 'PETQ', 'PETS', 'PETZ', 'PEV', 'PFBC', 'PFC', 'PFD', 'PFE',
            'PFGC', 'PFH', 'PFIE', 'PFIN', 'PFIS', 'PFL', 'PFLT', 'PFN', 'PFMT', 'PFPT',
            'PFS', 'PFSI', 'PFX', 'PG', 'PGC', 'PGEN', 'PGNY', 'PGP', 'PGR', 'PGRE',
            'PGRU', 'PGZ', 'PH', 'PHAT', 'PHD', 'PHG', 'PHI', 'PHIN', 'PHM', 'PHR',
            'PHUN', 'PHVS', 'PHX', 'PHYT', 'PI', 'PICC', 'PII', 'PINC', 'PING', 'PINS',
            'PIO', 'PIQX', 'PIRS', 'PIXY', 'PJT', 'PK', 'PKD', 'PKE', 'PKG', 'PKI',
            'PKW', 'PKX', 'PLAN', 'PLAY', 'PLBY', 'PLC', 'PLCE', 'PLD', 'PLG', 'PLIN',
            'PLL', 'PLM', 'PLMR', 'PLNT', 'PLOW', 'PLPC', 'PLRX', 'PLSE', 'PLTK', 'PLTR',
            'PLUG', 'PLUS', 'PLXS', 'PLYA', 'PLYM', 'PM', 'PMBC', 'PMD', 'PME', 'PMGM',
            'PMTS', 'PMT', 'PMVP', 'PNBK', 'PNC', 'PNF', 'PNFP', 'PNI', 'PNK', 'PNM',
            'PNNT', 'PNR', 'PNRG', 'PNTG', 'PNW', 'POAI', 'PODD', 'POET', 'POLA', 'POLY',
            'POOL', 'POR', 'POST', 'POWI', 'POWL', 'PPBI', 'PPC', 'PPD', 'PPG', 'PPIH',
            'PPL', 'PPSI', 'PPT', 'PRAA', 'PRAX', 'PRCH', 'PRDO', 'PRE', 'PRFT', 'PRFZ',
            'PRG', 'PRGO', 'PRGS', 'PRI', 'PRIM', 'PRK', 'PRLB', 'PRLD', 'PRM', 'PRMW',
            'PRO', 'PROG', 'PROV', 'PRPH', 'PRPL', 'PRPO', 'PRQR', 'PRSO', 'PRST', 'PRT',
            'PRTA', 'PRTC', 'PRTG', 'PRTH', 'PRTK', 'PRTS', 'PRVA', 'PRZ', 'PS', 'PSA',
            'PSB', 'PSC', 'PSEC', 'PSFE', 'PSHG', 'PSN', 'PSMT', 'PSN', 'PSNL', 'PSO',
            'PSQH', 'PSTG', 'PSTL', 'PSTV', 'PSTX', 'PSX', 'PT', 'PTC', 'PTCT', 'PTE',
            'PTEN', 'PTGX', 'PTI', 'PTLO', 'PTMN', 'PTN', 'PTON', 'PTR', 'PTSI', 'PTY',
            'PUK', 'PULM', 'PUMP', 'PUYI', 'PVAC', 'PVBC', 'PVG', 'PVH', 'PVL', 'PWFL',
            'PWOD', 'PWSC', 'PXD', 'PXLW', 'PXS', 'PYCR', 'PYN', 'PYPD', 'PYR', 'PYXS',
            'PZZA', 'QADA', 'QADB', 'QD', 'QDEL', 'QFIN', 'QLC', 'QLYS', 'QMCO', 'QNRX',
            'QNST', 'QQEW', 'QQQX', 'QQQ', 'QRTEA', 'QRTEB', 'QRVO', 'QSI', 'QSR', 'QTNT',
            'QTWO', 'QUAD', 'QUBT', 'QUIK', 'QUOT', 'QURE', 'QVCC', 'R', 'RA', 'RACE',
            'RADI', 'RAIL', 'RAIN', 'RAMP', 'RAND', 'RAPT', 'RARE', 'RARX', 'RAVE', 'RAVN',
            'RBA', 'RBB', 'RBBN', 'RBC', 'RBCAA', 'RBCN', 'RBLX', 'RBOT', 'RBS', 'RC',
            'RCAP', 'RCB', 'RCC', 'RCEL', 'RCII', 'RCKT', 'RCKY', 'RCL', 'RCM', 'RCMT',
            'RCON', 'RCP', 'RCRT', 'RCUS', 'RDCM', 'RDFN', 'RDHL', 'RDI', 'RDN', 'RDNT',
            'RDOG', 'RDS.A', 'RDS.B', 'RDUS', 'RDVT', 'RDWR', 'RDY', 'RE', 'REAL', 'REAX',
            'RECE', 'RECI', 'RECN', 'REDU', 'REED', 'REFR', 'REG', 'REGI', 'REGN', 'REI',
            'REKR', 'RELL', 'RELY', 'REM', 'RENT', 'REPH', 'RES', 'RESI', 'RESN', 'RETA',
            'RETO', 'REV', 'REVG', 'REX', 'REXR', 'REYN', 'REZI', 'RF', 'RFIL', 'RFL',
            'RFP', 'RGA', 'RGEN', 'RGLD', 'RGLS', 'RGNX', 'RGP', 'RGR', 'RGS', 'RH',
            'RHE', 'RHI', 'RHP', 'RICK', 'RIG', 'RIGL', 'RILY', 'RIOT', 'RIVE', 'RIVN',
            'RJF', 'RJGN', 'RKT', 'RKDA', 'RKLB', 'RL', 'RLAY', 'RLGT', 'RLI', 'RLJ',
            'RLMD', 'RLX', 'RLY', 'RM', 'RMAX', 'RMBI', 'RMBL', 'RMBS', 'RMCF', 'RMD',
            'RMNI', 'RMO', 'RMP', 'RMR', 'RMTI', 'RNDB', 'RNEM', 'RNET', 'RNG', 'RNGR',
            'RNLX', 'RNP', 'RNR', 'RNST', 'RNWK', 'ROAD', 'ROCK', 'ROG', 'ROIC', 'ROK',
            'ROKT', 'ROL', 'ROP', 'ROSA', 'ROST', 'ROVI', 'ROW', 'RPAR', 'RPD', 'RPM',
            'RPRX', 'RPT', 'RPTX', 'RQI', 'RRC', 'RRGB', 'RRR', 'RRTS', 'RS', 'RSF',
            'RSG', 'RSI', 'RSLS', 'RSPR', 'RSS', 'RSVR', 'RT', 'RTIX', 'RTL', 'RTRX',
            'RTLR', 'RTX', 'RUBY', 'RVBD', 'RVI', 'RVLV', 'RVMD', 'RVNC', 'RVP', 'RVPH',
            'RVSB', 'RVT', 'RVTY', 'RWAY', 'RWT', 'RXN', 'RXRX', 'RY', 'RYAAY', 'RYAN',
            'RYB', 'RYI', 'RYN', 'RYTM', 'RZA', 'RZB', 'S', 'SA', 'SABR', 'SABS',
            'SAFE', 'SAFM', 'SAFT', 'SAGE', 'SAH', 'SAIA', 'SAIC', 'SAIL', 'SAL', 'SALM',
            'SAM', 'SAN', 'SANM', 'SANW', 'SAP', 'SAR', 'SASR', 'SATS', 'SAVA', 'SAVE',
            'SB', 'SBAC', 'SBACK', 'SBBA', 'SBCF', 'SBBX', 'SBFG', 'SBGI', 'SBH', 'SBI',
            'SBNY', 'SBOW', 'SBRA', 'SBS', 'SBSI', 'SBT', 'SBUX', 'SCCO', 'SCD', 'SCE.G',
            'SCHL', 'SCHN', 'SCHW', 'SCI', 'SCL', 'SCM', 'SCOR', 'SCPH', 'SCS', 'SCSC',
            'SCVL', 'SCW', 'SCWX', 'SCYX', 'SD', 'SDC', 'SDGR', 'SDIG', 'SDPI', 'SDRL',
            'SE', 'SEAC', 'SEAL', 'SEAS', 'SEB', 'SECO', 'SEDG', 'SEE', 'SEED', 'SEER',
            'SEG', 'SEGI', 'SEIC', 'SELF', 'SEM', 'SEMR', 'SENEA', 'SENEB', 'SENS', 'SERA',
            'SES', 'SESN', 'SF', 'SFBC', 'SFBS', 'SFE', 'SFIX', 'SFL', 'SFM', 'SFNC',
            'SFST', 'SG', 'SGA', 'SGBX', 'SGC', 'SGEN', 'SGH', 'SGHT', 'SGMA', 'SGML',
            'SGMO', 'SGMS', 'SGRP', 'SGRY', 'SGU', 'SHAK', 'SHBI', 'SHC', 'SHCO', 'SHEN',
            'SHFS', 'SHG', 'SHIP', 'SHLS', 'SHLX', 'SHO', 'SHOO', 'SHOP', 'SHOT', 'SHPW',
            'SHSP', 'SHW', 'SHY', 'SIBN', 'SID', 'SIDU', 'SIEB', 'SIEN', 'SIF', 'SIFY',
            'SIG', 'SIGI', 'SIGN', 'SII', 'SIL', 'SILC', 'SILK', 'SILV', 'SIM', 'SIMO',
            'SINT', 'SIOX', 'SIRI', 'SITC', 'SITE', 'SITM', 'SIVB', 'SIX', 'SJI', 'SJM',
            'SJR', 'SJT', 'SJW', 'SKE', 'SKIL', 'SKLZ', 'SKM', 'SKT', 'SKX', 'SKY',
            'SKYW', 'SKYT', 'SKYV', 'SKYX', 'SLAB', 'SLB', 'SLCA', 'SLCR', 'SLDB', 'SLF',
            'SLG', 'SLGG', 'SLGL', 'SLGN', 'SLM', 'SLND', 'SLNH', 'SLNO', 'SLP', 'SLQT',
            'SLRC', 'SLRX', 'SLS', 'SLVM', 'SM', 'SMAR', 'SMBC', 'SMBK', 'SMCI', 'SMCP',
            'SMED', 'SMFG', 'SMFR', 'SMG', 'SMHI', 'SMID', 'SMLP', 'SMLR', 'SMM', 'SMMC',
            'SMMT', 'SMP', 'SMPL', 'SMRT', 'SMSI', 'SMTC', 'SMTI', 'SMTS', 'SNA', 'SNAP',
            'SNAX', 'SNBR', 'SNCR', 'SNCY', 'SND', 'SNDA', 'SNDE', 'SNDL', 'SNDR', 'SNDX',
            'SNE', 'SNEX', 'SNFCA', 'SNGX', 'SNH', 'SNHN', 'SNI', 'SNJV', 'SNL', 'SNMP',
            'SNN', 'SNO', 'SNOW', 'SNPS', 'SNPX', 'SNR', 'SNSS', 'SNT', 'SNTA', 'SNTG',
            'SNV', 'SNX', 'SNY', 'SO', 'SOBR', 'SOFI', 'SOFO', 'SOHO', 'SOHU', 'SOIL',
            'SOL', 'SOLY', 'SON', 'SONM', 'SONO', 'SONX', 'SOPA', 'SOPH', 'SOS', 'SOUN',
            'SOVO', 'SOWG', 'SOXL', 'SP', 'SPAQ', 'SPB', 'SPCB', 'SPCE', 'SPCM', 'SPE',
            'SPEC', 'SPFI', 'SPG', 'SPGI', 'SPH', 'SPHR', 'SPI', 'SPIR', 'SPK', 'SPLK',
            'SPNE', 'SPNS', 'SPNT', 'SPOK', 'SPOT', 'SPPI', 'SPR', 'SPRB', 'SPRC', 'SPRT',
            'SPRU', 'SPSC', 'SPTN', 'SPWH', 'SPWR', 'SPXC', 'SPXS', 'SQ', 'SQBG', 'SQFT',
            'SQL', 'SQLV', 'SQNS', 'SR', 'SRAD', 'SRAX', 'SRC', 'SRCE', 'SRCL', 'SRDX',
            'SRE', 'SREV', 'SRG', 'SRI', 'SRLP', 'SRNE', 'SRPT', 'SRRA', 'SRT', 'SRTS',
            'SRV', 'SRZN', 'SSB', 'SSD', 'SSIC', 'SSKN', 'SSL', 'SSNC', 'SSNT', 'SSP',
            'SSRM', 'SSSS', 'SSTI', 'SSTK', 'SSY', 'SSYS', 'ST', 'STAA', 'STAF', 'STAG',
            'STAR', 'STAY', 'STBA', 'STBX', 'STC', 'STE', 'STEC', 'STEM', 'STEP', 'STER',
            'STFC', 'STGW', 'STI', 'STIM', 'STKS', 'STKL', 'STL', 'STLA', 'STLD', 'STM',
            'STMP', 'STN', 'STNE', 'STNG', 'STNL', 'STOK', 'STON', 'STOR', 'STRA', 'STRC',
            'STRL', 'STRM', 'STRN', 'STRO', 'STRS', 'STRT', 'STSA', 'STSS', 'STT', 'STTK',
            'STVN', 'STWD', 'STX', 'STXB', 'STXS', 'STZ', 'SU', 'SUI', 'SUM', 'SUMR',
            'SUN', 'SUNS', 'SUNW', 'SUP', 'SUPN', 'SUPV', 'SURF', 'SURG', 'SURO', 'SUZ',
            'SVBI', 'SVC', 'SVFD', 'SVMK', 'SVRA', 'SVRE', 'SVT', 'SVVC', 'SVV', 'SWAG',
            'SWAV', 'SWBI', 'SWI', 'SWIR', 'SWK', 'SWKH', 'SWKS', 'SWM', 'SWN', 'SWTX',
            'SWX', 'SWZ', 'SXC', 'SXI', 'SXT', 'SXTC', 'SYBT', 'SYBX', 'SYF', 'SYK',
            'SYKE', 'SYMC', 'SYN', 'SYNC', 'SYNL', 'SYPR', 'SYRS', 'SYY', 'SZC', 'T',
            'TA', 'TAC', 'TACO', 'TACT', 'TAHO', 'TAIT', 'TAK', 'TAL', 'TALO', 'TANH',
            'TAOP', 'TAP', 'TARA', 'TARO', 'TASK', 'TAST', 'TATT', 'TAWNF', 'TAXI', 'TAYD',
            'TBB', 'TBBK', 'TBC', 'TBI', 'TBK', 'TBLA', 'TBLT', 'TBMC', 'TBNK', 'TBPH',
            'TC', 'TCBI', 'TCBK', 'TCBP', 'TCBS', 'TCBX', 'TCCO', 'TCDA', 'TCFC', 'TCF',
            'TCGP', 'TCG', 'TCN', 'TCNNF', 'TCO', 'TCOM', 'TCON', 'TCP', 'TCPC', 'TCRD',
            'TCRR', 'TCS', 'TCX', 'TD', 'TDA', 'TDC', 'TDCX', 'TDF', 'TDG', 'TDOC',
            'TDS', 'TDW', 'TDY', 'TEAM', 'TECH', 'TECK', 'TECL', 'TEDU', 'TEF', 'TEI',
            'TEL', 'TELL', 'TELZ', 'TEN', 'TENB', 'TENX', 'TEO', 'TER', 'TERN', 'TESS',
            'TETC', 'TEVA', 'TEX', 'TFC', 'TFIN', 'TFSL', 'TFX', 'TG', 'TGLS', 'TGNA',
            'TGP', 'TGS', 'TGT', 'TH', 'THCA', 'THFF', 'THG', 'THM', 'THO', 'THQ',
            'THR', 'THRD', 'THRM', 'THRY', 'THS', 'THTX', 'THVRF', 'TICC', 'TIGO', 'TIK',
            'TILE', 'TIPT', 'TISI', 'TIVO', 'TJX', 'TK', 'TKC', 'TKKS', 'TKR', 'TLF',
            'TLGT', 'TLMD', 'TLND', 'TLRY', 'TLS', 'TLSA', 'TLSI', 'TLYS', 'TM', 'TMBR',
            'TME', 'TMHC', 'TMKR', 'TMO', 'TMPR', 'TMST', 'TMUS', 'TNC', 'TNDM', 'TNET',
            'TNK', 'TNL', 'TNP', 'TNXP', 'TO', 'TOCA', 'TOI', 'TOL', 'TOOLY', 'TOPS',
            'TORM', 'TOT', 'TOUR', 'TOWN', 'TPB', 'TPC', 'TPCO', 'TPG', 'TPH', 'TPHS',
            'TPIC', 'TPL', 'TPRE', 'TPR', 'TPVG', 'TPX', 'TPYP', 'TR', 'TRC', 'TRCO',
            'TRDA', 'TREE', 'TREX', 'TRGP', 'TRHC', 'TRI', 'TRIL', 'TRIP', 'TRIT', 'TRMB',
            'TRMD', 'TRMK', 'TRMR', 'TRN', 'TRNO', 'TRNR', 'TRON', 'TROO', 'TROW', 'TROX',
            'TRP', 'TRQ', 'TRS', 'TRST', 'TRT', 'TRTN', 'TRTX', 'TRU', 'TRUE', 'TRUP',
            'TRV', 'TRVG', 'TRVI', 'TRVN', 'TRX', 'TS', 'TSBK', 'TSCO', 'TSE', 'TSHA',
            'TSIB', 'TSL', 'TSLA', 'TSM', 'TSN', 'TSND', 'TSO', 'TSRI', 'TSU', 'TT',
            'TTC', 'TTCF', 'TTD', 'TTEC', 'TTGT', 'TTI', 'TTMI', 'TTNP', 'TTOO', 'TTP',
            'TTSH', 'TTWO', 'TU', 'TUFN', 'TUP', 'TURN', 'TUSK', 'TVTX', 'TVTY', 'TW',
            'TWI', 'TWIN', 'TWLO', 'TWN', 'TWNK', 'TWO', 'TWOU', 'TWST', 'TX', 'TXG',
            'TXMD', 'TXN', 'TXRH', 'TXT', 'TY', 'TYG', 'TYL', 'TYPE', 'TZOO', 'U',
            'UA', 'UAA', 'UAL', 'UAMY', 'UAN', 'UAVS', 'UBA', 'UBCP', 'UBER', 'UBFO',
            'UBOH', 'UBP', 'UBSI', 'UBX', 'UCBI', 'UCBIO', 'UCFC', 'UCL', 'UCTT', 'UDMY',
            'UDR', 'UE', 'UEC', 'UEIC', 'UEPS', 'UFAB', 'UFC', 'UFCS', 'UFI', 'UFPI',
            'UFPT', 'UFS', 'UG', 'UGI', 'UGP', 'UHAL', 'UHG', 'UHS', 'UHT', 'UI',
            'UIL', 'UIS', 'UIVM', 'UJNA', 'UL', 'ULBI', 'ULH', 'ULHC', 'ULT', 'ULTA',
            'ULTC', 'ULTI', 'UMBF', 'UMC', 'UMH', 'UMPQ', 'UNAM', 'UNB', 'UNCY', 'UNF',
            'UNFI', 'UNG', 'UNH', 'UNIT', 'UNM', 'UNP', 'UNTY', 'UNVR', 'UONE', 'UONEK',
            'UPBD', 'UPC', 'UPGI', 'UPH', 'UPLD', 'UPST', 'UPWK', 'URBN', 'URG', 'URI',
            'UROV', 'USAC', 'USAK', 'USAP', 'USAS', 'USAU', 'USB', 'USCR', 'USEA', 'USEG',
            'USFD', 'USGO', 'USIG', 'USIO', 'USLM', 'USM', 'USNA', 'USPH', 'USWS', 'UTEK',
            'UTHR', 'UTHY', 'UTI', 'UTIS', 'UTL', 'UTMD', 'UTRS', 'UTSI', 'UTZ', 'UUU',
            'UVE', 'UVSP', 'UVV', 'UXIN', 'V', 'VAC', 'VAL', 'VALE', 'VALU', 'VANI',
            'VAPO', 'VAQC', 'VAR', 'VAXX', 'VBF', 'VBFC', 'VBIV', 'VBLT', 'VBNK', 'VBTX',
            'VC', 'VCA', 'VCBI', 'VCEL', 'VCIF', 'VCIT', 'VCKA', 'VCKB', 'VCLT', 'VCNX',
            'VCRA', 'VCSA', 'VCSH', 'VCTR', 'VCVC', 'VCYT', 'VECO', 'VEDU', 'VEEV', 'VEGA',
            'VEII', 'VENA', 'VEON', 'VER', 'VERB', 'VERI', 'VERO', 'VERU', 'VERV', 'VERX',
            'VERY', 'VET', 'VEV', 'VFC', 'VFF', 'VFL', 'VFLO', 'VFSV', 'VG', 'VGI',
            'VGIT', 'VGM', 'VGR', 'VHC', 'VHI', 'VIA', 'VIAB', 'VIAC', 'VIASP', 'VIAV',
            'VICP', 'VICI', 'VICR', 'VIGI', 'VIHD', 'VII', 'VIKG', 'VIOT', 'VIP', 'VIPS',
            'VIR', 'VIRC', 'VIRT', 'VISL', 'VIST', 'VIV', 'VIVO', 'VJET', 'VKI', 'VKQ',
            'VKTX', 'VKTXW', 'VLN', 'VLO', 'VLRS', 'VLT', 'VLTO', 'VLU', 'VLUE', 'VLUQF',
            'VLY', 'VLYPO', 'VLYPP', 'VMBS', 'VMC', 'VMD', 'VMEO', 'VMI', 'VMO', 'VMW',
            'VNCE', 'VNE', 'VNLA', 'VNO', 'VNOM', 'VNQI', 'VNTR', 'VO', 'VOC', 'VOD',
            'VOEXP', 'VOO', 'VOOG', 'VOOV', 'VOR', 'VOST', 'VOX', 'VOXX', 'VOYA', 'VPG',
            'VPOP', 'VPV', 'VQT', 'VRA', 'VRAY', 'VRCA', 'VRDN', 'VRE', 'VREX', 'VRIG',
            'VRIG', 'VRNA', 'VRNS', 'VRNT', 'VRO', 'VRP', 'VRPX', 'VRSK', 'VRSN', 'VRTS',
            'VRTV', 'VRTX', 'VRX', 'VRYYF', 'VS', 'VSAC', 'VSCO', 'VSDA', 'VSEC', 'VSH',
            'VSI', 'VSL', 'VSLR', 'VSM', 'VSME', 'VSMV', 'VSPR', 'VSS', 'VSTA', 'VSTM',
            'VSTX', 'VT', 'VTA', 'VTAQ', 'VTEB', 'VTEX', 'VTG', 'VTGN', 'VTHM', 'VTHR',
            'VTIP', 'VTIQ', 'VTIV', 'VTNR', 'VTOL', 'VTRE', 'VTRN', 'VTRS', 'VTRU', 'VTRY',
            'VTSI', 'VTSS', 'VTT', 'VTV', 'VTWO', 'VTX', 'VTYX', 'VUG', 'VUZI', 'VV',
            'VVC', 'VVNT', 'VVR', 'VVUS', 'VVV', 'VWE', 'VWID', 'VWOB', 'VXF', 'VXRT',
            'VXUS', 'VYGR', 'VYMI', 'VYM', 'VYNE', 'VYNT', 'VYX', 'VZIO', 'W', 'WAB',
            'WABC', 'WAFD', 'WAFU', 'WAL', 'WASH', 'WAT', 'WAVE', 'WDAY', 'WDC', 'WDFC',
            'WE', 'WEAT', 'WEAV', 'WEBK', 'WEC', 'WELL', 'WEN', 'WERN', 'WES', 'WETF',
            'WEX', 'WEYS', 'WF', 'WFCF', 'WFC', 'WFRD', 'WGO', 'WHD', 'WHF', 'WHG',
            'WHLM', 'WHLR', 'WHR', 'WIA', 'WILC', 'WIMI', 'WIN', 'WING', 'WINT', 'WIRE',
            'WIT', 'WIX', 'WK', 'WKC', 'WKHS', 'WKME', 'WL', 'WLBMD', 'WLD', 'WLDN',
            'WLFC', 'WLK', 'WLTW', 'WM', 'WMB', 'WMC', 'WMG', 'WMK', 'WMS', 'WMT',
            'WNC', 'WNEB', 'WNS', 'WOLF', 'WOOD', 'WOR', 'WOW', 'WPC', 'WPG', 'WPM',
            'WPRT', 'WPST', 'WR', 'WRB', 'WRBY', 'WRE', 'WRK', 'WRLD', 'WRLDF', 'WRLS',
            'WRN', 'WSBC', 'WSBF', 'WSC', 'WSFS', 'WSM', 'WSO', 'WSR', 'WST', 'WSTG',
            'WSTL', 'WSTQ', 'WTBA', 'WTI', 'WTM', 'WTRG', 'WTRU', 'WTS', 'WTTR', 'WTW',
            'WU', 'WUBA', 'WULF', 'WVE', 'WVFC', 'WW', 'WWD', 'WWE', 'WWOW', 'WWR',
            'WWW', 'WY', 'WYNN', 'WYY', 'X', 'XAN', 'XAUEURO', 'XAUEUR', 'XAUEUR', 'XAUUSD',
            'XBIO', 'XCO', 'XELA', 'XELAP', 'XENE', 'XEL', 'XERS', 'XFLT', 'XFOR', 'XGN',
            'XHR', 'XIN', 'XL', 'XLC', 'XLNX', 'XLRE', 'XLRN', 'XLU', 'XLV', 'XMTR',
            'XNCR', 'XNET', 'XOG', 'XOM', 'XOMA', 'XONE', 'XPEL', 'XPER', 'XPEV', 'XPL',
            'XPO', 'XPOF', 'XPON', 'XRAY', 'XRTX', 'XRX', 'XTL', 'XTLB', 'XTNT', 'XYL',
            'XYLD', 'XYLG', 'XYLO', 'XYNG', 'Y', 'YALA', 'YCBD', 'YCL', 'YCS', 'YELP',
            'YETI', 'YEXT', 'YGMZ', 'YGT', 'YI', 'YIN', 'YJ', 'YMAB', 'YORW', 'YOU',
            'YRCW', 'YRD', 'YRIV', 'YSG', 'YTEN', 'YTRA', 'YUM', 'YUMC', 'YUMAU', 'YVR',
            'YY', 'Z', 'ZAGG', 'ZAIS', 'ZAPTF', 'ZAZZT', 'ZBAO', 'ZBH', 'ZBRA', 'ZBTK',
            'ZCMD', 'ZD', 'ZDGE', 'ZEAL', 'ZEN', 'ZEPP', 'ZEST', 'ZEUS', 'ZG', 'ZGNX',
            'ZH', 'ZI', 'ZIM', 'ZIMV', 'ZINGA', 'ZION', 'ZIV', 'ZIXI', 'ZLAB', 'ZLCS',
            'ZM', 'ZMED', 'ZNGA', 'ZNWAA', 'ZOM', 'ZPTA', 'ZS', 'ZSAN', 'ZTO', 'ZTR',
            'ZTS', 'ZUMZ', 'ZUO', 'ZVLO', 'ZVRA', 'ZVSA', 'ZXYZ', 'ZYNE', 'ZYXI'
        ]
        
        # Combine all three indices
        all_sp1500 = sp500 + midcap_400 + smallcap_600
        
        # Remove duplicates and return
        return list(dict.fromkeys(all_sp1500))
    
    def get_major_etfs(self) -> List[str]:
        """
        Get major ETF symbols covering all asset classes
        """
        return [
            # Broad Market Equity
            'SPY', 'QQQ', 'DIA', 'IWM', 'VOO', 'VTI', 'IVV', 'VEA', 'IEFA',
            
            # Sector ETFs
            'XLE',   # Energy
            'XLF',   # Financials
            'XLK',   # Technology
            'XLV',   # Healthcare
            'XLI',   # Industrials
            'XLP',   # Consumer Staples
            'XLY',   # Consumer Discretionary
            'XLU',   # Utilities
            'XLB',   # Materials
            'XLRE',  # Real Estate
            'XLC',   # Communication Services
            
            # International
            'EFA', 'EEM', 'VWO', 'IEMG', 'FXI', 'EWJ', 'EWZ', 'EWU', 'EWG', 'INDA',
            
            # Fixed Income
            'TLT', 'AGG', 'LQD', 'HYG', 'TIP', 'BND', 'SHY', 'IEF',
            
            # Commodities
            'GLD',   # Gold
            'SLV',   # Silver
            'IBIT',  # Bitcoin Spot ETF
            'ETHA',  # Ethereum Spot ETF
            'USO',   # Oil
            'UNG',   # Natural Gas
            'DBC',   # Broad Commodities
            'CORN',  # Corn
            'WEAT',  # Wheat
            'SOYB',  # Soybeans
            
            # Thematic/Strategy
            'ARKK',  # Innovation
            'XBI',   # Biotech
            'SMH',   # Semiconductors
            'IBB',   # Biotech
            'VNQ',   # REITs
            'GDX',   # Gold Miners
        ]
    
    def test_connection(self) -> bool:
        """
        Test API connection with a simple request
        """
        try:
            data = self.get_weekly_data('AAPL', weeks=5)
            return len(data) >= 5
        except:
            return False
    
    def get_stocks_by_market_cap(self, min_market_cap_billions: float = 2.0, max_results: int = 2000) -> List[str]:
        """
        Get US stocks filtered by minimum market cap
        
        Args:
            min_market_cap_billions: Minimum market cap in billions USD (default: 2.0)
            max_results: Maximum number of stocks to return (default: 2000)
        
        Returns:
            List of stock symbols meeting the criteria
        
        Note: This makes multiple API calls and may take several minutes
        """
        url = f"{self.base_url}/v3/reference/tickers"
        
        params = {
            'market': 'stocks',
            'active': 'true',
            'type': 'CS',  # Common Stock only
            'limit': 1000,  # Max per page
            'apiKey': self.api_key
        }
        
        all_symbols = []
        page_count = 0
        
        try:
            print(f"🔍 Fetching US stocks with market cap >= ${min_market_cap_billions}B...")
            
            while url and len(all_symbols) < max_results:
                page_count += 1
                print(f"  Page {page_count}...")
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'results' not in data or not data['results']:
                    break
                
                # Filter by market cap
                for ticker in data['results']:
                    # Skip if no market cap data
                    if 'market_cap' not in ticker or not ticker['market_cap']:
                        continue
                    
                    market_cap_billions = ticker['market_cap'] / 1_000_000_000
                    
                    # Only include if above threshold
                    if market_cap_billions >= min_market_cap_billions:
                        symbol = ticker['ticker']
                        # Skip symbols with dots (foreign ADRs) or weird characters
                        if '.' not in symbol and symbol.isalpha():
                            all_symbols.append(symbol)
                
                print(f"    Total qualifying stocks: {len(all_symbols)}")
                
                # Check for next page
                url = data.get('next_url')
                if url:
                    params = {'apiKey': self.api_key}
                    time.sleep(0.2)  # Rate limit protection
                else:
                    break
            
            # Sort by symbol for consistency
            all_symbols = sorted(list(set(all_symbols)))[:max_results]
            
            print(f"✓ Found {len(all_symbols)} US stocks with market cap >= ${min_market_cap_billions}B")
            return all_symbols
            
        except Exception as e:
            print(f"✗ Error fetching stocks by market cap: {e}")
            raise

# Test the client
if __name__ == '__main__':
    client = MassiveClient(config.MASSIVE_API_KEY)
    print("Testing Massive API connection...")
    
    if client.test_connection():
        print("✓ Connection successful!")
        print(f"✓ API Key working")
    else:
        print("✗ Connection failed")
