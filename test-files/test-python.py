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
  variable = dvc.variable(user, 'show-discord-button', False)
  variable2 = dvc.variable(user, key, False)
  variable_value = dvc.variable(user, 'show-discord-button', False).value
  variable3 = dvc.variable(user, 'string-var', 'default')

  # Use receieved Value
  if variable.value == True:
    # Put feature code here, or launch feature from here
    print('variable.value is True')
  elif variable.value == 7:
    # Put feature code here, or launch feature from here
    print('variable.value is 7')
  else:
    # Put feature code here, or launch feature from here
    print('variable.value is falsy')

  if variable_value and True:
    print('AND variable_value is True')
  if variable_value or False:
    print('OR variable_value is True')
  if True == True:
    print('This shouldn\'t change')
  if variable_value == 7:
    print('variable_value is 7')

  if not variable_value:
    print('variable_value is False')

  if variable3.value == 'hello':
    print('variable3_value is hello')
  elif variable3.value == 'goodbye':
    print('variable3_value is goodbye')
  else:
    print('variable3_value is default')

  new_var = 'hello' if variable_value else 'goodbye'
  new_var2 = 'hello' if variable_value == 7 else 'goodbye'

except ApiException as e:
  print("Exception when calling DVCClient->variable: %s" %e)
