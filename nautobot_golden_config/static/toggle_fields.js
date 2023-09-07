
/**
 * Clear fields in forms based on conditions specified in the 'data' parameter.
 *
 * This function takes in an array of data objects, where each object contains a 'values'
 * property with an array of conditions. Each condition has a 'hide' property that contains
 * a list of field names. The function iterates through the 'data' array and hides the fields
 * specified in the 'hide' property for each condition. See `setupFieldListeners` doc
 * string for example data and more details.
 *
 * @param {Object[]} data - An array of data objects, each with a 'values' property.
 * @returns {void} - This function does not return anything.
 */
function clearFields(data) {
  // Iterate through the data array
  data.forEach(item => {
    // Get the field and value objects
    var values = item["values"];

    // Iterate through the values array
    values.forEach(condition => {
      // Hide the fields specified in "hide" array
      condition["hide"].forEach(fieldToHide => $("#" + fieldToHide).parent().parent().hide());
    });
  });
}

/**
 * Set up event listeners for fields based on conditions specified in the 'data' parameter.
 *
 * This function takes in an array of data objects, where each object contains an 'event_field'
 * property with the ID of a prior field. It also contains a 'values' property with an array of conditions.
 * Each condition has 'name', 'show', and 'hide' properties. The function iterates through the 'data' array
 * and sets up change event listeners for the prior fields. When the prior field's value changes, the function
 * checks the conditions and shows or hides fields based on the selected value. Please note that this is 
 * intended to be used in a django form rended_field, which adds `id_` to the field, such as `id_commands`.
 * Additionally, consider an empty "", `name` key to hide everything as shown. Example data being expected:
 * 
 * const hideFormData = [
 *   {
 *     "event_field": "id_plan_type",
 *     "values": [
 *       {
 *         "name": "manual",
 *         "show": ["id_commands"],
 *         "hide": ["id_feature"]
 *       },
 *       {
 *         "name": "missing",
 *         "show": ["id_feature"],
 *         "hide": ["id_commands"]
 *       },
 *       {
 *         "name": "", // Used for blank field
 *         "show": [],
 *         "hide": ["id_feature", "id_commands"]
 *       }
 *    }
 * ]
 *
 * @param {Object[]} data - An array of data objects, each with 'event_field' and 'values' properties.
 * @returns {void} - This function does not return anything.
 */
function setupFieldListeners(data) {
  // Iterate through the hideFormData array
  data.forEach(item => {
    // Get the prior field element by its ID
    var priorField = $("#" + item["event_field"]);

    // Handle the change event of the prior field
    priorField.on("change", function() {
      // Get the selected value of the prior field
      var selectedValue = priorField.val();

      // Iterate through the values array
      item["values"].forEach(condition => {
        if (condition["name"] === selectedValue) {
          // Show the fields specified in "show" array
          condition["show"].forEach(fieldToShow => $("#" + fieldToShow).parent().parent().show());
          // Hide the fields specified in "hide" array
          condition["hide"].forEach(fieldToHide => $("#" + fieldToHide).parent().parent().hide());
        }
      });
    });
  });
}