#SYMBOLS=[
#    "BTC/USDT",
#    "BTC/USDT",
#    "ETH/USDT",
#    "SOL/USDT",
#    "BNB/USDT",
#    "XRP/USDT",
#    "ADA/USDT",
#    "DOGE/USDT"
#]

#REFERENCE_PRICES = {
#    "BTC/USDT": 53477,
#    "ETH/USDT": 2800,
#    "SOL/USDT": 145,
#    "BNB/USDT": 590,
#    "XRP/USDT": 0.55,
#    "ADA/USDT": 0.42,
#    "DOGE/USDT": 0.12,
#}


"""
Configuration des cryptomonnaies utilisées dans le projet.
"""

CRYPTO_CONFIG = {
    "BTC/USDT": {
        "reference_price": 110000,
        "hype": 100,
    },
    "ETH/USDT": {
        "reference_price": 3500,
        "hype": 85,
    }
    #"SOL/USDT": {
    #    "reference_price": 180,
    #    "hype": 70,
    #},
    #"BNB/USDT": {
    #    "reference_price": 590,
    #    "hype": 45,
    #},
    #"XRP/USDT": {
    #    "reference_price": 0.55,
    #    "hype": 55,
    #},
    #"ADA/USDT": {
    #    "reference_price": 0.42,
    #    "hype": 35,
    #},
    #"DOGE/USDT": {
    #    "reference_price": 0.12,
    #    "hype": 60,
    #},
}

SYMBOLS = list(CRYPTO_CONFIG.keys())

REFERENCE_PRICES = {
    symbol: config["reference_price"]
    for symbol, config in CRYPTO_CONFIG.items()
}

SYMBOL_HYPE = {
    symbol: config["hype"]
    for symbol, config in CRYPTO_CONFIG.items()
}