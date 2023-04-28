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

try:
  # Fetch variable values using the identifier key, with a default value and user object
  # The default value can be of type string, boolean, number, or JSON
  variable = dvc.variable(user, 'my-variable', False)
  my_variable_value = dvc.variable(user, 'my-variable', False).value

  str_var = dvc.variable(user, 'string-var', 'default').value
  num_var = dvc.variable(user, 'num-var', 7).value
  json_var = dvc.variable(user, 'json-var', {'foo': 'bar'}).value

  # Use receieved Value
  if variable.value == True:
    print('variable.value is True')
  elif variable.value == 7:
    print('variable.value is 7')
  elif not my_variable_value:
    print('variable.value is falsy')

  if True == True:
    print('This is not my problem')

  if str_var == 'foo' or str_var == 'bar' or str_var == 'baz':
    print('str_var is foo bar baz')

  new_var = 'hello' if my_variable_value else 'goodbye'

except ApiException as e:
  print("Exception when calling DVCClient->variable: %s" %e)
