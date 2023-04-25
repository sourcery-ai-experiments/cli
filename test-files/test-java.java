import com.devcycle.sdk.server.cloud.api.DVCCloudClient;
import com.devcycle.sdk.server.cloud.model.DVCCloudOptions;
import com.devcycle.sdk.server.common.exception.DVCException;
import com.devcycle.sdk.server.common.model.User;
import com.devcycle.sdk.server.common.model.Variable;

public class MyClass {

    private DVCCloudClient dvcClient;

    private DVCCloudOptions dvcOptions = DVCCloudOptions.builder()
                .enableEdgeDB(false)
                .build();

    // Initialize DevCycle Client
    dvcClient = new DVCCloudClient("server-123", dvcOptions);

    public void useFeature() throws DVCException {

      // Create user object
      User user = User.builder()
          .userId("SOME_USER_ID")
          .build();
      
      // The default value can be of type string, boolean, number, or JSON
      String key = "show-discord-button";
      Boolean defaultValue = false;

      // Fetch variable values using the identifier key, with a default value and user object
      Variable<Boolean> variable = dvcClient.variable(user, key, defaultValue);

      // If the variable doesn't exist isDefaulted will be true
      System.out.print(variable.getIsDefaulted());

      // Use variable value
      if (variable.getValue()) {
         // Put feature code here, or launch feature from here
      } else {
         // Put feature code here, or launch feature from here
      }
    }
}