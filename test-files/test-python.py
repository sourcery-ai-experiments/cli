from __future__ import print_function
from devcycle_python_sdk import Configuration, DVCClient, UserData
from devcycle_python_sdk.rest import ApiException
configuration = Configuration()

# Set up authorization
configuration.api_key['Authorization'] = 'server-123'

# Create an instance of the API class
dvc = DVCClient(configuration)

# Create user object
user = UserData(
  user_id='test'
)

key = 'show-discord-button' # Variable key

try:
  # Fetch variable values using the identifier key, with a default value and user object
  # The default value can be of type string, boolean, number, or JSON
  variable = dvc.variable(user, key, False)

  # Use receieved Value
  if variable.value:
    # Put feature code here, or launch feature from here
  else:
    # Put feature code here, or launch feature from here

except ApiException as e:
  print("Exception when calling DVCClient->variable: %s" %e)