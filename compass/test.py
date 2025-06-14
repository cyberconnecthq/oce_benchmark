from compass_api_sdk import models
from compass_api_sdk.sdk import CompassAPI


with CompassAPI(
    api_key_auth="<YOUR_API_KEY_HERE>",
) as compass_api_sdk:

    res = compass_api_sdk.token.price(chain=models.TokenPriceChain.ARBITRUM_MAINNET, token=models.TokenPriceToken.WBTC)

    # Handle response
    print(res)