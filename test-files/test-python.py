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

MY_VARIABLE = 'show-discord-button' # Variable key

try:
  # Fetch variable values using the identifier key, with a default value and user object
  # The default value can be of type string, boolean, number, or JSON
  variable = dvc.variable(user, 'show-discord-button', False)
  variable2 = dvc.variable(user, MY_VARIABLE, False)
  variable_value = dvc.variable(user, 'show-discord-button', False).value
  stringVariable = dvc.variable(user, 'string-var', 'default')

  numVariable = dvc.variable(user, 'num-var', 7)
  jsonVariable = dvc.variable(user, 'json-var', {'key': 'value'})

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

  if variable_value and True and variable_value == True:
    print('AND variable_value is True')
  if variable_value or False:
    print('OR variable_value is True')
  if True == True:
    print('This shouldn\'t change')           # this shouldn't change
  if variable_value == 7:
    print('variable_value is 7')

  if not variable_value:
    print('variable_value is False')

  if stringVariable.value == 'hello':         # if stringVariable is hello inline comment
    print('stringVariable value is hello')    #hello
  elif stringVariable.value == 'goodbye':     # if stringVariable is goodbye inline comment
    print('stringVariable value is goodbye')  #goodbye
  else:
    print('stringVariable value is default')  #default

  if numVariable.value == 7:
    print('numVariable value is 7')
  else:
    print('numVariable value is not 7')

  if jsonVariable.value['key'] == 'value':
    print('jsonVariable value is default')
  else:
    print('jsonVariable value is not defaulted')


  if not variable_value:
    print('variable_value is Falsy')
  if not some_var:
    print('something is Falsy')

  print("variable: %s" % stringVariable.value)  # this prints the variable value of stringVariable

  new_var = 'hello' if variable_value else 'goodbye'
  new_var2 = 'hello' if variable_value == 7 else 'goodbye'
  new_var3 = 'hello' if variable_value < 7 else 'goodbye'
  new_var4 = 'hello' if variable_value < 'foo' else 'goodbye'
  new_var5 = 'hello' if variable_value > 7 else 'goodbye'
  new_var6 = 'hello' if variable_value <= 7 else 'goodbye'
  new_var7 = 'hello' if variable_value >= 7 else 'goodbye'

except ApiException as e:
  print("Exception when calling DVCClient->variable: %s" %e)
