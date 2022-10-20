import json
from web3 import Web3

import pandas as pd
from time import sleep, strftime, localtime

from inputs import settings
from decouple import config


POOL_FEE = 3000
SWAP_TOKEN_AMOUNT = 1
SWAP_TOKEN_DECIMALS = 6
# LET'S IMAGINE WE HAVE 10 USDC (BLOCKCHAIN FEES ARE NOT CONSIDERED)
SWAP_AMOUNT_IN_WEI = SWAP_TOKEN_AMOUNT * 1000 ** SWAP_TOKEN_DECIMALS

provider_url = f"https://mainnet.infura.io/v3/{config('INFURA_PROJECT_ID')}"
web3 = Web3(Web3.HTTPProvider(provider_url))


def get_max_for_input_token_uniswap_v2(input_amount,
                                       input_token_address,
                                       output_token_address,
                                       output_token_decimals):
    try:
        amount_in_wei = uniswapv2_router2_contract.functions.getAmountsOut(
            input_amount,
            [input_token_address,
             output_token_address]
        ).call()[1]
        return amount_in_wei / (10 ** output_token_decimals)
    except Exception as e:
        return str(e)


def get_max_for_input_token_uniswap_v3(input_amount,
                                       input_token_address,
                                       output_token_address,
                                       output_token_decimals):
    try:
        amount_in_wei = uniswapv3_quoter3_contract.functions.quoteExactInputSingle(
            input_token_address,
            output_token_address,
            POOL_FEE,
            input_amount,
            0
        ).call()
        return amount_in_wei / (10 ** output_token_decimals)
    except Exception as e:
        return str(e)


# TODO: add def retrieve decimals of the token


# Sources for prices (DEXes smart contracts)
# Uniswap V2
uniswapv2_router2_contract = web3.eth.contract(
    address=settings.uniswapv2_router2_address,
    abi=json.loads(settings.uniswapv2_router2_abi)
)

# Uniswap V3
uniswapv3_quoter3_contract = web3.eth.contract(
    address=settings.uniswapv3_quoter3_address,
    abi=json.loads(settings.uniswapv3_quoter3_abi)
)

# TODO: Sushiswap
# TODO: Balancer

# Import tokens names and addresses
header = ['token_name',
          'token_address',
          'token_decimals']

df_tokens = pd.read_csv('inputs//tokens_list.csv', names=header)
df_tokens['token_address'] = df_tokens['token_address'].apply(Web3.toChecksumAddress)


while 1:
    # BUYING
    df_tokens['amount_for_input_token_uni_v2'] = df_tokens.apply(
        lambda df: get_max_for_input_token_uniswap_v2(
            input_amount=SWAP_AMOUNT_IN_WEI,
            input_token_address=settings.usdc_address,
            output_token_address=df['token_address'],
            output_token_decimals=df['token_decimals']
        ),
        axis=1
    )

    df_tokens['amount_for_input_token_uni_v3'] = df_tokens.apply(
        lambda df: get_max_for_input_token_uniswap_v3(
            input_amount=SWAP_AMOUNT_IN_WEI,
            input_token_address=settings.usdc_address,
            output_token_address=df['token_address'],
            output_token_decimals=df['token_decimals']
        ),
        axis=1
    )

    df_tokens['max_amount_for_input_token'] = df_tokens[['amount_for_input_token_uni_v2',
                                                         'amount_for_input_token_uni_v3']].max(axis=1)
    df_tokens['max_amount_for_input_token_wei_int'] = (df_tokens['max_amount_for_input_token'] *
                                                       10 ** df_tokens['token_decimals']).astype(int)

    # SELLING
    df_tokens['amount_for_quote_token_uni_v2'] = df_tokens.apply(
        lambda df: get_max_for_input_token_uniswap_v2(
            input_amount=df['max_amount_for_input_token_wei_int'],
            input_token_address=df['token_address'],
            output_token_address=settings.usdc_address,
            output_token_decimals=SWAP_TOKEN_DECIMALS
        ),
        axis=1
    )

    df_tokens['amount_for_quote_token_uni_v3'] = df_tokens.apply(
        lambda df: get_max_for_input_token_uniswap_v3(
            input_amount=df['max_amount_for_input_token_wei_int'],
            input_token_address=df['token_address'],
            output_token_address=settings.usdc_address,
            output_token_decimals=SWAP_TOKEN_DECIMALS
        ),
        axis=1
    )

    df_tokens['max_amount_for_token'] = df_tokens[['amount_for_quote_token_uni_v2',
                                                   'amount_for_quote_token_uni_v3']].max(axis=1)

    df_tokens['arbitrage_result'] = round((df_tokens['max_amount_for_token'] - SWAP_TOKEN_AMOUNT) / \
                                          df_tokens['max_amount_for_input_token'], 4)

    print(strftime("%d/%m/%Y %H:%M:%S (LOCAL)", localtime()))
    print(df_tokens[['token_name', 'arbitrage_result']].to_string(index=False, header=['Token', 'Arb result']))

    df_tokens.to_csv('outputs//arbitrage_table.csv')

    sleep(60)
