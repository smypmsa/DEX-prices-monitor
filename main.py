import json
from web3 import Web3

import settings
from decouple import config

POOL_FEE = 3000
WETH_AMOUNT = 1
WETH_AMOUNT_IN_WEI = Web3.toWei(WETH_AMOUNT, 'ether')

provider_url = f"https://eth-mainnet.g.alchemy.com/v2/{config('INFURA_PROJECT_ID')}"
web3 = Web3(Web3.HTTPProvider(provider_url))

uniswapv2_router2_contract = web3.eth.contract(address=settings.uniswapv2_router2_address,
                                               abi=json.loads(settings.uniswapv2_router2_abi))

uniswapv3_quoter3_contract = web3.eth.contract(address=settings.uniswapv3_quoter3_address,
                                               abi=json.loads(settings.uniswapv3_quoter3_abi))

# Option 1: Buy on Uniswap V2, sell on Uniswap v3
dai_for_eth_amount = uniswapv2_router2_contract.functions.getAmountsOut(WETH_AMOUNT_IN_WEI,
                                                                        [settings.weth_address,
                                                                         settings.dai_address]).call()[1]

eth_for_dai_amount = uniswapv3_quoter3_contract.functions.quoteExactInputSingle(settings.dai_address,
                                                                                settings.weth_address,
                                                                                POOL_FEE,
                                                                                dai_for_eth_amount,
                                                                                0).call()

# Option 2: Buy on Uniswap V3, sell on Uniswap v2
dai_for_eth_amount3 = uniswapv3_quoter3_contract.functions.quoteExactInputSingle(settings.weth_address,
                                                                                 settings.dai_address,
                                                                                 POOL_FEE,
                                                                                 WETH_AMOUNT_IN_WEI,
                                                                                 0).call()

eth_for_dai_amount3 = uniswapv2_router2_contract.functions.getAmountsOut(dai_for_eth_amount3,
                                                                         [settings.dai_address,
                                                                          settings.weth_address]).call()[1]

arbitrage_result_in_weth_1 = Web3.fromWei(eth_for_dai_amount, 'ether') - WETH_AMOUNT
arbitrage_result_in_weth_2 = Web3.fromWei(eth_for_dai_amount3, 'ether') - WETH_AMOUNT

print(arbitrage_result_in_weth_1)
print(arbitrage_result_in_weth_2)
