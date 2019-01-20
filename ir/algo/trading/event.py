

class StockWatchEvent:
    isin = None
    last = None
    closing = None
    first = None
    high = None
    low = None
    min = None
    max = None
    tardeValue = None
    tradeVolume = None
    tradesCount = None
    referencePrice = None
    state = None
    event = None
    upRangeCount = None
    downRangeCount = None
    lastTrade = None

class TradeEvent:
    quantity= None
    price= None
    instrumentId= None
    createdAt= None
    sellerId= None
    buyerId= None
    high= None
    low= None
    number= None

class BidAskEvent:
    isin= None
    items=[]

class BidAskEvent:
    bidNumber= None
    bidPrice= None
    bidQuanltity= None
    askNumber= None
    askPrice= None
    askQuantity= None

class ClientInfoEvent:
    individualBuyCount= None
    individualSellCount= None
    individualBuyVolume= None
    individualSellVolume= None
    naturalBuyVolume= None
    naturalSellVolume= None
    naturalBuyCount= None
    naturalSellCount= None
    isin= None
    dateTime= None
    buyerDensityValue= None
    sellerDensityValue= None


